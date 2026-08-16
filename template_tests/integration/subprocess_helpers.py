from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

# Resolve the repository root relative to this file's location so the path is
# correct regardless of which directory pytest is invoked from.
# __file__ is this test file  → .parent is tests/integration/
#                              → .parent is tests/
#                              → .parent is the repo root
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]


def _is_path_inside(child: Path, parent: Path) -> bool:
    """Return True when child is inside parent."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class PytestRunResult:
    """Structured result for a subprocess pytest run."""

    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    run_dir: Path | None


def write_text_file(path: Path, content: str) -> Path:
    """
    Write a text file, creating parent directories if needed.

    Args:
        path: Destination file path.
        content: File content.

    Returns:
        The written path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def latest_run_dir(artifacts_root: Path) -> Path | None:
    """
    Return the most recently modified run_* artifact directory.

    Expected layout:
        artifacts/YYYY-MM-DD/run_HHMMSS/

    Args:
        artifacts_root: Base artifacts directory.

    Returns:
        Latest run directory or None if not found.
    """
    if not artifacts_root.exists():
        return None

    candidates = [
        path
        for date_dir in artifacts_root.iterdir()
        if date_dir.is_dir()
        for path in date_dir.glob("run_*")
        if path.is_dir()
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def run_pytest_subprocess(
    project_root: Path,
    test_path: Path,
    *extra_args: str,
    artifacts_root: Path | None = None,
) -> PytestRunResult:
    """
    Run pytest in a subprocess and return output plus detected artifact folder.

    Args:
        project_root: Repository root.
        test_path: Test file to execute.
        extra_args: Additional pytest CLI arguments.
        artifacts_root: Base artifacts directory for the subprocess run.
            If omitted, defaults to ``project_root / 'artifacts'``.

    Returns:
        Structured subprocess result.
    """
    safe_test_path = test_path
    artifacts_root = artifacts_root or project_root / "artifacts"

    if not _is_path_inside(test_path, project_root):
        with tempfile.TemporaryDirectory(
            dir=project_root, prefix="pytest_subprocess_"
        ) as temp_dir:
            safe_test_path = Path(temp_dir) / test_path.name
            shutil.copy2(test_path, safe_test_path)
            command = [
                sys.executable,
                "-m",
                "pytest",
                str(safe_test_path),
                *extra_args,
            ]
            completed = subprocess.run(  # noqa: S603 — command is built from trusted internal inputs only
                command,
                cwd=project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
    else:
        command = [
            sys.executable,
            "-m",
            "pytest",
            str(test_path),
            *extra_args,
        ]
        completed = subprocess.run(  # noqa: S603 — command is built from trusted internal inputs only
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    run_dir = latest_run_dir(artifacts_root)
    return PytestRunResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        command=command,
        run_dir=run_dir,
    )


def assert_file_exists(path: Path, description: str) -> None:
    """
    Assert a file exists with a useful message.

    Args:
        path: File path.
        description: Human-readable description.
    """
    assert path.is_file(), f"Expected {description} at: {path}"


def make_subprocess_artifacts_root(tmp_path: Path) -> Path:
    """
    Return a dedicated artifact root for subprocess pytest executions.

    This makes subprocess artifacts easy to identify and keeps them separate
    from the main test session's artifacts.
    """
    return tmp_path / "subprocess_artifacts"


def assert_dir_exists(path: Path, description: str) -> None:
    """
    Assert a directory exists with a useful message.

    Args:
        path: Directory path.
        description: Human-readable description.
    """
    assert path.is_dir(), f"Expected {description} at: {path}"
