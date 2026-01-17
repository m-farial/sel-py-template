# ============================================================================
# types.py - Core type definitions
# ============================================================================
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol, TypedDict

WCAGLevel = Literal["A", "AA", "AAA"]
Severity = Literal["critical", "serious", "moderate", "minor"]


class WCAGReference(TypedDict):
    """WCAG criterion reference."""
    criterion: str  # e.g. "1.1.1"
    level: WCAGLevel
    url: str | None


# ============================================================================
# Raw axe-core result types
# ============================================================================

class AxeNode(TypedDict, total=False):
    """A single affected DOM node from axe-core."""
    target: list[str]
    html: str
    impact: Severity | None
    failureSummary: str


class AxeViolation(TypedDict, total=False):
    """A single violation result from axe-core."""
    id: str
    description: str
    impact: Severity | None
    help: str
    helpUrl: str
    nodes: list[AxeNode]
    tags: list[str]
    screenshot_path: str | None


class AxeTestResult(TypedDict, total=False):
    """A passing test result from axe-core."""
    id: str
    description: str
    impact: Severity | None
    help: str
    helpUrl: str
    nodes: list[AxeNode]
    tags: list[str]


class AxeResults(TypedDict):
    """Complete results from axe.run()."""
    violations: list[AxeViolation]
    passes: list[AxeTestResult]
    incomplete: list[AxeViolation]
    inapplicable: list[AxeViolation]
    timestamp: str
    url: str


# ============================================================================
# Processed/structured types for application use
# ============================================================================

@dataclass
class ProcessedNode:
    """Structured node information for reporting."""
    selector: str
    all_selectors: list[str]
    html: str
    failure_summary: str
    impact: Severity | None

    @staticmethod
    def from_axe_node(node: AxeNode) -> ProcessedNode:
        """
        Convert raw AxeNode to ProcessedNode.
        
        Args:
            node: Raw node data from axe-core result
            
        Returns:
            Structured ProcessedNode with normalized data
        """
        targets = node.get("target", [])
        selector = targets[0] if targets else "unknown"
        
        return ProcessedNode(
            selector=selector,
            all_selectors=targets if targets else [],
            html=node.get("html", ""),
            failure_summary=node.get("failureSummary", ""),
            impact=node.get("impact"),
        )


@dataclass
class ProcessedViolation:
    """Fully processed violation ready for reporting."""
    id: str
    description: str
    impact: Severity | None
    help: str
    help_url: str
    nodes: list[ProcessedNode]
    tags: list[str]
    screenshot_path: str | None = None
    
    @property
    def summary(self) -> str:
        """
        Generate formatted summary line for display.
        
        Returns:
            Summary string like "[CRITICAL] Issue description (rule: id, affected nodes: N)"
        """
        impact_str = (self.impact or "unknown").upper()
        return (
            f"[{impact_str}] {self.description} "
            f"(rule: {self.id}, affected nodes: {len(self.nodes)})"
        )

    @staticmethod
    def from_axe_violation(violation: AxeViolation) -> ProcessedViolation:
        """
        Convert raw AxeViolation to ProcessedViolation.
        
        Args:
            violation: Raw violation from axe-core result
            
        Returns:
            Structured ProcessedViolation with normalized nodes
        """
        nodes = [
            ProcessedNode.from_axe_node(node)
            for node in violation.get("nodes", [])
        ]
        
        return ProcessedViolation(
            id=violation.get("id", "unknown"),
            description=violation.get("description", "Unknown violation"),
            impact=violation.get("impact"),
            help=violation.get("help", "N/A"),
            help_url=violation.get("helpUrl", ""),
            nodes=nodes,
            tags=violation.get("tags", []),
            screenshot_path=violation.get("screenshot_path"),
        )


@dataclass
class ProcessedResults:
    """Fully processed axe results ready for application use."""
    url: str
    timestamp: str
    violations: list[ProcessedViolation]
    passes: list[ProcessedViolation]
    incomplete: list[ProcessedViolation]
    inapplicable: list[ProcessedViolation]
    
    @property
    def violation_count(self) -> int:
        """Total number of violations found."""
        return len(self.violations)
    
    @property
    def pass_count(self) -> int:
        """Total number of passed checks."""
        return len(self.passes)
    
    @property
    def has_violations(self) -> bool:
        """Whether any violations were found."""
        return self.violation_count > 0
    
    @classmethod
    def from_axe_results(cls, results: AxeResults) -> ProcessedResults:
        """
        Convert raw axe-core results to fully processed format.
        
        This is the main entry point for processing axe.run() results.
        
        Args:
            results: Raw results dict from axe.run()
        
        Returns:
            ProcessedResults with all data structured and typed
        """
        return cls(
            url=results.get("url", "unknown"),
            timestamp=results.get("timestamp", ""),
            violations=[
                ProcessedViolation.from_axe_violation(v)
                for v in results.get("violations", [])
            ],
            passes=[
                ProcessedViolation.from_axe_violation(p)
                for p in results.get("passes", [])
            ],
            incomplete=[
                ProcessedViolation.from_axe_violation(i)
                for i in results.get("incomplete", [])
            ],
            inapplicable=[
                ProcessedViolation.from_axe_violation(ia)
                for ia in results.get("inapplicable", [])
            ],
        )


class AxeRunnerProtocol(Protocol):
    """Protocol for axe-core runner implementations."""
    
    def run(self) -> AxeResults:
        """
        Run axe-core accessibility checks.
        
        Returns:
            Complete AxeResults from the check run
        """
        ...
    
    def violation_count(self, results: AxeResults) -> int:
        """
        Count violations in results.
        
        Args:
            results: AxeResults from a run
            
        Returns:
            Total number of violations
        """
        ...


class A11YRunResults(TypedDict, total=False):
    """
    Results returned from check_a11y() fixture.
    
    All keys are optional depending on configuration.
    """
    axe: AxeResults | None
    html_report: str
    json_report: str
    screenshot_dir: str