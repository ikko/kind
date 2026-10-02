# Package Publication Guide

This document provides detailed instructions on how to build and publish the `kind` package to PyPI (Python Package Index) using `uv` and `twine`.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **`uv`**: A fast Python package installer and resolver. If you don't have it, install it via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
*   **`twine`**: A utility for uploading Python packages to PyPI. Install it using `pip install twine`.
*   **PyPI Account**: You need an account on [PyPI](https://pypi.org/) or [TestPyPI](https://test.pypi.org/).
*   **API Token**: For secure publishing, it is highly recommended to use an API token instead of your username and password. You can create an API token from your PyPI or TestPyPI account settings.

## Publication Steps

Follow these steps to build and publish the `kind` package:

### 1. Clean Build Artifacts

Before building, it's good practice to clean up any old build artifacts. This ensures a fresh build.

```bash
rm -rf build/ dist/ kind.egg-info/
```


### 2. Build the Package

Use `uv` to build the source distribution (`.tar.gz`) and the wheel distribution (`.whl`).

```bash
uv build
```

This command will create a `dist/` directory containing the generated package files.

### 3. Publish the Package

Use the `publish.sh` script to upload your package: it runs `twine check dist/*` and then `twine upload dist/*`. Twine reads the target repository and credentials from its environment variables, which lets you switch between TestPyPI and the official PyPI.

#### Publishing to TestPyPI (Recommended for Testing)

It is highly recommended to test your publication process on [TestPyPI](https://test.pypi.org/) first. This allows you to verify that your package builds and uploads correctly without affecting the official PyPI.

```bash
TWINE_REPOSITORY=testpypi TWINE_USERNAME=__token__ TWINE_PASSWORD=<your_testpypi_api_token> ./publish.sh
```

Replace `<your_testpypi_api_token>` with your actual API token from TestPyPI.

#### Publishing to Official PyPI

Once you have successfully published to TestPyPI and are confident, you can publish to the official PyPI.

```bash
TWINE_USERNAME=__token__ TWINE_PASSWORD=<your_pypi_api_token> ./publish.sh
```

Replace `<your_pypi_api_token>` with your actual API token from PyPI.

**Important Security Note**: Avoid typing your API token directly on the command line in shared environments. Consider using environment variables or a `.pypirc` file for better security.

## Verifying Publication

After successful publication, you can verify your package on:

*   **TestPyPI**: `https://test.pypi.org/project/kind/<version>`
*   **PyPI**: `https://pypi.org/project/kind/<version>`

Replace `<version>` with the actual version number of your package (e.g., `0.1.0`).

## Troubleshooting

*   **`twine` not found**: Ensure `twine` is installed (`pip install twine`).
*   **Authentication errors**: Double-check your username and API token. Ensure the token has the correct permissions for the repository you are targeting.
*   **No distribution files found**: Make sure `uv build` completed successfully and created files in the `dist/` directory.
*   **Package already exists**: If you are trying to upload a version that already exists on PyPI, you will get an error. Increment the version number in `pyproject.toml`.
