# Contributing to mobileadapt

We're excited that you're interested in contributing to mobileadapt! This document outlines the process for contributing to this project.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/mobileadapt.git
   ```
3. Create a new branch for your feature or bug fix:
   ```
   git checkout -b feature/your-feature-name
   ```

## Setting Up the Development Environment

1. Ensure you have Python 3.7+ installed.
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up Appium and the necessary mobile SDKs as described in the project's README.

## Making Changes

1. Make your changes in your feature branch.
2. Add or update tests as necessary.
3. Ensure your code follows the project's coding style (we use PEP 8 for Python).
4. Run the test suite to make sure all tests pass:
   ```
   python -m unittest discover tests
   ```

## Updating Documentation

1. Any changes that affect the project's functionality, API, or usage should be reflected in the documentation.
2. The documentation for this project is maintained in a separate repository: [adaptdocs](https://github.com/RevylAI/adaptdocs).
3. Clone the documentation repository:
   ```
   git clone https://github.com/RevylAI/adaptdocs.git
   ```
4. Make the necessary updates to the relevant documentation files.
5. Submit a separate pull request to the adaptdocs repository with your documentation changes.

## Submitting Changes

1. Commit your changes:
   ```
   git commit -am "Add a brief description of your changes"
   ```
2. Push to your fork:
   ```
   git push origin feature/your-feature-name
   ```
3. Submit a pull request through the GitHub website.
4. If you've made documentation changes, submit a separate pull request to the adaptdocs repository.

## Pull Request Guidelines

- Provide a clear title and description of your changes.
- Include any relevant issue numbers in the PR description.
- Ensure all tests pass and there are no linting errors.
- Add or update documentation as necessary.
- If your changes require documentation updates, mention the related PR in the adaptdocs repository.

## Reporting Bugs

- Use the GitHub issue tracker to report bugs.
- Describe the bug in detail, including steps to reproduce.
- Include information about your environment (OS, Python version, etc.).

## Requesting Features

- Use the GitHub issue tracker to suggest new features.
- Clearly describe the feature and its potential benefits.
- Be open to discussion about the feature's implementation.

## Code Review Process

The core team will review your pull request. We may suggest changes, improvements, or alternatives.

## Coding Conventions

- Follow PEP 8 style guide for Python code.
- Use meaningful variable and function names.
- Comment your code where necessary, especially for complex logic.
- Write docstrings for all functions, classes, and modules.

## License

By contributing to mobileadapt, you agree that your contributions will be licensed under the project's MIT license.

Thank you for contributing to mobileadapt!
