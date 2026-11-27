#Requires -Version 7.0
param(
    # Optional offline directory containing the two pinned upstream files.
    [string]$InputDirectory
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'dist/HopeCasement.exe') -PathType Leaf)) {
    throw 'Build dist/HopeCasement.exe with HopeCasement.spec before building the installer.'
}

$tempRoot = (Resolve-Path ([IO.Path]::GetTempPath())).Path
$workName = "hope-inno-build-$([guid]::NewGuid().ToString('N'))"
$workDir = Join-Path $tempRoot $workName

function Get-BuildInput([string]$Name, [string]$Url, [string]$Sha256) {
    $file = Join-Path $workDir $Name
    if ($InputDirectory) {
        Copy-Item -LiteralPath (Join-Path $InputDirectory $Name) -Destination $file
    } else {
        Invoke-WebRequest -Uri $Url -OutFile $file -MaximumRetryCount 2 -RetryIntervalSec 2 -TimeoutSec 180
    }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $Sha256) {
        throw "SHA-256 mismatch for $Name."
    }
    return $file
}

$null = New-Item -Path $workDir -ItemType Directory
try {
    $upstream = 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3'
    $sources = 'https://raw.githubusercontent.com/jrsoftware/issrc/is-6_7_3/Files/Languages/Unofficial'
    $installer = Get-BuildInput 'innosetup-6.7.3.exe' "$upstream/innosetup-6.7.3.exe" '9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732'
    $translation = Get-BuildInput 'ChineseSimplified.isl' "$sources/ChineseSimplified.isl" '7d544b9bb1d142cfa11f2e5d3cc8abe2e55f8e066c5124e3772675aa236e1278'

    $compilerDir = Join-Path $workDir 'compiler'
    $arguments = @('/PORTABLE=1', '/CURRENTUSER', '/VERYSILENT', '/SP-', '/SUPPRESSMSGBOXES', '/NORESTART', "/DIR=`"$compilerDir`"")
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) {
        throw "Portable Inno Setup extraction failed with exit code $($process.ExitCode)."
    }
    Copy-Item -LiteralPath $translation -Destination (Join-Path $compilerDir 'Languages/ChineseSimplified.isl')
    & (Join-Path $compilerDir 'ISCC.exe') (Join-Path $repoRoot 'setup/Hopecasement.iss')
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
    }
} finally {
    $resolved = (Resolve-Path -LiteralPath $workDir).Path
    if ([IO.Path]::GetFileName($resolved) -eq $workName -and [IO.Path]::GetDirectoryName($resolved) -eq [IO.Path]::TrimEndingDirectorySeparator($tempRoot)) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
