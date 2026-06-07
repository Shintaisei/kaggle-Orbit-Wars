$ErrorActionPreference = "Stop"

$venv = "C:\owv"

if (Test-Path -LiteralPath $venv) {
    Remove-Item -LiteralPath $venv -Recurse -Force
}

python -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install -r requirements.txt
& "$venv\Scripts\python.exe" -m pip install --no-deps "kaggle-environments==1.28.0"

& "$venv\Scripts\python.exe" test_local.py --games 1
