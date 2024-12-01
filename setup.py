from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gram_tools",
    version="1.0.3",
    author="Maehdakvan",
    author_email="visitanimation@google.com",
    description="Utilities for streamlined aiogram bot development.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DedInc/gram-tools",
    project_urls={
        "Bug Tracker": "https://github.com/DedInc/gram-tools/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    install_requires=['aiogram>=3.0.0', 'orjson', 'aiofiles', 'numpy', 'networkx', 'matplotlib'],
    python_requires='>=3.6'
)
