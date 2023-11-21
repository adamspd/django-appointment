import requests
from appointment import __version__, __package_name__

package_name = __package_name__
current_version = __version__

response = requests.get(f"https://pypi.org/pypi/{package_name}/json")

version_exists = False

if response.status_code == 200:
    released_versions = response.json()["releases"].keys()
    if current_version in released_versions:
        print(f"Version {current_version} already exists on PyPI!")
        version_exists = True

# Output for GitHub Actions
print(f"::set-output name=version_exists::{version_exists}")
