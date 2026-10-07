<#
  Set up this PC for The Fourth Sheet. Safe to run again any time.

  Easiest: double-click "Set up this PC.cmd" in OneDrive (Projects\The 4th Sheet).
  Or in PowerShell:  powershell -ExecutionPolicy Bypass -File "Set up this PC.ps1"

  What it does, in order (anything already done is skipped):
    1. checks OneDrive has the project folder (Projects\The 4th Sheet)
    2. installs Python 3.12, Git and Google Chrome if they're missing (winget)
    3. downloads the website project to %USERPROFILE%\thefourthsheet (or updates it if it's already there)
    4. switches on Python's UTF-8 mode for good
    5. runs tools\setup_machine.py: Python packages, Azure command line, git leak guard, OneDrive media sync
       (Azure sign-in is left for later unless you add -Azure: wait until the business Microsoft 365 account exists)
    6. checks it works: lists the reports, then tests every page in a real browser
    7. puts "Preview The Fourth Sheet" on the desktop and opens the site
  A log is kept at %USERPROFILE%\fourthsheet-setup.log. If anything fails, send that file.
#>
param(
    [string]$Folder = "$env:USERPROFILE\thefourthsheet",
    [switch]$Azure,
    [switch]$SkipSiteCheck
)

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/nnbooth/thefourthsheet.git"
$Log = "$env:USERPROFILE\fourthsheet-setup.log"
Start-Transcript -Path $Log -Append | Out-Null

function Say($m)  { Write-Host ""; Write-Host "== $m" -ForegroundColor Green }
function Ok($m)   { Write-Host "   ok  $m" -ForegroundColor Gray }
function Warn($m) { Write-Host "   !!  $m" -ForegroundColor Yellow }
function Has($c)  { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Install($id, $name) {
    if (-not (Has "winget")) {
        throw "winget (the Windows package installer) isn't available. Install 'App Installer' from the Microsoft Store, then run this again."
    }
    Write-Host "   installing $name (a window may ask for permission) ..."
    winget install -e --id $id --accept-package-agreements --accept-source-agreements --silent | Out-Host
    Refresh-Path
}

try {
    Write-Host "Setting up $env:COMPUTERNAME for The Fourth Sheet" -ForegroundColor Cyan

    # 1. OneDrive ---------------------------------------------------------------------------------
    Say "1. OneDrive"
    $bases = @($env:OneDriveConsumer, $env:OneDriveCommercial, $env:OneDrive) + @(Get-ChildItem $env:USERPROFILE -Directory -Filter "OneDrive*" -ErrorAction SilentlyContinue | ForEach-Object FullName)
    $project = $bases | Where-Object { $_ -and (Test-Path (Join-Path $_ "Projects\The 4th Sheet")) } | Select-Object -First 1
    if (-not $project) {
        throw "Can't find 'Projects\The 4th Sheet' in OneDrive. Open OneDrive, sign in with your Microsoft account, let the folder sync, then run this again."
    }
    $project = Join-Path $project "Projects\The 4th Sheet"
    Ok "project folder: $project"
    foreach ($sub in "Data", "Data documentation", "Business", "Media\site media") {
        if (Test-Path (Join-Path $project $sub)) { Ok $sub } else { Warn "$sub not synced yet (it will be fetched when needed)" }
    }

    # 2. Python, Git, Chrome ------------------------------------------------------------------------
    Say "2. Python, Git and Chrome"
    $hasPython = (Has "py") -and ((& py -3 --version 2>$null) -match "Python 3\.(1[0-9])")
    if (-not $hasPython) { Install "Python.Python.3.12" "Python 3.12" }
    if (-not ((& py -3 --version 2>$null) -match "Python 3")) {
        throw "Python didn't install properly. Install Python 3.12 from python.org (tick 'Add python.exe to PATH'), then run this again."
    }
    Ok (& py -3 --version)
    if (-not (Has "git")) { Install "Git.Git" "Git" }
    if (-not (Has "git")) { throw "Git didn't install properly. Install it from git-scm.com, then run this again." }
    Ok (& git --version)
    $chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $chrome) {
        try { Install "Google.Chrome" "Google Chrome" } catch { Warn "Chrome didn't install; the PDFs will use Playwright's own browser instead" }
    } else { Ok "Google Chrome" }

    # 3. The project ----------------------------------------------------------------------------------
    Say "3. The website project"
    if ($Folder -like "*OneDrive*") { Warn "The project shouldn't live inside OneDrive (git and OneDrive fight over files). Using $env:USERPROFILE\thefourthsheet instead."; $Folder = "$env:USERPROFILE\thefourthsheet" }
    if (Test-Path (Join-Path $Folder ".git")) {
        git -C $Folder checkout -q main
        git -C $Folder pull -q --ff-only origin main
        Ok "updated: $Folder"
    } else {
        git clone -q $Repo $Folder
        Ok "downloaded to $Folder"
    }
    git -C $Folder config user.name "Nathan Booth"
    Ok ("version: " + (git -C $Folder log -1 --format="%h %ad %s" --date=short))

    # 4. UTF-8 ----------------------------------------------------------------------------------------
    Say "4. Python UTF-8 mode"
    if ([Environment]::GetEnvironmentVariable("PYTHONUTF8", "User") -ne "1") { [Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User") }
    $env:PYTHONUTF8 = "1"
    Ok "on (the tools write characters like the cent sign and arrows)"

    # 5. The project's own setup -----------------------------------------------------------------------
    Say "5. Packages, Azure command line, git leak guard, media"
    Push-Location $Folder
    if ($Azure) { py tools\setup_machine.py } else { py tools\setup_machine.py --no-azure }
    if ($LASTEXITCODE -ne 0) { throw "tools\setup_machine.py reported a problem (see above)." }

    # 6. Check it works --------------------------------------------------------------------------------
    Say "6. Checking it works"
    py tools\report.py --list
    if ($LASTEXITCODE -ne 0) { throw "The report builder didn't run (see above)." }
    if (-not $SkipSiteCheck) {
        Write-Host "   testing every page and report in a real browser (a few minutes) ..."
        py tools\tests\site_check.py
        if ($LASTEXITCODE -ne 0) { Warn "The site check found problems (listed above). Everything else is set up; send me the log." }
    }
    Pop-Location

    # 7. Desktop shortcut and preview ------------------------------------------------------------------
    Say "7. Desktop shortcut"
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcut = Join-Path $desktop "Preview The Fourth Sheet.cmd"
    $lines = @("@echo off", "rem Starts the local preview of the website and opens it. Close this window to stop it.",
               "cd /d `"$Folder`"", "start `"`" http://127.0.0.1:8765/", "py tools\serve.py")
    Set-Content -Path $shortcut -Value $lines -Encoding ASCII
    Ok "double-click 'Preview The Fourth Sheet' on the desktop any time"
    Start-Process -FilePath $shortcut

    Say "Done. This PC is ready."
    Write-Host "   Project:   $Folder"
    Write-Host "   Data:      $project"
    Write-Host "   Next:      the checklist in OneDrive, Business\Microsoft 365, Azure and Fabric plan.md"
    Write-Host "   Everyday:  cd $Folder   then   py tools\sample_data.py  /  py tools\report.py --list"
    Write-Host "   Before you start work each day:  git -C $Folder pull"
    if (-not $Azure) { Write-Host "   Azure:     once the business Microsoft 365 account exists, run this again with -Azure (or: az login)" }
}
catch {
    Write-Host ""
    Write-Host "STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Nothing is broken: fix that one thing and run this again (it skips whatever is already done)."
    Write-Host "The full log is $Log"
    Stop-Transcript | Out-Null
    exit 1
}
Stop-Transcript | Out-Null
