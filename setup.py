"""Setup script for NuVo SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nuvo-sdk",
    version="0.1.0",
    author="Your Name",
    description="Python SDK for NuVo MusicPort multi-room audio systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nuvo-musicport",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.9",
    install_requires=[
        # SDK has no external dependencies - uses asyncio from stdlib
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.11.0",
            "mypy>=1.7.0",
            "ruff>=0.1.6",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "websockets>=12.0",
        ],
    },
)
