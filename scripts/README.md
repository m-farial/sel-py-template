# Create a structure with essential starter files/folders
```bash
python scripts/setup_structure.py
```
## Directory Purposes Quick Reference

| Directory                        | Purpose                       | Gitignored? |
|----------------------------------|-------------------------------|-------------|
| src/pages                        | Page Object Models            | No          |
| src/utils                        | Helper functions              | No          |
| src/config                       | Configuration files           | Partial     |
| tests                            | Test cases                    | No          |
| scripts                          | Automation scripts            | No          |
| logs                             | Test reports & screenshots    | Yes         |
| venv/                            | Virtual environment            | Yes         |
| pyproject.toml                   | Project config, dependencies, tool settings           | No         |
| poetry.lock                      | Locked dependency versions     | No         |


## Basic Directories Generated:
```
sel-py-template/
│
├── .github/                          # GitHub specific files
│   └── workflows/
│       └── test.yml                  # CI/CD pipeline configuration
│
├── src/                              # Source code directory
│   ├── __init__.py
│   │
│   ├── pages/                        # Page Object Models
│   │   ├── __init__.py
│   │   ├── base_page.py              # Base page with common methods
│   │   ├── login_page.py             # Login page object
│   │   ├── inventory_page.py         # Inventory/products page
│   │   ├── cart_page.py              # Shopping cart page
│   │   ├── checkout_page.py          # Checkout flow pages
│   │   └── order_confirmation_page.py
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
├── pyproject.toml                    # Project configuration and dependencies
├── poetry.lock                       # Locked dependency versions
├── README.md                         # Project documentation
├── pytest.ini                        # Pytest configuration (optional)
└── LICENSE                           # Project license
```

## Detailed File Purposes:

### Root Level Files
```
├── .gitignore                        # Ignore logs, cache, .venv, etc.
├── .pre-commit-config.yaml           # Auto-format on commit
├── pyproject.toml                    # All tool configurations
├── poetry.lock                       # Dependency lock file
├── README.md                         # Getting started guide
└── LICENSE                           # MIT/Apache/etc.
```
### src/pages/ - Page Object Models
```
├── base_page.py                      # Common methods (click, wait, get_text)
├── login_page.py                     # Login page locators & methods
├── inventory_page.py                 # Product listing page
├── cart_page.py                      # Shopping cart operations
└── checkout_page.py                  # Checkout flow
```

### src/utils/ - Helper Utilities
```
├── logger_util.py                    # Centralized logging
├── report_plugin.py                  # Custom pytest plugin
├── config_reader.py                  # Read config files
├── data_generator.py                 # Generate test data
└── screenshot_util.py                # Screenshot on failure
```

### tests/ - Test Cases
```
├── conftest.py                       # Fixtures, hooks, CLI options
├── test_login.py                     # Login tests
├── test_inventory.py                 # Browsing tests
├── test_cart.py                      # Cart management tests
├── test_checkout.py                  # Purchase flow tests
└── test_e2e.py                       # Complete user journeys
```

### scripts/ - Automation Scripts
```
├── fmt_lint.py                       # Run formatters & linters
├── clean_cache.py                    # Clean __pycache__, .pytest_cache
├── setup_env.py                      # Initialize project
└── generate_report.py                # Create custom reports
```

### logs/ - Test Artifacts (Gitignored)
```
└── YYYY-MM-DD_HH-MM-SS/
    ├── report.html                   # Test execution report
    ├── test_run.log                  # Detailed logs
    └── screenshots/                  # Failure screenshots
```

## Additional Recommended Directories (Optional):
```
docs/                                 # Documentation
├── architecture.md
├── contributing.md
└── test_strategy.md

fixtures/                             # Test fixtures/data files
├── test_users.json
└── sample_data.csv

resources/                            # Static resources
├── test_files/
└── images/

env/                                  # Environment configs
├── dev.env
├── staging.env
└── prod.env
```