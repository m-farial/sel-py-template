# Configuration

This document describes how to configure the `sel-py-template` framework.

---

## Browser Configuration

Set the browser via CLI:

```bash
poetry run pytest --browser chrome
```

Or configure defaults in your test setup.

---

## Environment Configuration

Environment-specific settings can be managed via:

* environment variables
* configuration files in `src/sel_py_template/config/`

Example:

```bash
export ENV=staging
```

---

## pytest Configuration

You can configure pytest using `pytest.ini`:

```ini
[pytest]
addopts = -v
testpaths = tests
```

---

## Parallel Execution

Enable parallel execution with:

```bash
poetry run pytest -n auto
```

Requires:

```bash
pip install pytest-xdist
```

---

## Artifact Configuration

Test artifacts are automatically generated under:

```text
artifacts/YYYY-MM-DD/run_HHMMSS/
```

Includes:

* logs
* HTML reports
* screenshots
* accessibility reports

---

## Accessibility Integration

Enable accessibility testing:

```bash
poetry run pytest --a11y
```

Optional configurations:

```bash
poetry run pytest --a11y --a11y-dir ./reports
poetry run pytest --a11y --a11y-standard wcag2aa
```

---

## Logging Configuration

Logging is managed through utilities in:

```text
src/sel_py_template/utils/
```

Logs are automatically captured per test run.

---

## Custom Fixtures

Framework supports custom pytest fixtures via:

```text
tests/conftest.py
```

Example:

```python
@pytest.fixture
def custom_data():
    return {"user": "test"}
```

---

## Best Practices

* Keep environment config separate from test logic
* Avoid hardcoding credentials
* Use fixtures for reusable setup
* Keep configuration centralized

---

## Summary

Configuration is designed to be:

* flexible
* environment-driven
* CI-friendly
* scalable
