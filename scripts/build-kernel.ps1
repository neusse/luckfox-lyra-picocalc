[CmdletBinding()]
param(
    [string]$Target = "kernel-stage",
    [string]$WslDistro = "Ubuntu-22.04"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EscapedProjectRoot = $ProjectRoot.Replace("\", "\\")
$WslProjectRootRaw = & wsl.exe -d $WslDistro -- wslpath -a $EscapedProjectRoot
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($WslProjectRootRaw)) {
    exit $LASTEXITCODE
}
$WslProjectRoot = $WslProjectRootRaw.Trim()

& wsl.exe -d $WslDistro -- make -C $WslProjectRoot $Target
exit $LASTEXITCODE
