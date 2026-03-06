# utils/artifact_config.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_timestamp() -> str:
    """Return a filesystem-safe timestamp string for the current run.

    Returns:
        A string in the format ``run_YYYYMMDD_HHMMSS``, e.g. ``run_20260226_143000``.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _resolve(base: Path, *parts: str) -> Path:
    """Join path parts onto *base* and return the resolved :class:`~pathlib.Path`.

    Args:
        base: The root directory to build from.
        *parts: Additional path segments to append.

    Returns:
        A :class:`~pathlib.Path` representing the combined path.
    """
    return base.joinpath(*parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class ArtifactConfig:
    """Central configuration object for all test artifact paths.

    This class acts as the **single source of truth** for every directory used
    during a test run — logs, screenshots, accessibility reports, HTML/JSON
    reports, and any user-defined extras.  Paths are computed lazily via
    ``@property`` so they always reflect the current ``base_dir`` and
    ``run_folder`` values.

    Args:
        base_dir: Root directory that contains all artifacts.
            Defaults to ``"artifacts"``.
        timestamped_runs: When ``True`` a unique sub-folder is created per run
            (e.g. ``run_20260226_143000``).  When ``False`` artifacts are
            written directly into ``base_dir``.  Defaults to ``True``.
        keep_passed: When ``False`` (default) the caller is responsible for
            cleaning up artifacts that belong to passed tests.  This flag is
            exposed so :class:`~utils.report_plugin.ReportPlugin` can read it;
            no automatic deletion is performed inside this class.
        extras: A mapping of user-defined artifact names to *relative* path
            strings.  Each value is resolved relative to :attr:`run_dir` at
            access time.

            Example::

                ArtifactConfig(extras={"traces": "traces", "videos": "videos"})
                # config.extra("traces") → Path("artifacts/run_.../traces")

        auto_create: When ``True`` (default) all standard directories are
            created on disk as soon as the config is instantiated.

    Example::

        config = ArtifactConfig(
            base_dir="artifacts",
            timestamped_runs=True,
            keep_passed=False,
            extras={"custom_traces": "traces"},
        )

        config.logs          # → Path("artifacts/run_20260226_143000/logs")
        config.screenshots   # → Path("artifacts/run_20260226_143000/screenshots/failures")
        config.a11y_report   # → Path("artifacts/run_20260226_143000/a11y/reports")
        config.html_report   # → Path("artifacts/run_20260226_143000/reports")
        config.extra("custom_traces")  # → Path("artifacts/run_20260226_143000/traces")
    """

    base_dir: str = "artifacts"
    timestamped_runs: bool = True
    keep_passed: bool = False
    extras: dict[str, str] = field(default_factory=dict)
    auto_create: bool = True

    # Private: fixed once per instance so all paths share the same timestamp.
    _run_folder: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialise the run folder and optionally create all directories.

        ``__post_init__`` is a special :mod:`dataclasses` hook that runs
        automatically after ``__init__``.  We use it to freeze the timestamp
        once so every path in the same session shares the same run folder.
        """
        self._run_folder = _make_timestamp() if self.timestamped_runs else ""
        if self.auto_create:
            self.setup()

    # ------------------------------------------------------------------
    # Core directories
    # ------------------------------------------------------------------

    @property
    def run_dir(self) -> Path:
        """Root directory for this specific run.

        Returns:
            ``base_dir`` when timestamped runs are disabled, otherwise
            ``base_dir/run_YYYYMMDD_HHMMSS``.
        """
        base = Path(self.base_dir)
        return base / self._run_folder if self._run_folder else base

    @property
    def logs(self) -> Path:
        """Directory for ``.log`` files generated during the run.

        Returns:
            ``<run_dir>/logs``
        """
        return _resolve(self.run_dir, "logs")

    @property
    def screenshots(self) -> Path:
        """Directory for failure screenshots captured by the driver.

        Returns:
            ``<run_dir>/screenshots/failures``
        """
        return _resolve(self.run_dir, "screenshots", "failures")

    @property
    def a11y_report(self) -> Path:
        """Directory where the accessibility HTML report is written.

        Returns:
            ``<run_dir>/a11y/reports``
        """
        return _resolve(self.run_dir, "a11y", "reports")

    @property
    def html_report(self) -> Path:
        """Directory where the pytest-html report is written.

        Returns:
            ``<run_dir>/reports``
        """
        return _resolve(self.run_dir, "pytest-html")


    # ------------------------------------------------------------------
    # User-defined extras
    # ------------------------------------------------------------------

    def extra(self, name: str) -> Path:
        """Resolve a user-defined artifact directory by name.

        The path is resolved relative to :attr:`run_dir`, so timestamped runs
        keep all extras nested inside the same run folder.

        Args:
            name: Key matching an entry in :attr:`extras`.

        Returns:
            Resolved :class:`~pathlib.Path` for the requested artifact.

        Raises:
            KeyError: If *name* is not present in :attr:`extras`.

        Example::

            config = ArtifactConfig(extras={"traces": "traces"})
            config.extra("traces")  # → Path("artifacts/run_.../traces")
        """
        if name not in self.extras:
            raise KeyError(
                f"'{name}' is not defined in ArtifactConfig.extras. "
                f"Available keys: {list(self.extras)}"
            )
        return _resolve(self.run_dir, self.extras[name])

    # ------------------------------------------------------------------
    # Directory creation
    # ------------------------------------------------------------------

    @property
    def _standard_dirs(self) -> list[Path]:
        """All built-in directories managed by this config.

        Returns:
            List of :class:`~pathlib.Path` objects for every standard artifact
            directory.
        """
        return [
            self.logs,
            self.screenshots,
            self.a11y_report,
            self.html_report,
        ]

    def setup(self) -> None:
        """Create all standard and user-defined artifact directories on disk.

        It is safe to call this multiple times — :func:`~pathlib.Path.mkdir`
        is invoked with ``exist_ok=True`` so no error is raised if a directory
        already exists.

        Returns:
            ``None``
        """
        all_dirs: list[Path] = self._standard_dirs + [
            self.extra(name) for name in self.extras
        ]
        for directory in all_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Convenience / debugging
    # ------------------------------------------------------------------

    def as_dict(self) -> dict[str, Path]:
        """Return all artifact paths as a plain dictionary.

        Useful for logging, debugging, or passing metadata into reports.

        Returns:
            Mapping of artifact name → resolved :class:`~pathlib.Path`.

        Example::

            for name, path in config.as_dict().items():
                print(f"{name}: {path}")
        """
        standard: dict[str, Path] = {
            "logs": self.logs,
            "screenshots": self.screenshots,
            "a11y_report": self.a11y_report,
            "html_report": self.html_report,
        }
        extra_paths: dict[str, Path] = {name: self.extra(name) for name in self.extras}
        return {**standard, **extra_paths}
