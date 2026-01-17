from datetime import datetime
from typing import Literal, Protocol, TypedDict

WCAGLevel = Literal["A", "AA", "AAA"]


class WCAGReference(TypedDict):
    criterion: str  # e.g. "1.1.1"
    level: WCAGLevel  # A | AA | AAA
    url: str | None  # Link to WCAG doc


Severity = Literal["critical", "serious", "moderate"]


# ---------------------------
# axe-core result structures
# ---------------------------
class AxeNode(TypedDict):
    html: str
    target: list[str]


class AxeViolation(TypedDict):
    id: str
    description: str
    impact: Severity | None
    help: str
    help_url: str | None
    nodes: list[AxeNode]
    page_url: str
    wcag: list[WCAGReference] | None
    screenshot_path: str | None


class AxeResults(TypedDict):
    violations: list[AxeViolation]


class AxeRunnerProtocol(Protocol):
    def run(self) -> AxeResults: ...
    def violation_count(self, results: AxeResults) -> int: ...


# class BaselineViolation(TypedDict):
#     engine: Literal["axe"]
#     rule_id: str
#     severity: Severity | None
#     wcag: list[WCAGReference] | None
#     fingerprint: str  # stable hash of rule + target


# class BaselineSnapshot(TypedDict):
#     url: str
#     created_at: datetime
#     violations: list[BaselineViolation]


A11YEngine = Literal["axe"]


class A11YRunResults(TypedDict, total=False):
    """
    Results returned from invoking the `check_a11y()` callable.

    Keys are present only when relevant:
      - axe: included if axe ran
      - html_report/json_report: always included when a11y enabled
      - axe_overlay_screenshot: included only if overlay screenshot was taken
    Note: total=False makes all keys optional.
    """

    axe: AxeResults | None
    html_report: str
    json_report: str
    axe_overlay_screenshot: str


class ViolationDetails(TypedDict):
    summary: str
    help: str
    help_url: str
    nodes: list
    tags: list
