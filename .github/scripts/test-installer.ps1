param(
    [Parameter(Mandatory)][string]$PreviousInstaller,
    [Parameter(Mandatory)][string]$CandidateInstaller,
    [Parameter(Mandatory)][string]$ExpectedVersion
)

$ErrorActionPreference = 'Stop'
if (-not $IsWindows -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:RUNNER_OS -ne 'Windows' -or
    -not $env:RUNNER_TEMP) {
    throw 'Installer acceptance requires a disposable GitHub-hosted Windows runner and pwsh.'
}

$PreviousInstaller = (Get-Item -LiteralPath $PreviousInstaller).FullName
$CandidateInstaller = (Get-Item -LiteralPath $CandidateInstaller).FullName
$sandbox = Join-Path $env:RUNNER_TEMP "installer-acceptance-$([guid]::NewGuid())"
$installDir = Join-Path $sandbox 'Installed App'
$application = Join-Path $installDir 'HopeCasement.exe'
$uninstaller = Join-Path $installDir 'unins000.exe'
$productKey = 'HKCU:\Software\HopeCasement'
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{2FB42E98-50ED-4FEE-8024-3B20F66DFF40}_is1'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$taskPath = '\HopeCasement\'
$taskNames = @('ChangeAtTime', 'ChangeOnInterval')

function Get-LoginCommand {
    if (Test-Path -LiteralPath $runKey) {
        (Get-Item -LiteralPath $runKey).GetValue('HopeCasement')
    }
}

function Get-AppTasks {
    Get-ScheduledTask | Where-Object { $_.TaskPath -eq $taskPath -and $_.TaskName -in $taskNames }
}

function Assert-Uninstalled {
    foreach ($path in @($installDir, $productKey, $uninstallKey)) {
        if (Test-Path -LiteralPath $path) { throw "Unexpected installed state at $path" }
    }
    if (($null -ne (Get-LoginCommand)) -or (Get-AppTasks)) {
        throw 'The login entry or a scheduled task is present.'
    }
}

function Invoke-Inno([string]$File, [string]$Phase, [string[]]$Options = @()) {
    $log = Join-Path $sandbox "$Phase.log"
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=`"$log`"") + $Options
    Write-Host "$Phase ($log)"
    $process = Start-Process -FilePath $File -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log -Tail 35 | Out-Host }
        throw "$Phase exited with code $($process.ExitCode)."
    }
}

function Install-App([string]$File, [string]$Phase, [string]$Version, [string]$Language) {
    $options = @("/DIR=`"$installDir`"", "/LANG=$Language", '/MERGETASKS="!desktopicon"')
    Invoke-Inno $File $Phase $options
    foreach ($path in @($application, $uninstaller)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing $path after $Phase" }
    }
    $installedVersion = Get-ItemPropertyValue -LiteralPath $uninstallKey -Name DisplayVersion
    if ($installedVersion -ne $Version) { throw "$Phase installed $installedVersion, expected $Version." }
    $expectedLanguage = @{ english = 'en'; chinesesimplified = 'zh' }[$Language]
    if ((Get-ItemPropertyValue -LiteralPath $productKey -Name Language) -ne $expectedLanguage) {
        throw "$Phase did not register the selected language $Language."
    }
}

New-Item -ItemType Directory -Path $sandbox | Out-Null
Assert-Uninstalled
Install-App $CandidateInstaller 'clean-install' $ExpectedVersion 'chinesesimplified'
$candidateHash = (Get-FileHash -LiteralPath $application).Hash
Invoke-Inno $uninstaller 'clean-uninstall'
Assert-Uninstalled

Install-App $PreviousInstaller 'install-v0.1.0' '0.1.0' 'english'
$images = Join-Path $sandbox 'Personal Images'
$backup = Join-Path $sandbox 'Backup'
foreach ($path in @($images, $backup, "$installDir\backgrounds", "$installDir\history")) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}
$config = @{
    images_dir = $images
    background_colors = @('#334455')
    schedule_modes = @('startup', 'interval', 'daily')
    save_history = $true
}
$config | ConvertTo-Json | Set-Content -LiteralPath "$installDir\config.json" -Encoding utf8
Set-Content -LiteralPath "$installDir\quotes.txt" -Value '来日可期', 'One more day.' -Encoding utf8
Set-Content -LiteralPath "$installDir\state.json" -Value '{}'
Set-Content -LiteralPath "$installDir\error.log" -Value 'previous diagnostic'
$png = [Convert]::FromBase64String('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGM0dgllYGBgYgADAAmYANCZH37rAAAAAElFTkSuQmCC')
$externalImage = Join-Path $images 'personal.png'
foreach ($path in @($externalImage, "$installDir\backgrounds\picture.png", "$installDir\history\previous.png", "$installDir\current_wallpaper.png")) {
    [IO.File]::WriteAllBytes($path, $png)
}

# Keep the backup outside the install directory, as described in the user guide.
$data = @('config.json', 'quotes.txt', 'state.json', 'error.log', 'backgrounds', 'history', 'current_wallpaper.png')
$installedHashes = @{}
foreach ($name in $data) {
    $source = Join-Path $installDir $name
    Copy-Item -LiteralPath $source -Destination $backup -Recurse
    foreach ($file in (Get-ChildItem -LiteralPath $source -File -Recurse)) {
        $relative = [IO.Path]::GetRelativePath($installDir, $file.FullName)
        $installedHashes[$relative] = (Get-FileHash -LiteralPath $file.FullName).Hash
    }
}
$imageHash = (Get-FileHash -LiteralPath $externalImage).Hash

# Match the production login command. The two tasks have no triggers and are disabled.
$loginCommand = '"{0}" --change' -f $application
if (-not (Test-Path -LiteralPath $runKey)) { New-Item -Path $runKey | Out-Null }
New-ItemProperty -LiteralPath $runKey -Name HopeCasement -Value $loginCommand -PropertyType String | Out-Null
$scheduler = New-Object -ComObject Schedule.Service
$scheduler.Connect()
$taskRoot = $scheduler.GetFolder('\')
if (-not ($taskRoot.GetFolders(0) | Where-Object Name -eq 'HopeCasement')) {
    $null = $taskRoot.CreateFolder('HopeCasement')
}
$action = New-ScheduledTaskAction -Execute $application -Argument '--change'
$settings = New-ScheduledTaskSettingsSet -Disable
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
foreach ($name in $taskNames) {
    Register-ScheduledTask -TaskPath $taskPath -TaskName $name -Action $action -Settings $settings -Principal $principal | Out-Null
}

Install-App $CandidateInstaller 'upgrade' $ExpectedVersion 'english'
if ((Get-FileHash -LiteralPath $application).Hash -ne $candidateHash) {
    throw 'The upgraded executable differs from the cleanly installed candidate.'
}
foreach ($relative in $installedHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $installDir $relative)).Hash -ne $installedHashes[$relative]) {
        throw "Upgrade changed $relative."
    }
}
if ((Get-LoginCommand) -cne $loginCommand) { throw 'Upgrade changed the login command.' }
$tasks = @(Get-AppTasks)
if ($tasks.Count -ne $taskNames.Count) { throw 'Upgrade removed a scheduled task.' }
foreach ($task in $tasks) {
    if ($task.State -ne 'Disabled' -or $task.Actions.Execute -ne $application -or $task.Actions.Arguments -ne '--change') {
        throw "Upgrade changed the registration of $($task.TaskName)."
    }
}

Invoke-Inno $uninstaller 'upgraded-uninstall'
Assert-Uninstalled
foreach ($relative in $installedHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $backup $relative)).Hash -ne $installedHashes[$relative]) {
        throw "Uninstall changed the backup of $relative."
    }
}
if ((Get-FileHash -LiteralPath $externalImage).Hash -ne $imageHash) { throw 'Uninstall changed the external image.' }
Write-Host "Installer acceptance passed for v0.1.0 -> $ExpectedVersion."
