from __future__ import annotations

from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from template_tests.integration.fixtures_html import FORM_WORKFLOW_HTML
from template_tests.integration.helpers import write_html

from sel_py_template.pages.base_page import BasePage
from sel_py_template.ui.elements import Element, ElementType


class WorkflowPage(BasePage):
    """Page object for the local smoke workflow fixture."""

    name_input: Element = Element("full-name", ElementType.TEXT_INPUT, name="Full name")
    role_dropdown: Element = Element(
        "role",
        ElementType.DROPDOWN,
        by=By.ID,
        name="Role dropdown",
    )
    agreement_checkbox: Element = Element(
        "agree",
        ElementType.CHECKBOX,
        by=By.ID,
        name="Agreement checkbox",
    )
    submit_button: Element = Element(
        "submit-btn",
        ElementType.BUTTON,
        by=By.ID,
        name="Submit button",
    )
    status: Element = Element("status", ElementType.TOAST, by=By.ID, name="Status")
    submitted_name: Element = Element(
        "submitted-name",
        ElementType.TOAST,
        by=By.ID,
        name="Submitted name",
    )
    submitted_role: Element = Element(
        "submitted-role",
        ElementType.TOAST,
        by=By.ID,
        name="Submitted role",
    )
    submitted_agreement: Element = Element(
        "submitted-agreement",
        ElementType.TOAST,
        by=By.ID,
        name="Submitted agreement",
    )


@pytest.mark.integration
class TestSmokeWorkflow:
    """End-to-end smoke tests for the local form workflow fixture."""

    def test_end_to_end_form_workflow_local_fixture(
        self,
        driver: WebDriver,
        browser_name: str,
        tmp_path: Path,
        logger,
    ) -> None:
        """
        Run a full local end-to-end workflow through the template page-object layer.
        """
        url = write_html(tmp_path, "form_workflow.html", FORM_WORKFLOW_HTML)
        page = WorkflowPage(driver, browser=browser_name)

        page.navigate(url)

        assert driver.session_id is not None, "Expected active browser session"

        page.name_input.type("Farial")
        page.role_dropdown.select_option(value="qa")
        page.agreement_checkbox.set_checked(True)
        page.submit_button.click()

        assert page.status.text() == "Submission complete"
        assert page.submitted_name.text() == "Name: Farial"
        assert page.submitted_role.text() == "Role: qa"
        assert page.submitted_agreement.text() == "Agreed: yes"

        logger.info("✓ End-to-end smoke workflow completed successfully")
