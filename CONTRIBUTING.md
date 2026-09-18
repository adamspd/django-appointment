# Contributing to Django-Appointment

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html), So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints.
5. Issue that pull request!

## Any contributions you make will be under the Software License

In short, when you submit code changes, your submissions are understood to be under the
same [Apache 2.0 License](https://opensource.org/licenses/Apache-2.0) that covers the project. Feel free to contact us
if that's a concern.

## Report bugs using Github's [issues](https://github.com/adamspd/django-appointment/issues)

We use GitHub issues to track public bugs. Report a bug
by [opening a new issue](https://github.com/adamspd/django-appointment/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
    - Be specific!
    - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports.

## Use a Consistent Coding Style

* 4 spaces for indentation rather than tabs
* You can try running `python -m flake8` for style unification

## Contributing to the documentation

The documentation lives in this repository and is built with
[MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
Pages are in [`docs/`](https://github.com/adamspd/django-appointment/tree/main/docs), and the navigation is defined in `mkdocs.yml`.

To preview your changes locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000/>. The site rebuilds as you save.

Before opening a pull request, make sure the site still builds cleanly:

```bash
mkdocs build --strict
```

`--strict` turns broken internal links into errors, and it is what CI runs.

A few pages (the custom templates guide, the internationalization guide, the compatibility
matrix, this file, and others) are not written twice: they are pulled straight from the
Markdown files at the repository root using snippets, so edit the root file and the site
follows. Pushing to `main` publishes the site automatically.

## License

By contributing, you agree that your contributions will be licensed under
its [Apache 2.0 License](https://github.com/adamspd/django-appointment/LICENSE).
