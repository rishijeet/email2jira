from setuptools import setup, find_packages

setup(
    name="email2jira",
    version="0.1",
    packages=find_packages(),
    extras_require={
        "test": ["pytest>=7.0", "pytest-cov>=4.0"],
    },
) 