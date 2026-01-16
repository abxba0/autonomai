from setuptools import setup, find_packages
from pathlib import Path


def read_requirements(filename):
    """Read requirements from a file and return as a list."""
    requirements_path = Path(__file__).parent / "requirements" / filename
    if not requirements_path.exists():
        return []

    with open(requirements_path, "r") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#") and not line.startswith("-r")
        ]


# Read base requirements
base_requirements = read_requirements("base.txt")
web_requirements = read_requirements("web.txt")
local_requirements = read_requirements("local.txt")
multimodal_requirements = read_requirements("multimodal.txt")

setup(
    name="self_optimizing_system",
    version="0.1.0",
    description="A self-optimizing instruction library that learns from failures",
    author="Your Name",
    packages=find_packages(),
    install_requires=base_requirements,
    extras_require={
        "web": web_requirements,
        "local": local_requirements,
        "multimodal": multimodal_requirements,
        "all": web_requirements + local_requirements + multimodal_requirements,
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
