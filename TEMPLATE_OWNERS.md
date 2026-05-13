# Template Ownership Guide

This project uses [`sel_py_template`](https://github.com/m-farial/sel_py_template) as its upstream template.

To pull in template updates without merge conflicts, it is critical to understand
which files are **template-owned** (never modify) and which are **user-owned** (yours to change).

---

## Ownership Map

```
repo root/
 ┣ src/
 ┃ ┣ sel_py_template/          🔒 TEMPLATE OWNED — never modify
 ┃ ┃ ┣ config/
 ┃ ┃ ┣ pages/
 ┃ ┃ ┃ ┗ base_page.py         ← inherit from this, do not edit it
 ┃ ┃ ┣ ui/
 ┃ ┃ ┗ utils/
 ┃ ┗ pages/                    ✅ USER OWNED — add your page objects here
 ┃   ┗ __init__.py
 ┣ examples/                   📖 TEMPLATE OWNED — reference only, do not edit
 ┃ ┗ example_page.py
 ┣ tests/                      ✅ USER OWNED — add your tests here
 ┣ conftest.py                 🔒 TEMPLATE OWNED — never modify
 ┣ pytest.ini                  ✅ USER OWNED — set report_title and extra_artifacts here
 ┣ pyproject.toml              🔒 TEMPLATE OWNED — never modify
 ┗ TEMPLATE_OWNERS.md         📖 This file
```

---

## 🔒 Template-Owned Files (never modify)

| Path | Reason |
|---|---|
| `src/sel_py_template/` | Core framework — updated by template releases |
| `conftest.py` | Browser fixtures, artifact management, CI config |
| `pyproject.toml` | Build and tooling config |
| `examples/` | Reference examples — updated alongside template |

Modifying any of these files will cause **merge conflicts** when you pull upstream updates.

---

## ✅ User-Owned Files (safe to modify)

| Path | What to put here |
|---|---|
| `src/pages/` | Your Page Object Model classes |
| `tests/` | Your test files and fixtures |
| `pytest.ini` | `report_title`, `extra_artifacts`, and other pytest settings |

---

## Adding a New Page

1. Create a file in `src/pages/`, e.g. `src/pages/login_page.py`
2. Inherit from `BasePage`:

```python
from sel_py_template.pages.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class LoginPage(BasePage):
    """Page object for the login screen."""

    USERNAME_INPUT: tuple[str, str] = (By.ID, "user-name")
    PASSWORD_INPUT: tuple[str, str] = (By.ID, "password")
    LOGIN_BUTTON: tuple[str, str] = (By.ID, "login-button")

    def __init__(self, driver: WebDriver, browser: str, timeout: int = 10) -> None:
        super().__init__(driver, browser=browser, timeout=timeout)

    def login(self, username: str, password: str) -> None:
        """Enter credentials and submit the login form."""
        self.find_element(self.USERNAME_INPUT).send_keys(username)
        self.find_element(self.PASSWORD_INPUT).send_keys(password)
        self.click(self.LOGIN_BUTTON)
```

3. See `examples/example_page.py` for a fully annotated reference.

---

## Pulling Template Updates

```bash
# One-time setup (if you haven't done this yet)
git remote add upstream https://github.com/m-farial/sel_py_template.git

# Pull latest template changes
git fetch upstream
git merge upstream/main
```

Because you have never modified the template-owned files, this merge will always be conflict-free.

If you ever see a merge conflict in a template-owned file, it means a modification
was made to it in your project. Resolve it by accepting the upstream version:

```bash
git checkout --theirs src/sel_py_template/
git add src/sel_py_template/
```