# sel-py-template
![Python](https://img.shields.io/badge/python-3.10+-blue)
[![A11y Powered](https://img.shields.io/badge/accessibility-integrated-brightgreen)](https://github.com/m-farial/pytest-a11y)
![Integration Tests](https://github.com/m-farial/sel-py-template/actions/workflows/tests.yaml/badge.svg)
![Unit Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://m-farial.github.io/pytest-a11y/)
![Architecture](https://img.shields.io/badge/architecture-layered-blueviolet)

Modern **Selenium + pytest automation framework** designed as a reusable template
for building production-grade UI test suites.

Built with:
Python 3.10+ • Selenium WebDriver • pytest • Page Object Model • CI/CD ready

---

## 🚀 What This Project Demonstrates

This project showcases how to design a **scalable UI automation framework**
used in real-world QA / SDET environments.

Key engineering concepts:

* pytest-based test architecture
* Page Object Model design using a rich `Element` descriptor system
* multi-browser execution
* parallel test execution (`pytest-xdist`)
* structured artifact management
* CI/CD-ready automation pipelines
* integration with accessibility testing via **pytest-a11y**

---

## ⚡ Quick Start

```bash
git clone https://github.com/m-farial/sel-py-template
cd sel-py-template
poetry install
poetry run pytest
```

Run interactively (visible browser window):

```bash
poetry run pytest --interactive
```

---

## 🧩 Project Structure

```text
sel-py-template/
│
├── src/
│   ├── pages/                  ✅ USER OWNED — add your Page Object Models here
│   │   └── __init__.py
│   └── sel_py_template/        🔒 TEMPLATE OWNED — core framework, do not modify
│       ├── pages/
│       │   └── base_page.py    ← inherit from this when building your pages
│       ├── ui/
│       │   └── elements.py     ← Element descriptor and BoundElement API
│       ├── utils/              ← logging, artifact management, reporting
│       └── config/             ← environment configuration
│
├── examples/                   📖 TEMPLATE OWNED — reference examples, do not modify
│   └── example_page.py         ← fully annotated page object to copy from
│
├── template_tests/             🔒 TEMPLATE OWNED — tests for the framework itself
│   ├── integration/
│   └── unit/
│
├── tests/                      ✅ USER OWNED — add your project tests here
│
├── conftest.py                 🔒 TEMPLATE OWNED — browser fixtures, CI config
├── pytest.ini                  ✅ USER OWNED — set report_title and other options
├── pyproject.toml              🔒 TEMPLATE OWNED — build and tooling config
└── TEMPLATE_OWNERS.md          📖 Full ownership reference and update guide
```

> See `TEMPLATE_OWNERS.md` for a complete breakdown of which files are safe to modify
> and which are owned by the template.

---

## 🧱 Adding Your Own Pages

Your page objects live in `src/pages/`. Each page inherits from `BasePage` and
declares its UI elements using the `Element` descriptor — a class-level declaration
that automatically wraps Selenium locators with a rich interaction API.

```python
# src/pages/login_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sel_py_template.pages.base_page import BasePage
from sel_py_template.ui.elements import Element, ElementType


class LoginPage(BasePage):

    username_input: Element = Element("user-name", ElementType.TEXT_INPUT, by=By.ID, name="Username")
    password_input: Element = Element("password", ElementType.TEXT_INPUT, by=By.ID, name="Password")
    login_button: Element = Element("login-button", ElementType.BUTTON, by=By.ID, name="Login Button")
    error_message: Element = Element(".error-message", ElementType.TOAST, by=By.CSS_SELECTOR, name="Error")

    def __init__(self, driver: WebDriver, browser: str, timeout: int = 10) -> None:
        super().__init__(driver, browser=browser, timeout=timeout)

    def login(self, username: str, password: str) -> None:
        self.username_input.type(username)
        self.password_input.type(password)
        self.login_button.click_retry()

    def should_show_error(self, expected_text: str) -> None:
        self.error_message.should_be_visible()
        self.error_message.should_contain_text(expected_text)
```

See `examples/example_page.py` for a fully annotated reference covering all
`Element` types, `BoundElement` methods, and the action/assertion pattern.

---

## 🧪 Example Test

```python
def test_login_valid_credentials(driver, browser_name):
    page = LoginPage(driver, browser=browser_name)
    page.login("standard_user", "secret_sauce")
    # assert your post-login state here

def test_login_invalid_credentials(driver, browser_name):
    page = LoginPage(driver, browser=browser_name)
    page.login("bad_user", "wrong_password")
    page.should_show_error("Epic sadface")
```

---

## 🌐 Multi-Browser Testing

```bash
# Run on a specific browser
poetry run pytest --browser chrome

# Run on all browsers sequentially
poetry run pytest --all-browsers

# Run all browsers in parallel
poetry run pytest --all-browsers -n 3
```

Supported browsers: `chrome`, `firefox`, `edge`.

---

## ⚙️ Configuration

Downstream projects configure the framework via `pytest.ini` at the project root.
This file is user-owned and will never be overwritten by template updates.

```ini
# pytest.ini
[pytest]
report_title = My Project Test Report
testpaths = tests

# Optional: register additional artifact directories
# extra_artifacts =
#     downloads=downloads
```

All browser options, artifact paths, and CI behaviour are controlled via
`conftest.py` (template-owned) and can be overridden via CLI flags:

| Flag | Default | Description |
|---|---|---|
| `--browser` | `chrome` | Browser to use (`chrome`, `firefox`, `edge`) |
| `--all-browsers` | off | Run on all three browsers |
| `--interactive` | off | Show the browser window (disables headless) |
| `--artifacts-dir` | `artifacts` | Base directory for all test output |
| `--report-title` | from `pytest.ini` | Override the HTML report title |
| `--extra-artifact NAME=PATH` | — | Register additional artifact directories |

---

## 📊 Test Artifacts

Every test run generates a self-contained output folder:

```text
artifacts/
└── YYYY-MM-DD/
    └── run_HHMMSS/
        ├── chrome_test_run_HH-MM-SS.log
        ├── pytest_html/
        │   ├── report.html
        │   ├── final_report.json
        │   ├── plus_metadata.json
        │   └── screenshots/          ← failure screenshots captured automatically
        └── a11y/                     ← created only when --a11y is passed
            ├── a11y_report.html
            ├── a11y_report.json
            └── violation_screenshots/
```

Benefits: easy debugging, CI artifact upload, historical test tracking.

---

## ♿ Accessibility Testing (pytest-a11y)

Integrated with [pytest-a11y](https://github.com/m-farial/pytest-a11y) for
axe-core accessibility scans alongside your UI tests:

```bash
pytest --a11y
```

Generates accessibility reports in `artifacts/.../a11y/`.

---

## ⚡ CI/CD Integration

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

## 🔄 Pulling Template Updates

This project is designed so that downstream projects can pull framework updates
from the template without merge conflicts.

**One-time setup:**
```bash
git remote add upstream https://github.com/m-farial/sel-py-template
```

**Getting updates:**
```bash
git fetch upstream
git merge upstream/main
```

This is conflict-free as long as you only add code to the user-owned locations
(`src/pages/`, `tests/`, `pytest.ini`) and never modify template-owned files.

See `TEMPLATE_OWNERS.md` for the full ownership map and conflict resolution guide.

---

## 🧠 System Architecture

```text
tests/
   ↓
Page Objects  (src/pages/ — user-owned)
   ↓
BasePage + Element descriptors  (sel_py_template — template-owned)
   ↓
Selenium WebDriver
   ↓
pytest execution engine
   ↓
Artifact Manager
   ↓
Reports + Logs + Screenshots
```

Optional:
```text
pytest-a11y plugin
   ↓
axe-core accessibility scans
   ↓
HTML + JSON accessibility reports
```

---

## 🛠 Development

```bash
poetry install
poetry run pytest
poetry run poe fmt-lint
poetry run poe coverage
```

---

## 🔗 Related Projects

**pytest-a11y** — accessibility testing plugin for pytest + Selenium.
Together these form a complete UI + accessibility testing ecosystem.

<https://github.com/m-farial/pytest-a11y>

---

## 📜 License

MIT