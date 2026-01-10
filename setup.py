from setuptools import setup, find_packages

setup(
    name="self_optimizing_system",
    version="0.1.0",
    description="A self-optimizing instruction library that learns from failures",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        # Add dependencies here when needed
        # "langchain>=0.1.0",
        # "langchain-anthropic>=0.0.1",
    ],
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
