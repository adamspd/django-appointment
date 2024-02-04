import os
import sys

import requests

from appointment import __package_name__, __test_version__, __version__


def check_package_version(package_name, current_version, github_ref_=None):
    """Check if the given package version already exists on PyPI or TestPyPI.

    :param: package_name (str): The name of the package to check.
    :param: current_version (str): The current version of the package.
    :param: github_ref_ (str, optional): The GitHub reference (branch or tag name).
        If it contains 'test', checks against TestPyPI, otherwise PyPI.
        Defaults to None, in which case the check is against PyPI.

    Sets environment variables for GitHub Actions:
    - version_exists: True if the version already exists, False otherwise.
    - publish_to_pypi: True if eligible for publishing to PyPI, False otherwise.
    - publish_to_testpypi: True if eligible for publishing to TestPyPI, False otherwise.
    """
    version_exists = False
    publish_to_pypi = False
    publish_to_testpypi = False

    # Determine if this is a test version based on the GitHub ref or __test_version__
    is_test_version = "test" in github_ref_ if github_ref_ else __test_version__
    pypi_url = "https://test.pypi.org/pypi/" if is_test_version else "https://pypi.org/pypi/"

    # Check if the current version exists on the respective PyPI repository
    response = requests.get(f"{pypi_url}{package_name}/json")
    if response.status_code == 200:
        released_versions = response.json()["releases"].keys()
        if current_version in released_versions:
            print(f"Version {current_version} already exists on {'TestPyPI' if is_test_version else 'PyPI'}!")
            version_exists = True
        else:
            publish_to_pypi = not is_test_version
            publish_to_testpypi = is_test_version

    # Set environment variables for GitHub Actions
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"version_exists={version_exists}\n")
            f.write(f"publish_to_pypi={publish_to_pypi}\n")
            f.write(f"publish_to_testpypi={publish_to_testpypi}\n")
            f.write(f"version={current_version}\n")


if __name__ == "__main__":
    # Get the GitHub ref from the command line argument, if provided
    github_ref = sys.argv[1] if len(sys.argv) > 1 else None
    check_package_version(__package_name__, __version__, github_ref)
