# sel-py-template

A modern Selenium Python automation framework demonstrating best practices for web testing. Features include Page Object Model architecture, multi-browser support (Chrome, Firefox, Edge), parallel test execution, automated HTML reporting with screenshots, and complete CI/CD integration.

**Built with:** Python 3.10+ · Selenium WebDriver · pytest · Poetry · Ruff · Black

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd sel-py-template

# Install Poetry (if not already installed)
# Windows PowerShell:
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS/Linux:
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run your first test
poetry run pytest --interactive
```

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [Useful Commands](#useful-commands)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required
- **Python 3.10+** - [Download here](https://www.python.org/downloads/)
  - Verify: `python --version`
- **Git** - [Download here](https://git-scm.com/downloads)
  - Verify: `git --version`

### Recommended
- **Poetry** - Python dependency management tool
  - Will be installed in the next section
- **VS Code** or **PyCharm** - For the best development experience

### Browser Drivers (Automatic)
Selenium Manager automatically downloads and manages browser drivers. No manual setup needed! ✨

---

## Installation

### Step 1: Install Poetry

Poetry manages dependencies and virtual environments for this project.

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Alternative (using pipx - recommended for isolation):**
```bash
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install poetry
```

Verify installation:
```bash
poetry --version
```

### Step 2: Clone and Set Up the Project

```bash
# Navigate to your workspace
cd /path/to/your/workspace

# Clone the repository
git clone <repository-url>
cd sel-py-template

# (Optional) Configure Poetry to create virtualenv inside project
# This makes it easier for IDEs to detect the environment
poetry config virtualenvs.in-project true --local

# Install all dependencies
poetry install
```

### Step 3: Install Pre-commit Hooks (Optional but Recommended)

Pre-commit hooks automatically format and lint your code before each commit.

```bash
poetry run pre-commit install
```

Now every time you commit, your code will be automatically formatted! 🎉

---

## Running Tests

### Basic Test Runs

**Run all tests (Chrome, headless - fastest):**
```bash
poetry run pytest
```

**Run with visible browser (great for debugging):**
```bash
poetry run pytest --interactive
```

**Run specific test file1(Chrome default):**
```bash
poetry run pytest tests/test_example.py
```

**Run specific test:**
```bash
poetry run pytest tests/test_example.py::test_success --interactive
```

---

### Browser Selection

**Chrome (default):**
```bash
poetry run pytest --browser chrome
```

**Firefox:**
```bash
poetry run pytest --browser firefox --interactive
```

**Edge:**
```bash
poetry run pytest --browser edge --interactive
```

---

### Multi-Browser Testing

**Run on all browsers sequentially:**
```bash
poetry run pytest --all-browsers
```

**Run on all browsers in parallel (3x faster!):**
```bash
poetry run pytest --all-browsers -n 3
```

**Watch all browsers run simultaneously:**
```bash
poetry run pytest --all-browsers -n 3 --interactive
```

---

### Common Testing Scenarios

**Development/Debugging:**
```bash
# See exactly what's happening in the browser
poetry run pytest --interactive --browser chrome -v

# Stop on first failure
poetry run pytest --interactive -x

# Run with print statements visible
poetry run pytest --interactive -s
```

**Quick Validation:**
```bash
# Fast check on all browsers
poetry run pytest --all-browsers -n auto
```

**CI/CD Pipeline:**
```bash
# Fastest, most reliable for automation
poetry run pytest --all-browsers -n auto
```

**Specific Test Debugging:**
```bash
# Debug a single failing test
poetry run pytest tests/test_checkout.py::test_complete_purchase --interactive -v -s
```

---

### Test Reports and Logs

After running tests, reports are automatically generated using a centralized artifact manager that creates one folder per day and one folder per test run.:

```
artifacts/
└── YYYY-MM-DD/
    └── run_HHMMSS/
        ├── chrome_test_run_HH-MM-SS.log
        ├── pytest_html/
        │   ├── report.html
        │   ├── plus_metadata.json
        │   └── failure_screenshots/
        └── a11y/
            ├── a11y_report.html
            └── violation_screenshots/
```
- The run log file is written directly at the run root.
- `pytest_html/` contains the regular HTML report artifacts.
- `failure_screenshots/` lives under `pytest_html/`.
- `a11y/` is created only when accessibility reporting is enabled.
- `violation_screenshots/` lives under `a11y/`.

With the artifact manager, every run is self-contained and easier to archive, inspect, or upload from CI.

#### User-defined extra artifacts

Users can register additional artifact folders without changing framework code.

##### pytest.ini

```ini
[pytest]
extra_artifacts =
    downloads=downloads
    videos=videos
    traces=debug/traces
```

##### Command line

```bash
poetry run pytest \
  --extra-artifact downloads=downloads \
  --extra-artifact videos=videos \
  --extra-artifact traces=debug/traces

**Open the HTML report:**
```bash
# Windows
start logs/2024-01-15_14-30-45/report.html

# macOS
open logs/2024-01-15_14-30-45/report.html

# Linux
xdg-open logs/2024-01-15_14-30-45/report.html
```

##### Python configuration

```python
from pathlib import Path

from sel_py_template.utils.artifact_manager import ArtifactConfig

artifact_config = ArtifactConfig(
    base_dir=Path("artifacts"),
    extra_artifacts={
        "downloads": "downloads",
        "videos": "videos",
        "traces": "debug/traces",
    },
)
```

#### Accessing extra artifacts in code

```python
def test_example(artifact_manager) -> None:
    downloads_dir = artifact_manager.get_extra_dir("downloads")
    trace_file = artifact_manager.get_extra_file("traces", "trace.zip")
```

Relative paths are created under the current run folder.

For example:

```text
artifacts/
└── 2026-03-05/
    └── run_111344/
        ├── chrome_test_run_11-13-44.log
        ├── pytest_html/
        ├── a11y/
        ├── downloads/
        ├── videos/
        └── debug/
            └── traces/
```

Absolute paths are also allowed if a team wants a specific artifact outside the run folder.

#### Recommended usage

Use `pytest.ini` for stable project-wide artifact folders and `--extra-artifact` for temporary CI or debug-only additions.

#### Integration notes

`pytest_configure(...)` is the right place to create the artifact manager once per session and store it on `config`, because that same hook already:
- creates output directories
- registers the report plugin
- configures pytest-html-plus related paths fileciteturn3file8L54-L83

`report_plugin.py` currently writes screenshots and failure logs using `self.base_log_dir`, and writes `plus_metadata.json` into the HTML output folder. Those are exactly the kinds of paths that benefit from central management. 

---

## Development Workflow

### Format and Lint Code

The project uses **Ruff**, **Black**, and **isort** for code quality.

**Format and lint in one command:**
```bash
poetry run poe fmt-lint
```

**Individual commands:**
```bash
# Format code
poetry run poe fmt

# Check formatting (without changing files)
poetry run poe lint

# Run tests
poetry run poe test

# Clean cache directories
poetry run poe clean
```

### Pre-commit Hooks

If you installed pre-commit hooks, formatting happens automatically:

```bash
git add .
git commit -m "Add new test"
# ✨ Code is automatically formatted before commit!
```

**Skip pre-commit hooks (use sparingly):**
```bash
git commit --no-verify -m "Skip formatting"
```

---

## Project Structure

```
sel-py-template/
│
├── .github/                          # GitHub specific files
│   └── workflows/
│
├── src/                              # Source code directory
│   ├── __init__.py
│   │
│   ├── pages/                        # Page Object Models
│   │   ├── __init__.py
│   │   ├── base_page.py              # Base page with common methods
│   │   └── example_page.py
│   │
│   ├── utils/                        # Utility modules
│   │   ├── __init__.py
│   │   ├── logger_util.py            # Logging configuration
│   │   ├── report_plugin.py          # Test reporting plugin
│   │   ├── config_reader.py          # Configuration file reader
│   │   ├── data_generator.py         # Test data generation
│   │   └── screenshot_util.py        # Screenshot utilities
│   │
│   └── config/                       # Configuration files
│       ├── __init__.py
│       ├── config.py                 # Main configuration
│       └── test_data.json            # Test data storage
│
├── tests/                            # Test cases
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures and hooks
│   │
│   ├── test_login.py                 # Login functionality tests
│   ├── test_inventory.py             # Product browsing tests
│   ├── test_cart.py                  # Shopping cart tests
│   ├── test_checkout.py              # Checkout flow tests
│   └── test_e2e.py                   # End-to-end scenarios
│
├── scripts/                          # Utility scripts
│   ├── __init__.py
│   ├── fmt_lint.py                   # Format and lint runner
│   ├── clean_cache.py                # Clean cache directories
│   ├── setup_env.py                  # Environment setup script
│   └── generate_report.py           # Custom report generator
│
├── logs/                             # Test execution logs (gitignored)
│   ├── .gitkeep                      # Keep directory in git
│   └── YYYY-MM-DD_HH-MM-SS/          # Timestamped log folders
│       ├── report.html               # HTML test report
│       ├── test_run.log              # Execution logs
│       └── screenshots/              # Screenshots on failure
│           ├── test_name_chrome.png
│           └── test_name_firefox.png
│
├── .venv/                            # Virtual environment (gitignored)
│
├── .pytest_cache/                    # Pytest cache (gitignored)
├── .ruff_cache/                      # Ruff cache (gitignored)
├── __pycache__/                      # Python cache (gitignored)
│
├── .gitignore                        # Git ignore rules
├── .pre-commit-config.yaml           # Pre-commit hooks configuration
├── pyproject.toml                    # Project dependencies and configuration
├── poetry.lock                       # Locked dependency versions
└── README.md                         # This file
```

### Key Files

- **`conftest.py`** - Browser fixtures, pytest configuration, CLI options
- **`pyproject.toml`** - All project configuration (dependencies, tools, settings)
- **`src/pages/`** - Page Object Model classes for web pages
- **`tests/`** - Test cases organized by feature

---

## Contributing

Thank you for contributing! Follow these steps to ensure a smooth process:

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/sel-py-template.git
cd sel-py-template
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Set Up Your Environment

```bash
# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### 4. Make Your Changes

- Write clean, readable code
- Follow existing patterns in the codebase
- Add tests for new features
- Update documentation if needed

### 5. Test Your Changes

```bash
# Format and lint
poetry run poe fmt-lint

# Run all tests
poetry run pytest

# Run tests on all browsers
poetry run pytest --all-browsers -n 3
```

### 6. Commit and Push

```bash
git add .
git commit -m "feat: add new login validation test"
git push origin feature/your-feature-name
```

### 7. Open a Pull Request

- Go to GitHub and open a Pull Request
- Describe what you changed and why
- Include steps to test your changes
- Link any related issues

### Code Style Guidelines

- **Formatting**: Handled automatically by Black and Ruff
- **Imports**: Organized by isort
- **Naming**: Use clear, descriptive names
  - Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Type hints**: Add type hints to all function signatures
- **Docstrings**: Add docstrings to public functions and classes

---

## Troubleshooting

### Import File Mismatch / Stale Cache

If pytest raises "import file mismatch" errors after renaming files:

**Windows (PowerShell):**
```powershell
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
Get-ChildItem -Path . -Recurse -Include *.pyc | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
if (Test-Path -Path ".pytest_cache") { Remove-Item -LiteralPath ".pytest_cache" -Recurse -Force }
```

**macOS/Linux:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache
```

**Or use the built-in command:**
```bash
poetry run poe clean
```

### Browser Driver Issues

Selenium Manager handles drivers automatically, but if you encounter issues:

1. **Update Selenium:**
   ```bash
   poetry update selenium
   ```

2. **Check browser version:**
   - Ensure Chrome/Firefox/Edge is up to date

3. **Clear Selenium cache:**
   ```bash
   rm -rf ~/.cache/selenium  # macOS/Linux
   del %USERPROFILE%\.cache\selenium  # Windows
   ```

### Poetry Issues

**Poetry not found after installation:**
```bash
# Close and reopen your terminal, or:
export PATH="$HOME/.local/bin:$PATH"  # macOS/Linux
$env:Path += ";$env:APPDATA\Python\Scripts"  # Windows PowerShell
```

**Lock file out of sync:**
```bash
poetry lock --no-update
poetry install
```

### Tests Failing Unexpectedly

1. **Run in interactive mode to see what's happening:**
   ```bash
   poetry run pytest --interactive -v -s
   ```

2. **Check logs and screenshots:**
   - Navigate to `logs/` directory
   - Open the HTML report
   - Review screenshots for failures

3. **Run a single test:**
   ```bash
   poetry run pytest tests/test_example.py::test_success --interactive -v
   ```

---

## Useful Commands

### Testing
```bash
# Run all tests
poetry run pytest

# Run with specific browser
poetry run pytest --browser firefox --interactive

# Run all browsers
poetry run pytest --all-browsers # sequentially
poetry run pytest --all-browsers -n 3 # in parallel

# Run specific test file
poetry run pytest tests/test_example.py

# Run with verbose output
poetry run pytest -v

# Stop on first failure
poetry run pytest -x

# Show print statements
poetry run pytest -s

# Generate HTML report
poetry run pytest --html=report.html --self-contained-html
```

### Code Quality
```bash
# Format and lint everything
poetry run poe fmt-lint

# Format only
poetry run poe fmt

# Lint only (no changes)
poetry run poe lint

# Run pre-commit on all files
poetry run pre-commit run --all-files
```

### Poetry
```bash
# Install dependencies
poetry install

# Add new dependency
poetry add package-name

# Add dev dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Activate virtual environment
poetry shell

# Run command in virtual environment
poetry run <command>
```

### Cleaning
```bash
# Clean all cache directories
poetry run poe clean

# Remove virtual environment
poetry env remove python

# Rebuild environment
poetry install
```

---

## Performance Tips

- **Headless mode** is 2-3x faster than interactive mode
- **Parallel execution** with `-n 3` can cut test time by 60-70%
- For **CI/CD**, always use: `poetry run pytest --all-browsers -n auto`
- For **debugging**, use: `poetry run pytest --interactive --browser chrome -v -s`
- Use `-x` flag to stop on first failure and save time
- Run specific tests during development instead of the full suite

---

## Additional Resources

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Page Object Model Pattern](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)

---

## License

MIT

---

**Happy Testing! 🧪✨**

If you encounter any issues or have questions, please open an issue on GitHub.