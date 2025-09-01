#!/usr/bin/env python3
"""
Setup script for ACS ACR1252 NFC CLI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="acs-acr1252-nfc-cli",
    version="1.0.0",
    author="Daniel Rosehill",
    description="A modern CLI for ACS ACR1252 USB NFC Reader/Writer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/danielrosehill/ACS-ACR-1252-NFC-CLI-Linux",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Hardware",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            # TUI default entry point
            "nfc-tui=main:main",
            # Plain CLI
            "nfc-cli=nfc_cli:main",
            # Simple GUI
            "nfc-gui=nfc_gui:main",
        ],
    },
)
