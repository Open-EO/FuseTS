import re
from pathlib import Path

from setuptools import setup


def get_version(path: str = "src/fusets/__init__.py"):
    # Single-sourcing package version (https://packaging.python.org/en/latest/guides/single-sourcing-package-version/#single-sourcing-the-package-version)
    try:
        regex = re.compile(r"^__version__\s*=\s*(?P<q>['\"])(?P<v>.+?)(?P=q)\s$", flags=re.MULTILINE)
        with (Path(__file__).absolute().parent / path).open("r") as f:
            return regex.search(f.read()).group("v")
    except Exception:
        raise RuntimeError("Failed to find version string.")


if __name__ == "__main__":
    # See setup.cfg
    setup(
        version=get_version(),
    )
