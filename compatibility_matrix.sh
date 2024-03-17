#!/bin/bash
# How to use:
# sudo bash compatibility_matrix.sh 3
# The above command will run the compatibility tests with a maximum of 3 parallel jobs.

# Check for command-line argument; default to 1 if not provided
max_parallel_jobs=${1:-1}


# Ensure jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq could not be found. Please install jq to run this script."
    exit 1
fi

echo "Running compatibility tests with a maximum of $max_parallel_jobs parallel jobs..."

# Tests and store results in JSON
run_tests() {
  local dj_ver_key=$1
  local dj_ver="${dj_ver_key//d_/}"  # Convert key to version
  dj_ver="${dj_ver//_/.}"
  shift
  local python_versions=("$@")

  # Define a counter for running jobs
  local -i jobs=0

  for py_ver in "${python_versions[@]}"; do
    (
      echo "Testing with Python ${py_ver} and Django ${dj_ver}"
      local individual_result_file="${result_dir}/${dj_ver}_${py_ver}.json"
      if docker build -f Dockerfile.test --build-arg PYTHON_VERSION="${py_ver}" --build-arg DJANGO_VERSION="${dj_ver}" -t django_appointment_test:"${py_ver}_${dj_ver}" . && \
         docker run --rm django_appointment_test:"${py_ver}_${dj_ver}"; then
        echo "{\"result\": \"PASS\"}" > "$individual_result_file"
        echo "Test passed for Python ${py_ver} and Django ${dj_ver}"
      else
        echo "{\"result\": \"FAIL\"}" > "$individual_result_file"
        echo "Test failed for Python ${py_ver} and Django ${dj_ver}"
      fi
    ) &

    # Increment the job counter
    ((jobs++))

    # If we've reached the max parallel jobs, wait for one to finish
    if ((jobs >= max_parallel_jobs)); then
      wait -n  # Wait for any job to finish
      ((jobs--))  # Decrement the job counter
    fi
  done

  wait  # Wait for the remaining jobs to finish
}

# Generate Markdown table from JSON results
generate_markdown_table() {
  # Initialize Markdown file with the compatibility matrix header
  echo "# Compatibility Matrix" > compatibility_matrix.md
  # shellcheck disable=SC2129
  echo "" >> compatibility_matrix.md
  echo "| Django \\ Python | 3.6 | 3.7 | 3.8 | 3.9 | 3.10 | 3.11 | 3.12 |" >> compatibility_matrix.md
  echo "|------------------|-----|-----|-----|-----|------|------|------|" >> compatibility_matrix.md

  for dj_ver_key in "${DJANGO_VERSIONS[@]}"; do
    local dj_ver="${dj_ver_key//d_/}"  # Convert from d_x_y to x.y format
    dj_ver="${dj_ver//_/.}"
    echo -n "| $dj_ver " >> compatibility_matrix.md

    for py_ver in "${PYTHON_VERSIONS[@]}"; do
      local combined_key="${dj_ver}_${py_ver}"
      # shellcheck disable=SC2155
      local result=$(jq -r --arg key "$combined_key" '.[$key]' "$result_file")
      [[ "$result" == "null" ]] && result="-"
      echo -n "| $result " >> compatibility_matrix.md
    done
    echo "|" >> compatibility_matrix.md
  done

  # shellcheck disable=SC2129
  echo "" >> compatibility_matrix.md
  echo "## Test Results Explanation" >> compatibility_matrix.md
  echo "" >> compatibility_matrix.md
  echo "The compatibility matrix above demonstrates which combinations of Django and Python versions the package is compatible with based on the conducted tests. A 'PASS' indicates a successful compatibility test, whereas a 'FAIL' denotes an incompatibility or an issue encountered during testing. Versions marked with '-' were not tested due to known incompatibilities of django with python or other constraints." >> compatibility_matrix.md
  echo "" >> compatibility_matrix.md
  echo "See [django's official documentation about supported python versions](https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django) for more details." >> compatibility_matrix.md
  echo "" >> compatibility_matrix.md
  echo "It's important to ensure that your environment matches these compatible combinations to avoid potential issues. If a specific combination you're interested in is marked as 'FAIL', it's recommended to check the corresponding test logs for details and consider alternative versions or addressing the identified issues." >> compatibility_matrix.md
}

generate_badge_json() {
  local python_compatible=()
  local django_compatible=()

  for py_ver in "${PYTHON_VERSIONS[@]}"; do
    for dj_ver_key in "${DJANGO_VERSIONS[@]}"; do
      local dj_ver="${dj_ver_key//d_/}"
      dj_ver="${dj_ver//_/.}"
      local combined_key="${dj_ver}_${py_ver}"
      # shellcheck disable=SC2155
      local result=$(jq -r --arg key "$combined_key" '.[$key]' "$result_file")
      if [[ "$result" == "PASS" ]]; then
        # shellcheck disable=SC2076
        if ! [[ " ${python_compatible[*]} " =~ " ${py_ver} " ]]; then
          python_compatible+=("$py_ver")
        fi
        # shellcheck disable=SC2076
        if ! [[ " ${django_compatible[*]} " =~ " ${dj_ver} " ]]; then
          django_compatible+=("$dj_ver")
        fi
      fi
    done
  done

  # Remove duplicates and sort versions
  readarray -t unique_python_versions < <(printf '%s\n' "${python_compatible[@]}" | sort -uV)
  readarray -t unique_django_versions < <(printf '%s\n' "${django_compatible[@]}" | sort -uV)

  echo "Python compatible versions: ${unique_python_versions[*]}"
  echo "Django compatible versions: ${unique_django_versions[*]}"

  echo "{
    \"schemaVersion\": 1,
    \"label\": \"compatible with python\",
    \"message\": \"$(IFS=' | '; echo "${unique_python_versions[*]}")\",
    \"color\": \"blue\"
  }" > "python_compatible.json"

  echo "{
    \"schemaVersion\": 1,
    \"label\": \"compatible with django\",
    \"message\": \"$(IFS=' | '; echo "${unique_django_versions[*]}")\",
    \"color\": \"blue\"
  }" > "django_compatible.json"
}

post_cleanup() {
  echo "Cleaning up temporary files..."
  rm -rf "$result_dir"

  echo "Removing docker images..."
  # shellcheck disable=SC2155
#  local dangling_images=$(docker images -q --filter "dangling=true")
#  if [ -n "$dangling_images" ]; then
#    docker rmi "$dangling_images"
#  fi

  echo "Cleanup complete."
}

# Define directories and files
result_dir="test_results"
post_cleanup  # Clean up any previous test results
result_file="${result_dir}/results.json"

# Compatible Python versions for each Django version with prefixed keys
declare -A DJANGO_COMPATIBILITY=(
  ["d_3_2"]="3.6 3.7 3.8 3.9 3.10"
  ["d_4_0"]="3.8 3.9 3.10"
  ["d_4_1"]="3.8 3.9 3.10 3.11"
  ["d_4_2"]="3.8 3.9 3.10 3.11 3.12"
  ["d_5_0"]="3.10 3.11 3.12"
)

# Django and Python versions
DJANGO_VERSIONS=("d_3_2" "d_4_0" "d_4_1" "d_4_2" "d_5_0")
PYTHON_VERSIONS=("3.6" "3.7" "3.8" "3.9" "3.10" "3.11" "3.12")


# Setup
mkdir -p "$result_dir"
echo "{}" > "$result_file"

# Run tests for each Django/Python version combination
for dj_ver_key in "${DJANGO_VERSIONS[@]}"; do
  IFS=' ' read -r -a python_versions <<< "${DJANGO_COMPATIBILITY[$dj_ver_key]}"
  run_tests "$dj_ver_key" "${python_versions[@]}"
done

wait # Wait for all tests to complete

# Aggregate individual results into the final JSON file
echo "{}" > "$result_file" # Reinitialize to ensure it's empty
for file in "${result_dir}"/*.json; do
  dj_ver_py=$(basename "$file" .json)
  result=$(jq -r '.result' "$file")
  jq --arg dj_ver_py "$dj_ver_py" --arg result "$result" \
    '.[$dj_ver_py] = $result' "$result_file" > "${result_file}.tmp" && mv "${result_file}.tmp" "$result_file"
done

# Generate the Markdown table after all tests are run
generate_markdown_table

echo "Compatibility matrix has been generated: compatibility_matrix.md"
echo "Generating compatibility badges..."
generate_badge_json
echo "Compatibility badges have been generated: python_compatible.json, django_compatible.json"
echo "Cleaning up..."
post_cleanup
