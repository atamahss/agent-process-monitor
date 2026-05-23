$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python is required to run agent-run."
    exit 1
}

& $python.Source "$PSScriptRoot\agent-run.py" @args
exit $LASTEXITCODE
