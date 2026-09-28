#requires -Version 5.1
[CmdletBinding()]
param([switch]$NoBrowser)
. (Join-Path $PSScriptRoot 'runtime-common.ps1')
$lock = $null
$launched = $false
$result = 0
try {
    Initialize-MicuRuntime
    $lock = Enter-MicuLock
    $owned = Get-MicuOwnedProcess
    if ($null -ne $owned) {
        if (-not (Test-MicuReady)) {
            throw '本项目预览进程仍在运行，但页面暂不可用。请查看 .runtime\preview-error.log；可先停止后重试。'
        }
        Write-Host ('预览已在运行：' + $script:PreviewUrl)
    }
    else {
        Remove-MicuState
        if (Test-MicuPortOccupied) {
            throw '端口 1313 已被其他进程占用。请自行关闭占用程序后重试；本脚本不会结束无关进程。'
        }
        $arguments = @(
            'server', '--source', (Quote-MicuArgument $script:ProjectRoot),
            '--bind', '127.0.0.1', '--port', '1313', '--baseURL', $script:PreviewUrl,
            '--buildDrafts', '--environment', 'development', '--renderToMemory',
            '--disableFastRender', '--noHTTPCache', '--logLevel', 'info',
            '--cacheDir', (Quote-MicuArgument (Join-Path $script:RuntimeDirectory 'cache'))
        )
        $owned = Start-Process -FilePath $script:HugoExecutable -ArgumentList $arguments -WorkingDirectory $script:ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $script:RuntimeDirectory 'preview.log') -RedirectStandardError (Join-Path $script:RuntimeDirectory 'preview-error.log')
        $launched = $true
        Save-MicuProcessState $owned
        $ready = $false
        $deadline = [DateTime]::UtcNow.AddSeconds(45)
        while ([DateTime]::UtcNow -lt $deadline) {
            $owned.Refresh()
            if ($owned.HasExited) { throw 'Hugo 已在页面就绪前退出，请查看 preview.log 和 preview-error.log。' }
            if (Test-MicuReady) { $ready = $true; break }
            Start-Sleep -Milliseconds 250
        }
        if (-not $ready) { throw '等待预览就绪超时。' }
        Write-Host ('米醋保研指南已启动：' + $script:PreviewUrl)
        Write-Host '预览仅允许本机访问。关闭浏览器不会停止预览，请使用“停止预览.cmd”。'
    }
    if (-not $NoBrowser) { Start-Process $script:PreviewUrl | Out-Null }
}
catch {
    $result = 1
    Write-Host ('启动失败：' + $_.Exception.Message) -ForegroundColor Red
    Write-Host ('日志目录：' + $script:RuntimeDirectory)
    if ($launched) {
        $failed = Get-MicuOwnedProcess
        if ($null -ne $failed) { Stop-Process -Id $failed.Id -ErrorAction SilentlyContinue }
        Remove-MicuState
    }
}
finally {
    if ($null -ne $lock) { $lock.ReleaseMutex(); $lock.Dispose() }
}
exit $result
