#!/usr/bin/env bash
# Build the Django/Python compatibility matrix by running the test suite in Docker
# for every supported combination.
#
# How to use:
#   bash compatibility_matrix.sh 10
# The above command runs at most 10 combinations at a time. Each combination also runs
# its own test suite in parallel; by default the available CPUs are split between the
# combinations running at once, so the machine stays busy either way. Set TEST_PARALLEL
# to pick that number yourself:
#   TEST_PARALLEL=10 bash compatibility_matrix.sh 1   # one combination, 10 test processes
#   bash compatibility_matrix.sh 10                   # 10 combinations, CPUs split between them
#
# Docker is the only requirement; sudo is not needed when your user can reach the
# Docker daemon. Written for bash 3.2 so it runs on a stock macOS shell.

set -uo pipefail

# Compatible Python versions for each Django version, as "django:python python ...".
# This is the single source of truth: the table columns, the badges and the jobs to
# run are all derived from it.
# See https://docs.djangoproject.com/en/stable/faq/install/#what-python-version-can-i-use-with-django
# Override this to try a subset, e.g. COMBINATIONS="6.1:3.13" bash compatibility_matrix.sh
COMBINATIONS=${COMBINATIONS:-"
  4.2:3.10 3.11 3.12
  5.0:3.10 3.11 3.12
  5.1:3.10 3.11 3.12 3.13
  5.2:3.10 3.11 3.12 3.13
  6.0:3.12 3.13 3.14
  6.1:3.12 3.13 3.14
"}

# Tolerate indentation, blank lines and spaces around the colon.
COMBINATIONS=$(
  echo "$COMBINATIONS" \
    | sed 's/^[[:space:]]*//; s/[[:space:]]*$//; s/[[:space:]]*:[[:space:]]*/:/' \
    | grep -v '^$'
)

if [ -z "$COMBINATIONS" ]; then
  echo "COMBINATIONS is empty: nothing to test." >&2
  echo "Each line must look like \"6.1:3.12 3.13\" (django:python python ...)." >&2
  exit 1
fi

max_parallel_jobs=${1:-1}

detect_cpus() {
  if command -v nproc > /dev/null 2>&1; then
    nproc
  elif command -v sysctl > /dev/null 2>&1; then
    sysctl -n hw.ncpu 2> /dev/null || echo 1
  else
    echo 1
  fi
}

cpu_count=$(detect_cpus)
[ -z "$cpu_count" ] && cpu_count=1

# Split the CPUs between the combinations running concurrently, unless told otherwise.
# The suite stops getting faster past about 4 processes (it is split by test class),
# so there is no point handing a single combination more than that; a floor of 2 keeps
# each combination reasonable when many are running at once.
if [ -z "${TEST_PARALLEL:-}" ]; then
  TEST_PARALLEL=$((cpu_count / max_parallel_jobs))
  [ "$TEST_PARALLEL" -gt 4 ] && TEST_PARALLEL=4
  [ "$TEST_PARALLEL" -lt 2 ] && TEST_PARALLEL=2
  [ "$cpu_count" -le 1 ] && TEST_PARALLEL=1
fi

result_dir="test_results"
log_dir="${result_dir}/logs"
image_prefix="django_appointment_test"

if ! command -v docker &> /dev/null; then
  echo "docker could not be found. Please install Docker to run this script." >&2
  exit 1
fi

if ! docker info &> /dev/null; then
  echo "The Docker daemon is not reachable. Start Docker and try again." >&2
  exit 1
fi

# --- helpers -----------------------------------------------------------------

django_versions() {
  echo "$COMBINATIONS" | while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "${line%%:*}"
  done
}

pythons_for() {
  # $1: django version
  echo "$COMBINATIONS" | while IFS= read -r line; do
    [ -z "$line" ] && continue
    if [ "${line%%:*}" = "$1" ]; then
      echo "${line#*:}"
      return
    fi
  done
}

python_versions() {
  # every python version mentioned, de-duplicated and version-sorted
  echo "$COMBINATIONS" | while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "${line#*:}" | tr ' ' '\n'
  done | grep -v '^$' | sort -u -t. -k1,1n -k2,2n
}

result_of() {
  # $1: django, $2: python -> PASS | FAIL | BUILD | (empty when not run)
  local f="${result_dir}/${1}_${2}.result"
  [ -f "$f" ] && cat "$f"
}

wait_for_slot() {
  # bash 3.2 has no `wait -n`, so poll the running job count instead
  while [ "$(jobs -r | wc -l | tr -d ' ')" -ge "$max_parallel_jobs" ]; do
    sleep 1
  done
}

cleanup_images() {
  echo "Removing test images..."
  docker images --format '{{.Repository}}:{{.Tag}}' \
    | grep "^${image_prefix}:" \
    | while IFS= read -r tag; do
        docker rmi -f "$tag" > /dev/null 2>&1
      done
}

on_interrupt() {
  echo ""
  echo "Interrupted. Partial results are in ${result_dir}/ and logs in ${log_dir}/."
  echo "compatibility_matrix.md and the badge files were left untouched."
  # shellcheck disable=SC2046
  kill $(jobs -p) 2> /dev/null
  exit 130
}
trap on_interrupt INT TERM

# --- running the tests -------------------------------------------------------

run_cell() {
  # $1: django version, $2: python version
  local dj_ver=$1
  local py_ver=$2
  local tag="${image_prefix}:${py_ver}_${dj_ver}"
  local log="${log_dir}/${dj_ver}_${py_ver}.log"
  local result_file="${result_dir}/${dj_ver}_${py_ver}.result"

  echo "Testing with Python ${py_ver} and Django ${dj_ver}"

  if ! docker build -f Dockerfile.test \
        --build-arg PYTHON_VERSION="${py_ver}" \
        --build-arg DJANGO_VERSION="${dj_ver}" \
        -t "${tag}" . > "$log" 2>&1; then
    echo "BUILD" > "$result_file"
    echo "  Python ${py_ver} / Django ${dj_ver}: image build failed (see ${log})"
    return
  fi

  # Confirm the image really holds the versions we asked for. A build arg that the
  # Dockerfile ignores would otherwise silently test the wrong combination.
  local actual
  actual=$(docker run --rm "${tag}" python -c \
    "import sys, django; print('%d.%d' % sys.version_info[:2], django.get_version())" 2>> "$log")
  local actual_py="${actual%% *}"
  local actual_dj="${actual#* }"

  {
    echo "=== requested: Python ${py_ver} / Django ${dj_ver}"
    echo "=== in image:  Python ${actual_py} / Django ${actual_dj}"
  } >> "$log"

  local dj_ok=0
  case "$actual_dj" in
    "$dj_ver"|"$dj_ver".*) dj_ok=1 ;;
  esac

  if [ "$actual_py" != "$py_ver" ] || [ "$dj_ok" -ne 1 ]; then
    echo "BUILD" > "$result_file"
    echo "  Python ${py_ver} / Django ${dj_ver}: image contains Python ${actual_py} / Django ${actual_dj} (see ${log})"
    return
  fi

  if docker run --rm -e TEST_PARALLEL="$TEST_PARALLEL" "${tag}" >> "$log" 2>&1; then
    echo "PASS" > "$result_file"
    echo "  Python ${py_ver} / Django ${dj_ver}: PASS"
  else
    echo "FAIL" > "$result_file"
    echo "  Python ${py_ver} / Django ${dj_ver}: FAIL (see ${log})"
  fi
}

# --- reporting ---------------------------------------------------------------

generate_markdown_table() {
  local py_versions="$1"
  local header="| Django \\ Python "
  local divider="|------------------"

  for py_ver in $py_versions; do
    header="${header}| ${py_ver} "
    divider="${divider}|------"
  done

  {
    echo "# Compatibility Matrix"
    echo ""
    echo "${header}|"
    echo "${divider}|"
  } > compatibility_matrix.md

  for dj_ver in $(django_versions); do
    local row="| ${dj_ver} "
    for py_ver in $py_versions; do
      local result
      result=$(result_of "$dj_ver" "$py_ver")
      [ -z "$result" ] && result="-"
      [ "$result" = "BUILD" ] && result="ERROR"
      row="${row}| ${result} "
    done
    echo "${row}|" >> compatibility_matrix.md
  done

  {
    echo ""
    echo "## Test Results Explanation"
    echo ""
    echo "The compatibility matrix above demonstrates which combinations of Django and Python versions the package is compatible with based on the conducted tests. A 'PASS' indicates a successful compatibility test, whereas a 'FAIL' denotes an incompatibility or an issue encountered during testing. An 'ERROR' means the test environment itself could not be built, so the combination was never actually exercised. Versions marked with '-' were not tested due to known incompatibilities of django with python or other constraints."
    echo ""
    echo "See [django's official documentation about supported python versions](https://docs.djangoproject.com/en/stable/faq/install/#what-python-version-can-i-use-with-django) for more details."
    echo ""
    echo "It's important to ensure that your environment matches these compatible combinations to avoid potential issues. If a specific combination you're interested in is marked as 'FAIL', it's recommended to check the corresponding test logs for details and consider alternative versions or addressing the identified issues."
  } >> compatibility_matrix.md
}

generate_badge_json() {
  local py_versions="$1"
  local python_compatible=""
  local django_compatible=""

  for dj_ver in $(django_versions); do
    for py_ver in $py_versions; do
      if [ "$(result_of "$dj_ver" "$py_ver")" = "PASS" ]; then
        case " ${python_compatible} " in *" ${py_ver} "*) ;; *) python_compatible="${python_compatible} ${py_ver}" ;; esac
        case " ${django_compatible} " in *" ${dj_ver} "*) ;; *) django_compatible="${django_compatible} ${dj_ver}" ;; esac
      fi
    done
  done

  python_compatible=$(echo "$python_compatible" | tr ' ' '\n' | grep -v '^$' | sort -u -t. -k1,1n -k2,2n | paste -sd'|' - | sed 's/|/ | /g')
  django_compatible=$(echo "$django_compatible" | tr ' ' '\n' | grep -v '^$' | sort -u -t. -k1,1n -k2,2n | paste -sd'|' - | sed 's/|/ | /g')

  echo "Python compatible versions: ${python_compatible}"
  echo "Django compatible versions: ${django_compatible}"

  cat > python_compatible.json <<EOF
{
    "schemaVersion": 1,
    "label": "compatible with python",
    "message": "${python_compatible}",
    "color": "blue"
  }
EOF

  cat > django_compatible.json <<EOF
{
    "schemaVersion": 1,
    "label": "compatible with django",
    "message": "${django_compatible}",
    "color": "blue"
  }
EOF
}

# --- main --------------------------------------------------------------------

echo "Detected ${cpu_count} CPUs."
echo "Running up to ${max_parallel_jobs} combination(s) at a time, each with --parallel=${TEST_PARALLEL}."
if [ $((max_parallel_jobs * TEST_PARALLEL)) -gt "$cpu_count" ]; then
  echo "That is $((max_parallel_jobs * TEST_PARALLEL)) test processes on ${cpu_count} CPUs."
  echo "For the best throughput try: bash $0 $((cpu_count / 4 > 0 ? cpu_count / 4 : 1))"
fi

rm -rf "$result_dir" 2> /dev/null
if [ -d "$result_dir" ]; then
  echo "Could not remove ${result_dir}/, which is left over from an earlier run." >&2
  echo "If that run used sudo the directory is owned by root; remove it with:" >&2
  echo "  sudo rm -rf ${result_dir}" >&2
  exit 1
fi
mkdir -p "$log_dir"

PY_VERSIONS=$(python_versions | tr '\n' ' ')
planned=0
completed=0

for dj_ver in $(django_versions); do
  for py_ver in $(pythons_for "$dj_ver"); do
    planned=$((planned + 1))
    wait_for_slot
    run_cell "$dj_ver" "$py_ver" &
  done
done

wait

if [ "$planned" -eq 0 ]; then
  echo "" >&2
  echo "No combinations were dispatched. Every entry in COMBINATIONS parsed to an empty" >&2
  echo "list of Python versions, so there was nothing to run." >&2
  exit 1
fi

# --- summary -----------------------------------------------------------------

passed=0
failed=0
errored=0
failing_cells=""

for dj_ver in $(django_versions); do
  for py_ver in $(pythons_for "$dj_ver"); do
    case "$(result_of "$dj_ver" "$py_ver")" in
      PASS)  passed=$((passed + 1));  completed=$((completed + 1)) ;;
      FAIL)  failed=$((failed + 1));  completed=$((completed + 1))
             failing_cells="${failing_cells}  FAIL  Django ${dj_ver} / Python ${py_ver} -> ${log_dir}/${dj_ver}_${py_ver}.log\n" ;;
      BUILD) errored=$((errored + 1)); completed=$((completed + 1))
             failing_cells="${failing_cells}  ERROR Django ${dj_ver} / Python ${py_ver} -> ${log_dir}/${dj_ver}_${py_ver}.log\n" ;;
    esac
  done
done

echo ""
echo "Ran ${completed}/${planned} combinations: ${passed} passed, ${failed} failed, ${errored} could not be built."
if [ -n "$failing_cells" ]; then
  echo ""
  printf "%b" "$failing_cells"
fi

if [ "$completed" -ne "$planned" ]; then
  echo ""
  echo "Only ${completed} of ${planned} combinations produced a result, so compatibility_matrix.md" >&2
  echo "and the badge files were left untouched to avoid publishing a partial matrix." >&2
  exit 1
fi

if [ "$passed" -eq 0 ]; then
  echo ""
  echo "No combination passed, which points at a problem with the test harness rather" >&2
  echo "than at a real incompatibility. compatibility_matrix.md and the badge files were" >&2
  echo "left untouched; check the logs in ${log_dir}/." >&2
  exit 1
fi

generate_markdown_table "$PY_VERSIONS"
echo ""
echo "Compatibility matrix has been generated: compatibility_matrix.md"
echo "Generating compatibility badges..."
generate_badge_json "$PY_VERSIONS"
echo "Compatibility badges have been generated: python_compatible.json, django_compatible.json"

cleanup_images
echo "Done. Logs for every combination are in ${log_dir}/."
