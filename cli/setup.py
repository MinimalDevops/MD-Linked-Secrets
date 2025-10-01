"""
Setup script for the lsec CLI tool.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lsec",
    version="1.0.0",
    author="MD-Linked-Secrets Team",
    description="A CLI tool for managing and linking environment variables across multiple projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.7.0",
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "lsec=secretool.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 