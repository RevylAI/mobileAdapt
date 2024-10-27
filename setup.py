from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cognisim",
    version="0.1.0",
    author="Revyl AI",
    author_email="anam@revyl.ai",
    description="A package for cross platform LLM agentic testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/revyl-ai/mobileadapt",
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
)
