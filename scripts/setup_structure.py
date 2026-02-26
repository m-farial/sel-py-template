"""Script to create the complete Selenium framework directory structure."""

import os
from pathlib import Path


def create_directory(path: Path) -> None:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Path object for the directory
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {path}")
    else:
        print(f"○ Exists: {path}")


def create_file(path: Path, content: str = "") -> None:
    """
    Create a file with optional content.

    Args:
        path: Path object for the file
        content: Content to write to the file
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"✓ Created: {path}")
    else:
        print(f"○ Exists: {path}")


def setup_framework_structure() -> None:
    """Create the complete Selenium framework directory structure."""

    print("\n" + "=" * 60)
    print("Setting up Selenium Framework Structure")
    print("=" * 60 + "\n")

    # Get project root (assuming script is in scripts/)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Define directory structure
    directories: list[Path] = [
        # Source directories
        Path("src"),
        Path("src/pages"),
        Path("src/utils"),
        Path("src/config"),
        # Test directories
        Path("tests"),
        # Script directories
        Path("scripts"),
        # Log directories
        Path("logs"),
        Path("logs/screenshots"),
        # GitHub workflows
        Path(".github/workflows"),
    ]

    # Define files with their content
    init_files = {
        "sel_py_template/__init__.py": '"""Source code package."""\n\n__version__ = "1.0.0"\n',
        "sel_py_template/pages/__init__.py": '"""Page Object Models package."""\n\nfrom sel_py_template.pages.base_page import BasePage\n\n__all__ = ["BasePage"]\n',
        "sel_py_template/utils/__init__.py": '"""Utilities package."""\n\nfrom sel_py_template.utils.logger_util import get_logger\n\n__all__ = ["get_logger"]\n',
        "sel_py_template/config/__init__.py": '"""Configuration package."""\n',
        "tests/__init__.py": '"""Test cases package."""\n',
        "scripts/__init__.py": '"""Utility scripts package."""\n',
    }

    gitkeep_content = """# This file ensures the directory is tracked by git
# Files inside this directory are ignored by .gitignore
"""

    # Create directories
    print("Creating directories...")
    for directory in directories:
        create_directory(directory)

    print("\nCreating __init__.py files...")
    for file_path, content in init_files.items():
        create_file(Path(file_path), content)

    # Create .gitkeep for logs
    print("\nCreating .gitkeep files...")
    create_file(Path("logs/.gitkeep"), gitkeep_content)

    # Create placeholder files for key directories
    print("\nCreating placeholder files...")

    # Example page object
    create_file(
        Path("src/sel_py_template/pages/example_page.py"),
        '''"""Example page object - replace with your actual pages."""

from selenium.webdriver.common.by import By
from sel_py_template.pages.base_page import BasePage


class ExamplePage(BasePage):
    """Example page object model."""
    # Locators
    EXAMPLE_LOCATOR = (By.ID, "example")
    def __init__(self, driver):
        """Initialize the example page."""
        super().__init__(driver)
''',
    )

    # Example utility
    create_file(
        Path("src/sel_py_template/utils/example_util.py"),
        '''"""Example utility module."""

def example_function() -> str:
    """Example utility function."""
    return "Hello from utils!"
''',
    )

    # Example test
    create_file(
        Path("tests/test_example.py"),
        '''"""Example test file - replace with your actual tests."""

import pytest


def test_example():
    """Example test case."""
    assert True, "This is an example test"
''',
    )

    # Example script
    create_file(
        Path("scripts/example_script.py"),
        '''"""Example utility script."""

def main():
    """Main function for the script."""
    print("Example script executed!")


if __name__ == "__main__":
    main()
''',
    )

    print("\n" + "=" * 60)
    print("✓ Framework structure created successfully!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Review the created structure")
    print("2. Add your page objects to src/pages/")
    print("3. Add your test cases to tests/")
    print("4. Update .gitignore if needed")
    print("5. Run: poetry install")
    print("6. Run: poetry run pytest")
    print()


if __name__ == "__main__":
    setup_framework_structure()
