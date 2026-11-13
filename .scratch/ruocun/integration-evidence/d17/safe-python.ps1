param([Parameter(Mandatory=$true)][string]$Executable, [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$processInfo = [Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = $Executable
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.WorkingDirectory = (Get-Location).Path
$processInfo.Environment.Clear()
$allowed = @('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','HOMEDRIVE','HOMEPATH','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','COMSPEC','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE','PATHEXT','USERNAME','USERDOMAIN')
foreach ($name in $allowed) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ($null -ne $value) { $processInfo.Environment[$name] = $value }
}
$processInfo.Environment['PATH'] = "$(Split-Path -Parent $Executable);C:\Windows\System32;C:\Windows;D:\study_software\Git\cmd"
$processInfo.Environment['PYTHONIOENCODING'] = 'utf-8'
$processInfo.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
$syntheticHome = Join-Path (Get-Location).Path '.scratch/ruocun-discovery/experiments/windows/run/m17-synthetic-home'
$processInfo.Environment['HOME'] = $syntheticHome
$processInfo.Environment['XDG_CONFIG_HOME'] = Join-Path $syntheticHome 'config'
$processInfo.Environment['XDG_DATA_HOME'] = Join-Path $syntheticHome 'data'
$processInfo.Environment['XDG_CACHE_HOME'] = Join-Path $syntheticHome 'cache'
foreach ($argument in $Arguments) { $processInfo.ArgumentList.Add($argument) }
$process = [Diagnostics.Process]::Start($processInfo)
$stdout = $process.StandardOutput.ReadToEndAsync()
$stderr = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
if ($stdout.Result) { [Console]::Write($stdout.Result) }
if ($stderr.Result) { [Console]::Error.Write($stderr.Result) }
exit $process.ExitCode
