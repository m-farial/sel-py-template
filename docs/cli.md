# CLI Usage

This document outlines the available command-line options for running tests in `sel-py-template`.

---

## Basic Execution

Run all tests:

```bash
poetry run pytest
```

---

## Interactive Mode

Run tests with interactive debugging enabled:

```bash
poetry run pytest --interactive
```

---

## Browser Selection

Run tests on a specific browser:

```bash
poetry run pytest --browser chrome
```

Supported browsers:

* chrome
* firefox
* edge

---

## Run All Browsers

Execute tests across all configured browsers:

```bash
poetry run pytest --all-browsers
```

---

## Parallel Execution

Run tests in parallel using pytest-xdist:

```bash
poetry run pytest -n auto
```

Combine with multi-browser:

```bash
poetry run pytest --all-browsers -n auto
```

---

## Accessibility Testing

Run accessibility checks using pytest-a11y:

```bash
poetry run pytest --a11y
```

---

## Verbose Output

```bash
poetry run pytest -v
```

---

## Run Specific Tests

```bash
poetry run pytest tests/test_login.py
```

---

## Run by Keyword

```bash
poetry run pytest -k "login"
```

---

## Fail Fast

Stop execution after first failure:

```bash
poetry run pytest -x
```

---

## Debugging

Drop into debugger on failure:

```bash
poetry run pytest --pdb
```

---

## Summary

Typical real-world command:

```bash
poetry run pytest --all-browsers -n auto --a11y -v
```

This runs:

* multi-browser tests
* in parallel
* with accessibility checks
* with verbose output
