# Compatibility Matrix

| Django \ Python | 3.6 | 3.7 | 3.8 | 3.9 | 3.10 | 3.11 | 3.12 |
|------------------|-----|-----|-----|-----|------|------|------|
| 3.2 | PASS | PASS | PASS | PASS | PASS | - | - |
| 4.0 | - | - | PASS | PASS | PASS | - | - |
| 4.1 | - | - | PASS | PASS | PASS | PASS | - |
| 4.2 | - | - | PASS | PASS | PASS | PASS | PASS |
| 5.0 | - | - | - | - | PASS | PASS | PASS |

## Test Results Explanation

The compatibility matrix above demonstrates which combinations of Django and Python versions the package is compatible with based on the conducted tests. A 'PASS' indicates a successful compatibility test, whereas a 'FAIL' denotes an incompatibility or an issue encountered during testing. Versions marked with '-' were not tested due to known incompatibilities of django with python or other constraints.

See [django's official documentation about supported python versions](https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django) for more details.

It's important to ensure that your environment matches these compatible combinations to avoid potential issues. If a specific combination you're interested in is marked as 'FAIL', it's recommended to check the corresponding test logs for details and consider alternative versions or addressing the identified issues.
