#!/usr/bin/env python3

from pathlib import Path
from setuptools import setup, find_packages

directory = Path(__file__).resolve().parent
with open(directory / "README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sacagawea",
    version="0.0.1",
    description="language should be no barrier",
    author="Erfan Samandarian",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4",
        "certifi",
        "cffi",
        "chardet",
        "charset-normalizer",
        "deep-translator",
        "h11",
        "h2",
        "hpack",
        "hstspreload",
        "httpcore",
        "httpx",
        "hyperframe",
        "idna",
        "PyAudio",
        "pycparser",
        "pydub",
        "requests",
        "rfc3986",
        "sniffio",
        "soundfile",
        "soupsieve",
        "srt",
        "tqdm",
        "urllib3",
        "vosk",
        "websockets",
    ],
    py_modules=["sacagawea"],
    entry_points={
        "console_scripts": [
            "sacagawea=sacagawea.sacagawea:main",
        ],
    },
)
