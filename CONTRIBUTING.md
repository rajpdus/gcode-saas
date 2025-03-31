# Contributing to gcode-agent

Thank you for your interest in contributing to the `gcode-agent` project!

## How to Contribute

*   **Reporting Bugs:** If you find a bug, please open an issue on the GitHub repository, providing as much detail as possible (steps to reproduce, error messages, expected behavior, your environment).
*   **Suggesting Enhancements:** Open an issue to suggest new features or improvements. Describe the enhancement and why it would be valuable.
*   **Pull Requests:**
    1.  Fork the repository.
    2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name` or `bugfix/issue-number`).
    3.  Make your changes. Ensure code is well-formatted and adheres to project style (consider adding linting tools like flake8 or black).
    4.  Add tests for your changes if applicable.
    5.  Ensure all tests pass (`pytest tests/`).
    6.  Commit your changes with clear commit messages.
    7.  Push your branch to your fork (`git push origin feature/your-feature-name`).
    8.  Open a Pull Request against the main repository's `main` branch.
    9.  Clearly describe the changes in your Pull Request.

## Development Setup

Follow the virtual environment and dependency installation steps in the main `README.md`.

Install development dependencies:
```bash
pip install pytest pytest-mock
```

Run tests:
```bash
pytest tests/
```

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. (Consider adding a `CODE_OF_CONDUCT.md` file if desired). 