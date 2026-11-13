param([ValidateSet('seal','reseal','stage','check','identity')][string]$Mode = 'check')
$ErrorActionPreference = 'Stop'
$evidenceRoot = $PSScriptRoot
$repoRoot = [IO.Path]::GetFullPath((Join-Path $evidenceRoot '../../../..'))
$syntheticRoot = Join-Path $repoRoot '.scratch/ruocun-discovery/experiments/durable-io/.t/env'
if ($Mode -in @('seal','reseal')) { & (Join-Path $evidenceRoot 'bootstrap.ps1') -Mode 'preseal' }
$setup = Get-Content -LiteralPath (Join-Path $evidenceRoot 'setup.json') -Raw | ConvertFrom-Json
$start = [Diagnostics.ProcessStartInfo]::new((Join-Path $setup.venv 'Scripts/python.exe'))
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$start.WorkingDirectory = $repoRoot
$start.ArgumentList.Add((Join-Path $evidenceRoot 'seal.py'))
$start.ArgumentList.Add($Mode)
$start.Environment.Clear()
foreach ($envName in @('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','SYSTEMDRIVE')) {
    $envValue = [Environment]::GetEnvironmentVariable($envName)
    if ($null -ne $envValue) { $start.Environment[$envName] = $envValue }
}
$folders = @{HOME='home';USERPROFILE='home';APPDATA='app';LOCALAPPDATA='local';TEMP='tmp';TMP='tmp';XDG_CONFIG_HOME='config';XDG_CACHE_HOME='cache';XDG_DATA_HOME='data';PIP_CACHE_DIR='pipcache'}
foreach ($envName in $folders.Keys) { $start.Environment[$envName] = Join-Path $syntheticRoot $folders[$envName] }
foreach ($envName in @('PYTHONUTF8','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE','PIP_DISABLE_PIP_VERSION_CHECK')) { $start.Environment[$envName] = '1' }
$start.Environment['PIP_CONFIG_FILE'] = 'NUL'
$process = [Diagnostics.Process]::Start($start)
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
$sensitiveValues = @(Get-ChildItem Env: | Where-Object { $_.Name -match 'KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH' -and $_.Value.Length -ge 8 } | ForEach-Object Value)
foreach ($secretValue in $sensitiveValues) { if (($stdout + $stderr).Contains($secretValue)) { throw 'Sensitive output present; suppressed.' } }
if (($stdout + $stderr) -match '(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[opusr]_[A-Za-z0-9]{24,})') { throw 'Sensitive token shape present; suppressed.' }
if ($process.ExitCode -ne 0) {
    $failureRoot = Join-Path $evidenceRoot ('seal-failure-' + $Mode + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    [IO.Directory]::CreateDirectory($failureRoot) | Out-Null
    [IO.File]::WriteAllText((Join-Path $failureRoot 'stdout.txt'), $stdout)
    [IO.File]::WriteAllText((Join-Path $failureRoot 'stderr.txt'), $stderr)
    throw "Seal step failed with exit $($process.ExitCode); scanned failure retained."
}
Write-Output $stdout
