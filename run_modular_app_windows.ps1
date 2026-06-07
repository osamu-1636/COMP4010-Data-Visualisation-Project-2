$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (!(Test-Path ".venv")) { py -m venv .venv }
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python tests\test_smoke.py
python tests\test_json_safety.py
python tests\test_data_contract.py
python -m shiny run --launch-browser --port 8001 app.py
