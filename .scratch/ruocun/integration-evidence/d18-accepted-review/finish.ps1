$ErrorActionPreference = 'Stop'
$evidenceRoot = $PSScriptRoot
$repoRoot = [IO.Path]::GetFullPath((Join-Path $evidenceRoot '../../../..'))
$syntheticRoot = Join-Path $repoRoot '.scratch/ruocun-discovery/experiments/durable-io/.t/env'
$setup = Get-Content -LiteralPath (Join-Path $evidenceRoot 'setup.json') -Raw | ConvertFrom-Json
$pythonPath = Join-Path $setup.venv 'Scripts/python.exe'
$start = [Diagnostics.ProcessStartInfo]::new($pythonPath)
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$start.WorkingDirectory = $repoRoot
$start.ArgumentList.Add((Join-Path $evidenceRoot 'finish.py'))
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
# No captured output is displayed; the parent scan below examines all new bytes.
[IO.File]::WriteAllText((Join-Path $evidenceRoot 'finish.stdout.txt'), $stdout)
[IO.File]::WriteAllText((Join-Path $evidenceRoot 'finish.stderr.txt'), $stderr)
@{returncode=$process.ExitCode;command=@($pythonPath,(Join-Path $evidenceRoot 'finish.py'));environment_keys=@($start.Environment.Keys | Sort-Object)} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'finish.exit.json') -Encoding utf8
& (Join-Path $evidenceRoot 'bootstrap.ps1') -Mode 'finish'
if ($process.ExitCode -ne 0) { throw "Supplemental review exited $($process.ExitCode); logs retained and scanned." }
