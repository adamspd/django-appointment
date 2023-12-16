import requests
from appointment import __version__, __package_name__, __test_version__


def check_package_version(package_name, current_version):
    version_exists = False

    if __test_version__:
        print("Test version, skipping PyPI check.")
        version_exists = True
    else:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")

        if response.status_code == 200:
            released_versions = response.json()["releases"].keys()
            if current_version in released_versions:
                print(f"Version {current_version} already exists on PyPI!")
                version_exists = True

    # Output for GitHub Actions
    print(f"::set-output name=version_exists::{version_exists}")


check_package_version(__package_name__, __version__)
