# start.ps1 — Maverick 一鍵啟動 (Windows PowerShell)
# 用法：在此資料夾按右鍵「以 PowerShell 執行」，或在終端機輸入：  .\start.ps1
# 若被執行原則擋下，可先跑：  powershell -ExecutionPolicy Bypass -File .\start.ps1

$ErrorActionPreference = "Stop"

# 切到腳本所在資料夾（不管從哪裡呼叫都正確）
Set-Location -Path $PSScriptRoot

Write-Host "=== Maverick 啟動器 ===" -ForegroundColor Cyan

# 1) 找 Python
$py = $null
foreach ($cmd in @("python", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) { $py = $cmd; break }
}
if (-not $py) {
    Write-Host "找不到 Python。請先安裝 Python 3.11+ 並勾選 Add to PATH：https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "按 Enter 結束"
    exit 1
}

# 2) 虛擬環境（第一次會自動建立）
$venv = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "[1/3] 首次執行，建立虛擬環境 .venv ..." -ForegroundColor Yellow
    & $py -m venv $venv
}
$pyExe = Join-Path $venv "Scripts\python.exe"

# 3) 安裝 / 更新依賴（只在 requirements.txt 有變動時重裝）
$req = Join-Path $PSScriptRoot "requirements.txt"
$stamp = Join-Path $venv ".req.installed"
$needInstall = $true
if ((Test-Path $stamp) -and (Test-Path $req)) {
    if ((Get-Item $req).LastWriteTime -le (Get-Item $stamp).LastWriteTime) {
        $needInstall = $false
    }
}
if ($needInstall -and (Test-Path $req)) {
    Write-Host "[2/3] 安裝依賴套件..." -ForegroundColor Yellow
    & $pyExe -m pip install --upgrade pip | Out-Null
    & $pyExe -m pip install -r $req
    Set-Content -Path $stamp -Value (Get-Date)
} else {
    Write-Host "[2/3] 依賴已是最新，略過安裝。" -ForegroundColor DarkGray
}

# 4) 檢查 Ollama（本地模型，非強制，僅提醒）
if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    $models = ""
    try { $models = (ollama list 2>$null | Out-String) } catch { $models = "" }
    if ($models -match "gpt-oss") {
        Write-Host "[3/3] 偵測到 Ollama 與 gpt-oss 模型。" -ForegroundColor Green
    } else {
        Write-Host "[3/3] 偵測到 Ollama，但似乎沒有 gpt-oss 模型（預設大腦）。請先執行：  ollama pull gpt-oss:20b" -ForegroundColor Yellow
    }
} else {
    Write-Host "[3/3] 找不到 Ollama。預設本地模型需要它：https://ollama.com/download" -ForegroundColor Yellow
    Write-Host "      （若只想用雲端模型，設定 MAVERICK_ENABLE_CLOUD=1 與 OPENAI_API_KEY 後仍可啟動）" -ForegroundColor DarkGray
}

# 5) 啟動 Maverick
Write-Host ""
Write-Host "啟動 Maverick..." -ForegroundColor Cyan
Write-Host ""
& $pyExe (Join-Path $PSScriptRoot "cli.py")
