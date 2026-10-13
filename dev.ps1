[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('setup', 'build', 'dev', 'sync', 'test', 'release', 'package', 'icons')]
    [string]$Command = 'dev',
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [switch]$NoOpen,
    [switch]$Reinstall
)

$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv/Scripts/python.exe'
$interactiveRoot = Join-Path $repoRoot 'interactive'

function Invoke-Tool {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Befehl fehlgeschlagen (Exit $LASTEXITCODE): $Executable $($Arguments -join ' ')" }
}

function Initialize-Repo {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host '[dev] Erstelle .venv'
        $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($launcher) { Invoke-Tool $launcher.Source @('-3', '-m', 'venv', (Join-Path $repoRoot '.venv')) }
        else {
            $launcher = Get-Command python.exe -ErrorAction Stop
            Invoke-Tool $launcher.Source @('-m', 'venv', (Join-Path $repoRoot '.venv'))
        }
    }
    $dependencyHash = (Get-FileHash -LiteralPath (Join-Path $repoRoot 'pyproject.toml') -Algorithm SHA256).Hash
    $pythonStamp = Join-Path $repoRoot '.venv/.gil-dependencies-sha256'
    $installedHash = if (Test-Path -LiteralPath $pythonStamp) { (Get-Content -Raw -LiteralPath $pythonStamp).Trim() } else { '' }
    if ($Reinstall -or $installedHash -ne $dependencyHash) {
        Write-Host '[dev] Installiere Python-Abhaengigkeiten (Pipeline, lokales ASR, Tests)'
        Invoke-Tool $venvPython @('-m', 'pip', 'install', '-e', '.[pipeline,audio,dev]')
        Set-Content -LiteralPath $pythonStamp -Value $dependencyHash -Encoding ASCII
    }
    $node = Get-Command node.exe -ErrorAction Stop
    $nodeVersion = & $node.Source --version
    if ([int]($nodeVersion.TrimStart('v').Split('.')[0]) -lt 22) { throw 'Bitte Node.js 22 oder neuer installieren.' }
    $npm = Get-Command npm.cmd -ErrorAction Stop
    $lockHash = (Get-FileHash -LiteralPath (Join-Path $interactiveRoot 'package-lock.json') -Algorithm SHA256).Hash
    $nodeStamp = Join-Path $interactiveRoot 'node_modules/.gil-lock-sha256'
    $installedLock = if (Test-Path -LiteralPath $nodeStamp) { (Get-Content -Raw -LiteralPath $nodeStamp).Trim() } else { '' }
    if ($Reinstall -or $installedLock -ne $lockHash) {
        Write-Host '[dev] Installiere node_modules aus package-lock.json'
        Invoke-Tool $npm.Source @('ci', '--prefix', $interactiveRoot, '--ignore-scripts', '--no-audit', '--no-fund')
        Set-Content -LiteralPath $nodeStamp -Value $lockHash -Encoding ASCII
    }
    Write-Host '[dev] Einrichtung bereit'
}

function Invoke-Pipeline {
    param([string]$Stage)
    Invoke-Tool $venvPython @('-m', 'pipeline', $Stage)
}

Push-Location -LiteralPath $repoRoot
try {
    Initialize-Repo
    switch ($Command) {
        'setup' { }
        'build' { Invoke-Pipeline 'audio-reader' }
        'sync' { Invoke-Pipeline 'audio-reader' }
        'package' { Invoke-Pipeline 'audio-reader'; Invoke-Pipeline 'package-reader' }
        'icons' { Invoke-Pipeline 'figure-icons'; Invoke-Pipeline 'exercises'; Invoke-Pipeline 'audio-reader' }
        'test' {
            Invoke-Tool $venvPython @('-m', 'pytest')
            Invoke-Tool 'node.exe' @('--check', 'interactive/reader-app.mjs')
            Invoke-Tool 'node.exe' @('--check', 'interactive/reader-navigation.mjs')
            Invoke-Tool 'node.exe' @('--check', 'interactive/reader-service-worker.mjs')
            Invoke-Tool 'node.exe' @('--check', 'interactive/reader-singlefile-boot.mjs')
            Invoke-Tool 'node.exe' @('--test', 'interactive/reader-timeline.test.mjs')
            Invoke-Pipeline 'offline'
        }
        'release' {
            Invoke-Pipeline 'audio-reader'
            Invoke-Pipeline 'package-reader'
            Invoke-Pipeline 'export-notebooklm'
            Invoke-Pipeline 'anki'
            Invoke-Pipeline 'release'  # builds local archives; does not publish or merge
        }
        'dev' {
            Invoke-Pipeline 'audio-reader'
            Write-Host '[dev] Starte Reader'
            $readerArgs = @('-m', 'pipeline.reader_serve', '--directory', (Join-Path $repoRoot 'build/interactive'), '--port', "$Port")
            if (-not $NoOpen) { $readerArgs += '--open' }
            Invoke-Tool $venvPython $readerArgs
        }
    }
}
finally { Pop-Location }
