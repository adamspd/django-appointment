import requests

package_name = "django-appointment"
current_version = "2.1.1"

response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
if response.status_code == 200:
    released_versions = response.json()["releases"].keys()
    if current_version in released_versions:
        print(f"Version {current_version} already exists on PyPI!")
        exit(1)
