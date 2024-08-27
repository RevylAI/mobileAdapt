from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mobileadapt",
    version="0.1.0",
    author="RevylAI",
    author_email="your.email@example.com",
    description="Mobile adapter for IOS and android for mobile LLM agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RevylAI/mobileadapt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "appium-python-client",
        "loguru",
        "lxml",
        "numpy",
        "attrs",
    ],
    extras_require={
        "dev": [
            "pytest",
            "flake8",
            "black",
            "isort",
        ],
    },
)