$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$VenvPath = "C:\venvs\comp4010-dashboard"
if (!(Test-Path $VenvPath)) { py -m venv $VenvPath }
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. "$VenvPath\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
python tests\test_smoke.py
python tests\test_json_safety.py
python tests\test_data_contract.py
python -m shiny run --launch-browser --port 8001 app.py
