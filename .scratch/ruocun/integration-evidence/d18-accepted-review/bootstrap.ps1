param([string]$Mode = 'run')
$ErrorActionPreference = 'Stop'
$evidenceRoot = $PSScriptRoot
$repoRoot = [IO.Path]::GetFullPath((Join-Path $evidenceRoot '../../../..'))
$labRoot = Join-Path $repoRoot '.scratch/ruocun-discovery/experiments/durable-io'
$syntheticRoot = Join-Path $labRoot '.t/env'
$sensitiveValues = @(Get-ChildItem Env: | Where-Object { $_.Name -match 'KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH' -and $_.Value.Length -ge 8 } | ForEach-Object Value)
function Test-SensitiveBytes([byte[]]$Bytes) {
    $content = [Text.Encoding]::UTF8.GetString($Bytes)
    foreach ($secretValue in $sensitiveValues) { if ($content.Contains($secretValue)) { return $true } }
    return $content -match '(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[opusr]_[A-Za-z0-9]{24,})'
}
if ($Mode -eq 'run') {
    $pythonPath = (Get-Command python).Source
    $start = [Diagnostics.ProcessStartInfo]::new($pythonPath)
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.WorkingDirectory = $repoRoot
    $start.ArgumentList.Add((Join-Path $evidenceRoot 'review.py'))
    $start.Environment.Clear()
    foreach ($envName in @('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','SYSTEMDRIVE')) {
        $envValue = [Environment]::GetEnvironmentVariable($envName)
        if ($null -ne $envValue) { $start.Environment[$envName] = $envValue }
    }
    $folders = @{HOME='home';USERPROFILE='home';APPDATA='app';LOCALAPPDATA='local';TEMP='tmp';TMP='tmp';XDG_CONFIG_HOME='config';XDG_CACHE_HOME='cache';XDG_DATA_HOME='data';PIP_CACHE_DIR='pipcache'}
    foreach ($envName in $folders.Keys) {
        $folderPath = Join-Path $syntheticRoot $folders[$envName]
        [IO.Directory]::CreateDirectory($folderPath) | Out-Null
        $start.Environment[$envName] = $folderPath
    }
    foreach ($envName in @('PYTHONUTF8','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE','PIP_DISABLE_PIP_VERSION_CHECK')) { $start.Environment[$envName] = '1' }
    $start.Environment['PIP_CONFIG_FILE'] = 'NUL'
    $process = [Diagnostics.Process]::Start($start)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    if ((Test-SensitiveBytes ([Text.Encoding]::UTF8.GetBytes($stdout))) -or (Test-SensitiveBytes ([Text.Encoding]::UTF8.GetBytes($stderr)))) { throw 'Sensitive output present; suppressed.' }
    [IO.File]::WriteAllText((Join-Path $evidenceRoot 'bootstrap.stdout.txt'), $stdout)
    [IO.File]::WriteAllText((Join-Path $evidenceRoot 'bootstrap.stderr.txt'), $stderr)
    @{returncode=$process.ExitCode; command=@($pythonPath,(Join-Path $evidenceRoot 'review.py'));environment_keys=@($start.Environment.Keys | Sort-Object);sensitive_present=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'bootstrap.exit.json') -Encoding utf8
    if ($process.ExitCode -ne 0) { throw "Independent collector exited $($process.ExitCode); logs retained and scanned." }
}
$filesScanned = 0
$zipMembersScanned = 0
foreach ($file in Get-ChildItem -LiteralPath $evidenceRoot -Recurse -File) {
    if (Test-SensitiveBytes ([IO.File]::ReadAllBytes($file.FullName))) { throw 'Sensitive evidence present; do not publish.' }
    $filesScanned++
    if ($file.Extension -eq '.zip') {
        $archive = [IO.Compression.ZipFile]::OpenRead($file.FullName)
        try {
            foreach ($entry in $archive.Entries) {
                $stream = $entry.Open()
                $buffer = [IO.MemoryStream]::new()
                try { $stream.CopyTo($buffer); if (Test-SensitiveBytes $buffer.ToArray()) { throw 'Sensitive archive member present; do not publish.' } }
                finally { $stream.Dispose(); $buffer.Dispose() }
                $zipMembersScanned++
            }
        } finally { $archive.Dispose() }
    }
}
@{current_real_parent_environment_used_for_comparison=$true;known_sensitive_value_present=$false;token_shape_present=$false;credential_values_saved_or_printed=$false;files_scanned=$filesScanned;zip_members_scanned=$zipMembersScanned} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidenceRoot ('sensitive-scan-' + $Mode + '.json')) -Encoding utf8
Write-Output "Independent evidence scan passed; sensitive value present: false; files: $filesScanned; archive members: $zipMembersScanned."
