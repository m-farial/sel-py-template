# Troubleshooting

Common issues and how to resolve them.

---

## Tests Not Running

Ensure dependencies are installed:

```bash
poetry install
```

Run:

```bash
poetry run pytest
```

---

## WebDriver Not Found

Make sure the correct browser driver is installed:

* Chrome → chromedriver
* Firefox → geckodriver
* Edge → msedgedriver

---

## Tests Failing in CI but Passing Locally

Possible causes:

* environment differences
* missing environment variables
* browser version mismatch

Fix:

* align versions between local and CI
* verify environment variables

---

## Parallel Execution Issues

If tests fail with `-n auto`:

* ensure tests are isolated
* avoid shared state
* verify fixtures are thread-safe

---

## Accessibility Reports Not Generating

Ensure the flag is used:

```bash
pytest --a11y
```

Without the flag, reports are not created.

---

## Screenshots Not Captured

Check:

* failure actually occurred
* driver is properly initialized
* screenshot logic is not overridden

---

## Import Errors

If you see module import errors:

* verify Poetry environment is active
* run:

```bash
poetry shell
```

---

## Fixture Errors

If pytest cannot find a fixture:

* ensure it is defined in `conftest.py`
* check import paths

---

## Debugging Tips

Run with verbose output:

```bash
pytest -v
```

Use debugger:

```bash
pytest --pdb
```

Add breakpoints:

```python
import pdb; pdb.set_trace()
```

---

## Logs Not Appearing

Check:

* logging configuration
* artifact folder output
* test execution completed successfully

---

## Summary

Most issues fall into:

* environment setup
* driver configuration
* test isolation problems
* missing flags

Start debugging with:

```bash
pytest -v --pdb
```
