# Architecture

This document describes the system design and architecture of the
`sel-py-template` automation framework.

---

## Overview

`sel-py-template` is designed as a **modular, scalable UI automation framework**
built on top of:

* pytest (test orchestration)
* Selenium WebDriver (browser automation)
* Page Object Model (test abstraction)

The architecture emphasizes:

* separation of concerns
* reusability
* scalability for large test suites
* CI/CD compatibility

---

## High-Level Flow

```text
Test Cases
   ↓
Page Objects
   ↓
Selenium WebDriver
   ↓
pytest Execution Engine
   ↓
Artifact Manager
   ↓
Reports + Logs + Screenshots
```

Optional integration:

```text
pytest-a11y plugin
   ↓
axe-core accessibility engine
   ↓
Accessibility reports + screenshots
```

---

## Core Components

### Test Layer

Located in:

```text
tests/
```

Responsibilities:

* defines test scenarios
* validates application behavior
* uses fixtures for setup/teardown

Example:

```python
def test_login(driver, login_page):
    login_page.open()
    login_page.login("user", "password")
    assert login_page.is_logged_in()
```

---

### Page Object Layer

Located in:

```text
src/pages/
```

Responsibilities:

* encapsulates UI interactions
* isolates selectors and page logic
* provides reusable methods

Benefits:

* reduces duplication
* improves maintainability
* simplifies test readability

---

### WebDriver Layer

Handles browser interactions using Selenium.

Responsibilities:

* browser lifecycle management
* navigation and interaction
* execution across multiple browsers

Integrated through pytest fixtures.

---

### pytest Execution Engine

pytest is responsible for:

* test discovery
* fixture management
* execution orchestration
* parallel execution via `pytest-xdist`

Key features:

* simple test structure
* powerful fixture system
* plugin ecosystem support

---

### Artifact Management

Artifacts are generated for every test run:

```text
artifacts/YYYY-MM-DD/run_HHMMSS/
```

Includes:

* logs
* HTML reports
* screenshots
* accessibility reports

Purpose:

* debugging failed tests
* tracking historical runs
* CI artifact uploads

---

### Reporting Layer

The framework generates:

* pytest HTML reports
* failure screenshots
* structured logs

These outputs are designed to be:

* human-readable
* CI-friendly
* easy to archive

---

## Accessibility Integration

The framework integrates with:

```text
pytest-a11y
```

Flow:

```text
Test Execution
   ↓
pytest-a11y plugin
   ↓
axe-core scan
   ↓
Accessibility results
   ↓
HTML + JSON reports + screenshots
```

This allows accessibility testing to run alongside functional UI tests.

---

## Parallel Execution Model

Using `pytest-xdist`, tests can run in parallel:

```bash
pytest -n auto
```

Design considerations:

* test isolation
* independent browser instances
* thread-safe fixtures

---

## Design Principles

### Separation of Concerns

Each layer has a single responsibility:

* tests define behavior
* pages define UI interaction
* framework handles execution

---

### Reusability

* page objects are reusable across tests
* fixtures reduce duplication
* utilities centralize common logic

---

### Scalability

The framework supports:

* large test suites
* multi-browser execution
* parallel testing

---

### CI/CD Compatibility

Designed for integration with:

* GitHub Actions
* GitLab CI
* other pipelines

Supports:

* artifact uploads
* headless execution
* environment configuration

---

## Example Execution Flow

```text
1. pytest discovers tests
2. fixtures initialize WebDriver
3. test calls page object methods
4. Selenium interacts with UI
5. assertions validate results
6. failures trigger screenshots
7. artifacts are written to disk
8. (optional) pytest-a11y runs accessibility scans
```

---

## Project Structure

```text
sel-py-template
│
├── src/
│   ├── pages/
│   ├── utils/
│   └── config/
│
├── tests/
│
├── artifacts/
│
└── docs/
```

---

## Summary

This architecture provides:

* clean separation between test logic and implementation
* scalable test execution model
* strong debugging and reporting capabilities
* extensibility through plugins like pytest-a11y

The framework mirrors patterns used in real-world automation systems, making it
suitable for both learning and production use.
