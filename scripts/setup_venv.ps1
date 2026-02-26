param(
    [switch]$InstallDeps = $true
)

# Fail fast if Python isn't available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found in PATH. Install Python or add it to PATH."
    exit 1
}

# Create the venv (no-op if already exists)
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "Created .venv"
} else {
    Write-Host ".venv already exists"
}

# Activate the venv in the current shell (dot-source)
. .\.venv\Scripts\Activate.ps1

# Upgrade pip and optionally install dependencies
python -m pip install --upgrade pip
if ($InstallDeps -and (Test-Path "pyproject.toml")) {
    if (Get-Command poetry -ErrorAction SilentlyContinue) {
        poetry install
    } else {
        Write-Warning "Poetry not found — skipping dependency installation. Use 'pip install -r requirements.txt' or install Poetry."
    }
}

Write-Host "`n.venv is active. Run 'deactivate' to exit the virtual environment."