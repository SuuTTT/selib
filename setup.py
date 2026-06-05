"""Shim so editable installs work on older setuptools (<64, no PEP 660).
Metadata lives in pyproject.toml."""
from setuptools import setup

setup()
