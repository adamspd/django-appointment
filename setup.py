import setuptools

from appointment import __author__, __author_email__, __author_website__, __description__, __package_name__, __url__, \
    __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=__package_name__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=__url__,
    description=__description__,
    project_urls={
        "Author Website": __author_website__,
    },
    packages=setuptools.find_packages(where="appointments"),
    package_dir={"": "appointment"},
    include_package_data=True,
    classifiers=[
        # Maturity of project
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Intended for
        'Intended Audience :: Developers',

        # License
        "License :: OSI Approved :: Apache Software License",

        # Python versions supported.
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",

        # OS
        "Operating System :: OS Independent",

        # Topic
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    license="Apache License 2.0",
    python_requires='>=3.8',
    install_requires=[
        "Django>=4.2",
        "Pillow>=10.1.0",
        "phonenumbers>=8.13.22",
        "django-phonenumber-field>=7.2.0",
        "babel>=2.13.0",
        "pytz>=2023.3",
    ]
)
