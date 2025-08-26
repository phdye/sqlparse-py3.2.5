<#  Run-datamgr.ps1
    Purpose: Launch 32-bit datamgr.exe with a clean, app-local ODP.NET (2.122.1.0) and working PATH.
    Usage:
      ./Run-datamgr.ps1
      ./Run-datamgr.ps1 -OracleHome "C:\Oracle\Ora12_32\client" -ExeName "datamgr.exe" -Verbose
#>

[CmdletBinding()]
param(
  [string]$OracleHome = "C:\Oracle\Ora12_32\client",
  [string]$ExeName    = "datamgr.exe",
  [string]$OdpRelative = "odp.net\bin\2.x\Oracle.DataAccess.dll",
  [string]$RequiredOdpVersion = "2.122.1.0",
  [switch]$NoLaunch
)

# --- Helpers -------------------------------------------------------------

function Write-Header($text) { Write-Host ""; Write-Host $text -ForegroundColor Cyan; }
function Is-PE32([string]$Path) {
  try {
    $fs = [System.IO.File]::Open($Path,'Open','Read','ReadWrite')
    $br = New-Object System.IO.BinaryReader($fs)
    if ($br.ReadUInt16() -ne 0x5A4D) { $br.Close(); $fs.Close(); return $false } # 'MZ'
    $fs.Seek(0x3C, 'Begin') | Out-Null
    $lfanew = $br.ReadInt32()
    if ($lfanew -le 0) { $br.Close(); $fs.Close(); return $false }
    $fs.Seek($lfanew, 'Begin') | Out-Null
    if ($br.ReadUInt32() -ne 0x00004550) { $br.Close(); $fs.Close(); return $false } # 'PE\0\0'
    $fs.Seek(20, 'Current') | Out-Null
    $magic = $br.ReadUInt16()
    $br.Close(); $fs.Close()
    return ($magic -eq 0x10B) # PE32 (32-bit)
  } catch { return $false }
}

function Get-FileVersionOrNull([string]$Path) {
  try { (Get-Item $Path).VersionInfo.FileVersion } catch { $null }
}

# --- Resolve key paths ---------------------------------------------------

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = Join-Path $AppDir $ExeName
$OracleBin = Join-Path $OracleHome "bin"
$SourceOdp = Join-Path $OracleHome $OdpRelative
$LocalOdp  = Join-Path $AppDir "Oracle.DataAccess.dll"

# --- Basic validation ----------------------------------------------------

if (!(Test-Path $ExePath)) {
  Write-Error "Executable not found: $ExePath"
  exit 2
}
if (!(Test-Path $OracleBin)) {
  Write-Error "Oracle bin not found: $OracleBin"
  exit 2
}
if (!(Test-Path $SourceOdp)) {
  Write-Error "Managed ODP.NET not found: $SourceOdp"
  exit 2
}

# --- Show environment (before) ------------------------------------------

Write-Header "-- Environment (before) --------------------------------------"
$idx = 0
(($env:PATH) -split ';' | Where-Object { $_ -ne "" }) | ForEach-Object {
  "{0,3}: {1}" -f $idx++, $_
}
"ORACLE_HOME = {0}" -f ($env:ORACLE_HOME ?? "<not set>") | Write-Host
"TNS_ADMIN   = {0}" -f ($env:TNS_ADMIN   ?? "<not set>") | Write-Host
"ORACLE_SID  = {0}" -f ($env:ORACLE_SID  ?? "<not set>") | Write-Host
"NLS_LANG    = {0}" -f ($env:NLS_LANG    ?? "<not set>") | Write-Host

# --- Prepend Oracle bin to PATH for this process ------------------------

Write-Header "-- Updating PATH ---------------------------------------------"
$env:PATH = "$OracleBin;$env:PATH"
"Prepended: $OracleBin" | Write-Host

# --- Verify oci.dll presence & bitness ----------------------------------

Write-Header "-- Native client (oci.dll) -----------------------------------"
$oci = Join-Path $OracleBin "oci.dll"
if (!(Test-Path $oci)) {
  Write-Error "oci.dll NOT found in $OracleBin"
  exit 2
}
$pe32 = Is-PE32 $oci
"oci.dll: $oci  (PE32={0})" -f $pe32 | Write-Host
if (-not $pe32) {
  Write-Error "oci.dll is not 32-bit. Expected PE32."
  exit 2
}

# --- Ensure app-local Oracle.DataAccess.dll is correct -------------------

Write-Header "-- Managed ODP.NET (Oracle.DataAccess.dll) --------------------"
$haveLocal = Test-Path $LocalOdp
$localVer  = if ($haveLocal) { Get-FileVersionOrNull $LocalOdp } else { $null }
"Local ODP at app: $haveLocal  (Version=$localVer)" | Write-Host

$srcVer = Get-FileVersionOrNull $SourceOdp
"Source ODP in ORACLE_HOME: $SourceOdp  (Version=$srcVer)" | Write-Host

$needsCopy = $true
if ($haveLocal -and $localVer -eq $RequiredOdpVersion) { $needsCopy = $false }

if ($needsCopy) {
  "Copying Oracle.DataAccess.dll -> app folder..." | Write-Host
  try {
    Copy-Item -LiteralPath $SourceOdp -Destination $LocalOdp -Force
    $localVer = Get-FileVersionOrNull $LocalOdp
    "Local after copy: Version=$localVer" | Write-Host
  } catch {
    Write-Error "Failed to copy Oracle.DataAccess.dll: $($_.Exception.Message)"
    exit 2
  }
}

if ($localVer -ne $RequiredOdpVersion) {
  Write-Warning ("Local Oracle.DataAccess.dll version is {0}, expected {1}. Continuing, but you may see issues." -f ($localVer ?? "<unknown>"), $RequiredOdpVersion)
}

# --- Optional: echo minimal config guidance -----------------------------

Write-Header "-- Config sanity (informational) ------------------------------"
"Expecting datamgr.exe.config alongside $ExeName with:" | Write-Host
'  <bindingRedirect oldVersion="0.0.0.0-2.122.1.0" newVersion="2.122.1.0" />' | Write-Host
'  <DbProviderFactories> entry with Version=2.122.1.0' | Write-Host
'  (No <codeBase> needed since DLL is local)' | Write-Host

# --- Show environment (after) -------------------------------------------

Write-Header "-- Environment (after) ---------------------------------------"
$idx = 0
(($env:PATH) -split ';' | Where-Object { $_ -ne "" }) | ForEach-Object {
  "{0,3}: {1}" -f $idx++, $_
}

# --- Launch --------------------------------------------------------------

if ($NoLaunch) {
  Write-Header "-- NoLaunch specified; not starting the EXE ------------------"
  exit 0
}

Write-Header "-- Starting application --------------------------------------"
try {
  Start-Process -FilePath $ExePath | Out-Null
  "Launched: $ExePath" | Write-Host
  exit 0
} catch {
  Write-Error "Failed to start $ExePath : $($_.Exception.Message)"
  exit 1
}
