param([Parameter(Mandatory=$true)][string]$Executable,
      [Parameter(Mandatory=$true)][string]$OutputStem,
      [string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$info = [Diagnostics.ProcessStartInfo]::new()
$info.FileName = $Executable
$info.UseShellExecute = $false
$info.CreateNoWindow = $true
$info.RedirectStandardOutput = $true
$info.RedirectStandardError = $true
$info.WorkingDirectory = (Get-Location).Path
$info.Environment.Clear()
foreach ($name in @('SystemRoot','WINDIR','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','PROGRAMDATA','COMSPEC','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE','PATHEXT')) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ($null -ne $value) { $info.Environment[$name] = $value }
}
$fixtureHome = Join-Path $PSScriptRoot '.r/home'
[IO.Directory]::CreateDirectory($fixtureHome) | Out-Null
foreach ($name in @('HOME','USERPROFILE','APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME')) { $info.Environment[$name] = $fixtureHome }
$info.Environment['PATH'] = "$(Split-Path -Parent $Executable);C:\Windows\System32;C:\Windows;D:\study_software\Git\cmd"
$info.Environment['PYTHONIOENCODING'] = 'utf-8'
$info.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
$info.Environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
$info.Environment['GIT_CONFIG_NOSYSTEM'] = '1'
$info.Environment['GIT_CONFIG_GLOBAL'] = Join-Path $fixtureHome 'gitconfig'
foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
$stem = [IO.Path]::GetFullPath($OutputStem)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($stem)) | Out-Null
if ([IO.File]::Exists("$stem.exit.json")) { throw 'Never overwrite a completed invocation' }
$out = [IO.File]::Open("$stem.stdout", 'CreateNew', 'Write', 'Read')
$err = [IO.File]::Open("$stem.stderr", 'CreateNew', 'Write', 'Read')
try {
    $process = [Diagnostics.Process]::Start($info)
    $stdout = $process.StandardOutput.BaseStream.CopyToAsync($out)
    $stderr = $process.StandardError.BaseStream.CopyToAsync($err)
    $process.WaitForExit()
    $stdout.GetAwaiter().GetResult()
    $stderr.GetAwaiter().GetResult()
    $receipt = @{ executable = $Executable; arguments = $Arguments; cwd = $info.WorkingDirectory; environment_keys = @($info.Environment.Keys | Sort-Object); exitcode = $process.ExitCode }
    [IO.File]::WriteAllText("$stem.exit.json", ($receipt | ConvertTo-Json -Depth 6))
} finally { $out.Dispose(); $err.Dispose() }
[Console]::WriteLine(($receipt | ConvertTo-Json -Compress -Depth 6))
exit $process.ExitCode
