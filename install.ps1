$ErrorActionPreference = "Stop"

$repo = "tusmo-official/Tusmo"
$asset = "tusmo-windows-x86_64.tar.gz"
$tusmoHome = "$env:LOCALAPPDATA\Tusmo"
$temp = New-TemporaryFile
Remove-Item $temp
New-Item -ItemType Directory -Force -Path $temp | Out-Null

Write-Host "Downloading $asset..."
Invoke-WebRequest -Uri "https://github.com/$repo/releases/latest/download/$asset" -OutFile "$temp\$asset"

tar -xf "$temp\$asset" -C $temp
Remove-Item -Recurse -Force "$tusmoHome" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $tusmoHome | Out-Null
Move-Item "$temp\*" $tusmoHome
Remove-Item -Recurse -Force $temp

$binPath = "$tusmoHome\bin"
if (-not ($env:Path -split ';' | Where-Object { $_ -eq $binPath })) {
  [Environment]::SetEnvironmentVariable("Path", "$binPath;$env:Path", "User")
}

[Environment]::SetEnvironmentVariable("TUSMO_HOME", $tusmoHome, "User")
[Environment]::SetEnvironmentVariable("TUSMO_CC", "$tusmoHome\toolchain\cc.bat", "User")
[Environment]::SetEnvironmentVariable("TUSMO_LIB_DIR", "$tusmoHome\lib", "User")
[Environment]::SetEnvironmentVariable("TUSMO_INCLUDE_DIR", "$tusmoHome\runtime", "User")

Write-Host "Installed to $tusmoHome. Open a new shell and run 'tusmo'."
