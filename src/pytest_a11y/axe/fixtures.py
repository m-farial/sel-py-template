from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from src.pytest_a11y.axe.axe_runner import AxeRunner
from src.pytest_a11y.types import AxeRunnerProtocol


@pytest.fixture
def axe(driver: WebDriver) -> AxeRunnerProtocol:
    """
    Provide a ready-to-run axe runner.

    - Assumes the page will be navigated in the test.
    - Injects axe immediately so the next `axe.run()` will work.
      (If your AUT does a full navigation after this fixture runs, you can also
       choose to inject inside `AxeRunner.run()` instead.)
    """
    return AxeRunner(driver)
