from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class ArtifactConfig:
    """Configuration for organizing test artifacts for a single pytest run.

    Attributes:
        base_dir: Root directory under which all artifact folders are created.
        create_daily_folder: Whether to create a date-based folder under ``base_dir``.
        timestamped_runs: Whether each run folder should include a timestamp-based name.
        pytest_html_dirname: Folder name for pytest HTML and JSON-style report assets.
        failure_screenshots_dirname: Folder name for failure screenshots under
            ``pytest_html_dirname``.
        a11y_dirname: Folder name for accessibility artifacts.
        violation_screenshots_dirname: Folder name for accessibility violation screenshots
            under ``a11y_dirname``.
        pytest_html_filename: Filename for the main pytest HTML report.
        pytest_metadata_filename: Filename for the pytest-html-plus metadata file.
        a11y_html_filename: Filename for the accessibility HTML report.
        extra_artifacts: Additional user-defined artifact directories keyed by logical
            artifact name. Relative paths are resolved from the current run root.
    """

    base_dir: Path = Path("artifacts")
    create_daily_folder: bool = True
    timestamped_runs: bool = True
    pytest_html_dirname: str = "pytest_html"
    failure_screenshots_dirname: str = "failure_screenshots"
    a11y_dirname: str = "a11y"
    violation_screenshots_dirname: str = "violation_screenshots"
    pytest_html_filename: str = "report.html"
    pytest_metadata_filename: str = "plus_metadata.json"
    a11y_html_filename: str = "a11y_report.html"
    extra_artifacts: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ArtifactPaths:
    """Resolved filesystem paths for a single pytest run."""

    run_root: Path
    log_file: Path
    pytest_html_dir: Path
    pytest_html_report: Path
    pytest_metadata_file: Path
    failure_screenshots_dir: Path
    a11y_dir: Path
    a11y_html_report: Path
    violation_screenshots_dir: Path
    extra_dirs: dict[str, Path] = field(default_factory=dict)


@dataclass(slots=True)
class ArtifactProducer:
    """Represents a plugin or feature contributing artifact directories."""

    name: str
    directories: dict[str, str] = field(default_factory=dict)


class ArtifactManager:
    """Create and expose the directory structure for test artifacts.

    The structure is organized as:

    ``base_dir / YYYY-MM-DD / run_HHMMSS``

    The run root contains the session log file directly, while report-specific assets are
    grouped under ``pytest_html`` and ``a11y`` folders.
    """

    def __init__(
        self,
        config: ArtifactConfig,
        *,
        browser: str,
        a11y_enabled: bool = False,
        now: datetime | None = None,
    ) -> None:
        """Initialize the artifact manager.

        Args:
            config: Artifact path configuration.
            browser: Browser label used in the session log filename.
            a11y_enabled: Whether accessibility-specific folders should be created.
            now: Optional datetime override for deterministic tests.
        """
        self.config = config
        self.browser = browser
        self.a11y_enabled = a11y_enabled
        self.now = now or datetime.now()
        self._producers: dict[str, ArtifactProducer] = {}
        self._producer_dirs: dict[str, dict[str, Path]] = {}
        self.paths = self._build_paths()

    def _build_paths(self) -> ArtifactPaths:
        """Build all filesystem paths for the current test run."""
        daily_root = self.config.base_dir
        if self.config.create_daily_folder:
            daily_root = daily_root / self.now.strftime("%Y-%m-%d")

        run_name = (
            f"run_{self.now.strftime('%H%M%S')}"
            if self.config.timestamped_runs
            else "run"
        )
        run_root = daily_root / run_name

        log_file = (
            run_root / f"{self.browser}_test_run_{self.now.strftime('%H-%M-%S')}.log"
        )
        pytest_html_dir = run_root / self.config.pytest_html_dirname
        a11y_dir = run_root / self.config.a11y_dirname

        extra_dirs = {
            name: self._resolve_artifact_dir(raw_path, run_root)
            for name, raw_path in self.config.extra_artifacts.items()
        }

        return ArtifactPaths(
            run_root=run_root,
            log_file=log_file,
            pytest_html_dir=pytest_html_dir,
            pytest_html_report=pytest_html_dir / self.config.pytest_html_filename,
            pytest_metadata_file=pytest_html_dir / self.config.pytest_metadata_filename,
            failure_screenshots_dir=(
                pytest_html_dir / self.config.failure_screenshots_dirname
            ),
            a11y_dir=a11y_dir,
            a11y_html_report=a11y_dir / self.config.a11y_html_filename,
            violation_screenshots_dir=(
                a11y_dir / self.config.violation_screenshots_dirname
            ),
            extra_dirs=extra_dirs,
        )

    @staticmethod
    def _resolve_artifact_dir(raw_path: str, run_root: Path) -> Path:
        """Resolve an artifact directory relative to the run root when needed."""
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return candidate
        return run_root / candidate

    def register_producer(self, name: str, directories: dict[str, str]) -> None:
        """Register plugin-defined artifact directories.

        Producer-defined directories act as defaults. If the same artifact name was
        explicitly defined in ``config.extra_artifacts``, the user-defined location wins.

        Args:
            name: Unique producer name, such as ``playwright``.
            directories: Mapping of logical artifact names to relative or absolute paths.

        Raises:
            ValueError: If the producer name is empty or an artifact name/path is blank.
        """
        producer_name = name.strip()
        if not producer_name:
            raise ValueError("Producer name cannot be empty.")

        normalized_directories: dict[str, str] = {}
        resolved_dirs: dict[str, Path] = {}

        for artifact_name, raw_path in directories.items():
            normalized_name = artifact_name.strip()
            normalized_path = raw_path.strip()

            if not normalized_name:
                raise ValueError(
                    f"Producer {producer_name!r} contains an empty artifact name."
                )
            if not normalized_path:
                raise ValueError(
                    f"Producer {producer_name!r} artifact {normalized_name!r} has an empty path."
                )

            normalized_directories[normalized_name] = normalized_path

            if normalized_name in self.config.extra_artifacts:
                resolved = self._resolve_artifact_dir(
                    self.config.extra_artifacts[normalized_name],
                    self.paths.run_root,
                )
            else:
                resolved = self._resolve_artifact_dir(
                    normalized_path,
                    self.paths.run_root,
                )
                self.paths.extra_dirs[normalized_name] = resolved

            resolved_dirs[normalized_name] = resolved

        self._producers[producer_name] = ArtifactProducer(
            name=producer_name,
            directories=normalized_directories,
        )
        self._producer_dirs[producer_name] = resolved_dirs

    def create_directories(self) -> None:
        """Create the required directories for the run.

        Always creates the run root and ``pytest_html`` folder. Accessibility folders are
        created only when ``a11y_enabled`` is true. Extra artifact directories and
        producer-registered directories are also created.
        """
        self.paths.run_root.mkdir(parents=True, exist_ok=True)
        self.paths.pytest_html_dir.mkdir(parents=True, exist_ok=True)
        self.paths.failure_screenshots_dir.mkdir(parents=True, exist_ok=True)

        if self.a11y_enabled:
            self.paths.a11y_dir.mkdir(parents=True, exist_ok=True)
            self.paths.violation_screenshots_dir.mkdir(parents=True, exist_ok=True)

        for extra_dir in self.paths.extra_dirs.values():
            extra_dir.mkdir(parents=True, exist_ok=True)

        for producer_dirs in self._producer_dirs.values():
            for producer_dir in producer_dirs.values():
                producer_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_nodeid(nodeid: str) -> str:
        """Convert a pytest node id or test name into a filesystem-safe string."""
        sanitized = (
            nodeid.replace("::", "__")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )
        return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in sanitized)

    def failure_screenshot_path(
        self, nodeid: str, timestamp: str | None = None
    ) -> Path:
        """Return the failure screenshot path for a given test."""
        suffix = f"_{timestamp}" if timestamp else ""
        filename = f"{self.sanitize_nodeid(nodeid)}{suffix}.png"
        return self.paths.failure_screenshots_dir / filename

    def failure_log_path(self, nodeid: str, timestamp: str | None = None) -> Path:
        """Return the failure log path for a given test.

        Failure logs are kept at the run root so that run-level debugging assets stay easy
        to discover next to the main session log.
        """
        suffix = f"_{timestamp}" if timestamp else ""
        filename = f"{self.sanitize_nodeid(nodeid)}{suffix}_failure.log"
        return self.paths.run_root / filename

    def get_extra_dir(self, name: str, create: bool = True) -> Path:
        """Return a configured or producer-registered extra artifact directory."""
        if name not in self.paths.extra_dirs:
            raise KeyError(f"Unknown extra artifact directory: {name}")

        path = self.paths.extra_dirs[name]
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_extra_file(
        self,
        name: str,
        filename: str,
        create_parent: bool = True,
    ) -> Path:
        """Return a file path inside an extra artifact directory."""
        directory = self.get_extra_dir(name, create=create_parent)
        return directory / filename

    def get_producer_dirs(self, producer_name: str) -> dict[str, Path]:
        """Return resolved artifact directories for a registered producer."""
        if producer_name not in self._producer_dirs:
            raise KeyError(f"Unknown artifact producer: {producer_name}")
        return dict(self._producer_dirs[producer_name])

    def get_registered_producers(self) -> dict[str, dict[str, Path]]:
        """Return all registered producers and their resolved directories."""
        return {
            producer_name: dict(paths)
            for producer_name, paths in self._producer_dirs.items()
        }
