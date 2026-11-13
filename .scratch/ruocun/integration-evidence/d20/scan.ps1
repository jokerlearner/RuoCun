# Scan only this review; never expose environment values or matching bytes.
$ErrorActionPreference = 'Stop'
$values = @()
foreach ($item in [Environment]::GetEnvironmentVariables().GetEnumerator()) {
    if ($item.Key -match 'KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|COOKIE|AUTH|CONNECTION|DSN' -and ([string]$item.Value).Length -ge 8) { $values += [string]$item.Value }
}
$script:sensitive = $false
$script:token = $false
function Test-Bytes([byte[]]$bytes) {
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    $wide = [Text.Encoding]::Unicode.GetString($bytes)
    foreach ($value in $values) { if ($text.Contains($value) -or $wide.Contains($value)) { $script:sensitive = $true } }
    if ($text -match '(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})') { $script:token = $true }
}
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$candidate = Join-Path $repo '.scratch/ruocun-discovery/experiments/psec'
$items = Get-ChildItem -LiteralPath $PSScriptRoot,$candidate -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/](\.v|\.c|\.r|\.venv|run|__pycache__)[\\/]' }
foreach ($item in $items) {
    Test-Bytes ([IO.File]::ReadAllBytes($item.FullName))
    if ($item.Extension -eq '.zip') {
        $zip = [IO.Compression.ZipFile]::OpenRead($item.FullName)
        try { foreach ($entry in $zip.Entries) {
            $stream = $entry.Open(); $memory = [IO.MemoryStream]::new()
            try { $stream.CopyTo($memory); Test-Bytes $memory.ToArray() }
            finally { $stream.Dispose(); $memory.Dispose() }
        } } finally { $zip.Dispose() }
    }
}
$result = @{ has_current_sensitive_environment_value = $script:sensitive; has_common_token_pattern = $script:token }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'scan.json'), ($result | ConvertTo-Json).Replace("`r`n", "`n"))
$result | ConvertTo-Json -Compress
if ($script:sensitive -or $script:token) { exit 1 }
exit 0
