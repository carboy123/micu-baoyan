#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:ProjectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$script:RuntimeDirectory = Join-Path $script:ProjectRoot '.runtime'
$script:HugoExecutable = Join-Path $script:ProjectRoot 'tools\hugo\hugo.exe'
$script:StateFile = Join-Path $script:RuntimeDirectory 'preview.json'
$script:PreviewUrl = 'http://127.0.0.1:1313/'

function Initialize-MicuRuntime {
    if (-not (Test-Path -LiteralPath $script:RuntimeDirectory)) {
        New-Item -ItemType Directory -Path $script:RuntimeDirectory -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $script:HugoExecutable -PathType Leaf)) {
        throw '缺少 tools\hugo\hugo.exe，请恢复完整预览包。'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $script:ProjectRoot 'hugo.toml'))) {
        throw '缺少 hugo.toml，请确认预览包文件完整。'
    }
    $manifest = Get-Content -LiteralPath (Join-Path $script:ProjectRoot 'tools\hugo\runtime.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $actualHash = (Get-FileHash -LiteralPath $script:HugoExecutable -Algorithm SHA256).Hash
    if ($actualHash -ne $manifest.executable_sha256) {
        throw 'Hugo 运行时校验失败，请恢复 tools\hugo 中的原始文件。'
    }
}

function Enter-MicuLock {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { $digest = $hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($script:ProjectRoot.ToLowerInvariant())) }
    finally { $hasher.Dispose() }
    $key = ([BitConverter]::ToString($digest)).Replace('-', '').Substring(0, 24)
    $mutex = New-Object Threading.Mutex($false, ('Local\MicuPreview-' + $key))
    $acquired = $false
    try { $acquired = $mutex.WaitOne(30000) }
    catch [Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) { $mutex.Dispose(); throw '另一个启动或停止操作仍在执行，请稍后重试。' }
    return $mutex
}

function Get-MicuOwnedProcess {
    if (-not (Test-Path -LiteralPath $script:StateFile)) { return $null }
    try {
        $state = Get-Content -LiteralPath $script:StateFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($state.projectRoot -ne $script:ProjectRoot -or $state.executable -ne $script:HugoExecutable) { return $null }
        $candidate = Get-Process -Id ([int]$state.processId) -ErrorAction Stop
        if ($candidate.Path -ne $script:HugoExecutable) { return $null }
        if ($candidate.StartTime.ToUniversalTime().ToString('o') -ne $state.startTimeUtc) { return $null }
        return $candidate
    }
    catch { return $null }
}

function Test-MicuPortOccupied {
    $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    return @($listeners | Where-Object { $_.Port -eq 1313 }).Count -gt 0
}

function Test-MicuReady {
    try {
        $request = [Net.HttpWebRequest]::Create($script:PreviewUrl)
        $request.Proxy = $null
        $request.Timeout = 1000
        $response = $request.GetResponse()
        try { return [int]$response.StatusCode -eq 200 }
        finally { $response.Dispose() }
    }
    catch { return $false }
}

function Save-MicuProcessState([Diagnostics.Process]$Process) {
    [ordered]@{
        projectRoot = $script:ProjectRoot
        executable = $script:HugoExecutable
        processId = $Process.Id
        startTimeUtc = $Process.StartTime.ToUniversalTime().ToString('o')
        url = $script:PreviewUrl
    } | ConvertTo-Json | Set-Content -LiteralPath $script:StateFile -Encoding UTF8
}

function Remove-MicuState {
    if (Test-Path -LiteralPath $script:StateFile) { Remove-Item -LiteralPath $script:StateFile -Force }
}

function Quote-MicuArgument([string]$Value) {
    if ($Value.Contains('"')) { throw '参数不得包含双引号。' }
    return '"' + $Value.TrimEnd('\') + '"'
}
