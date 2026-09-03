#Requires -Version 5
Set-Location $PSScriptRoot
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $pair = $line.Split("=", 2)
        if ($pair.Count -eq 2) {
            Set-Item -Path ("Env:" + $pair[0].Trim()) -Value $pair[1].Trim().Trim("'").Trim('"')
        }
    }
}
$port = if ($env:MAILTRACE_PORT) { $env:MAILTRACE_PORT } else { "8777" }
Write-Host "MailTrace → http://127.0.0.1:$port  (leave this window open)"
python -m uvicorn app:app --host 127.0.0.1 --port $port
