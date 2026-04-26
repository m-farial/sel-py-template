# sel-py-template
![Python](https://img.shields.io/badge/python-3.10+-blue)
[![A11y Powered](https://img.shields.io/badge/accessibility-integrated-brightgreen)](https://github.com/m-farial/pytest-a11y)
![Integration Tests](https://github.com/m-farial/sel-py-template/actions/workflows/tests.yaml/badge.svg)
![Unit Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://m-farial.github.io/pytest-a11y/)
![Architecture](https://img.shields.io/badge/architecture-layered-blueviolet)


Modern **Selenium + pytest automation framework** demonstrating
production-grade UI test architecture.

Built with:
Python 3.10+ • Selenium WebDriver • pytest • Page Object Model • CI/CD ready

---

## 🚀 What This Project Demonstrates

This project showcases how to design a **scalable UI automation framework**
used in real-world QA / SDET environments.

Key engineering concepts:

* pytest-based test architecture
* Page Object Model design
* multi-browser execution
* parallel test execution (`pytest-xdist`)
* structured artifact management
* CI/CD-ready automation pipelines
* integration with accessibility testing via **pytest-a11y**

---

## 🎥 Example Test Execution

Run tests:

```bash
poetry run pytest
```

Run interactively:

```bash
poetry run pytest --interactive
```

The framework automatically generates:

* structured run artifacts
* HTML reports
* screenshots on failure
* logs for debugging

---

## 🧠 System Architecture

```text
tests/
   ↓
Page Objects
   ↓
Selenium WebDriver
   ↓
pytest execution engine
   ↓
Artifact Manager
   ↓
Reports + Logs + Screenshots
```

Optional integration:

```text
pytest-a11y plugin
   ↓
axe-core accessibility scans
   ↓
HTML + JSON accessibility reports
```

---

## ⚡ Quick Start

```bash
git clone https://github.com/m-farial/sel-py-template
cd sel-py-template
poetry install
poetry run pytest
```

---

## 🧪 Example Test

```python
def test_login(driver, login_page):
    login_page.open()
    login_page.login("standard_user", "secret")
    assert login_page.is_logged_in()
```

---

## 🌐 Multi-Browser Testing

Run specific browser:

```bash
poetry run pytest --browser chrome
```

Run all browsers:

```bash
poetry run pytest --all-browsers
```

Parallel execution:

```bash
poetry run pytest --all-browsers -n 3
```

---

## 📊 Test Artifacts

After running tests, reports are automatically generated using a centralized artifact manager that creates one folder per day and one folder per test run.:

```text
artifacts/
└── YYYY-MM-DD/
    └── run_HHMMSS/
        ├── chrome_test_run_HH-MM-SS.log
        ├── pytest_html/
        │   ├── final_report.json
        │   ├── report.html
        │   ├── plus_metadata.json
        │   └── screenshots/
        └── a11y/
            ├── a11y_report.html
            ├── a11y_report.json
            └── violation_screenshots/
```
- The run log file is written directly at the run root.
- `pytest_html/` contains the regular HTML report artifacts.
- `screenshots/` lives under `pytest_html/`.
- `a11y/` is created only when accessibility reporting is enabled.
- `violation_screenshots/` lives under `a11y/`.

With the artifact manager, every run is self-contained and easier to archive, inspect, or upload from CI.

Benefits:

* easy debugging
* CI artifact upload
* historical test tracking

---

## ♿ Accessibility Testing (pytest-a11y)

This framework integrates directly with:

<https://github.com/m-farial/pytest-a11y>

Run accessibility checks:

```bash
pytest --a11y
```

This generates accessibility reports alongside UI test artifacts.

---

## ⚡ CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: UI Tests

on: [push, pull_request]

jobs:
  tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --all-browsers -n auto
```

---

## 🧩 Project Structure

```text
sel-py-template
│
├── src/
│   ├── pages/          # Page Object Models
│   ├── utils/          # Logging, reporting, utilities
│   └── config/         # Environment configuration
│
├── tests/              # Test suites
├── artifacts/          # Generated outputs
└── scripts/            # Developer utilities
```

---

## 🛠 Development

```bash
poetry install
poetry run pytest
poetry run poe fmt-lint
```

---

## 🧪 Advanced Usage (Moved for clarity)

This section previously contained detailed CLI, configuration, and execution variations.

👉 Recommended: move detailed usage into:

```text
docs/
  usage.md
  configuration.md
```

---

## Architecture

See full system design:

[Architecture](docs/architecture.md)

---

## 📚 Learning Goals

This repository demonstrates:

* scalable test architecture
* modern Python tooling
* maintainable test design
* CI-friendly automation

---

## 🔗 Related Projects

### pytest-a11y

Accessibility testing plugin for pytest + Selenium.

<https://github.com/m-farial/pytest-a11y>

Together, these repositories form a **complete UI + accessibility testing ecosystem**.

---

## 📜 License

MIT
