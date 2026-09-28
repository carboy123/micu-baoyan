#requires -Version 5.1
[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'runtime-common.ps1')
$lock = $null
$result = 0
try {
    $lock = Enter-MicuLock
    $owned = Get-MicuOwnedProcess
    if ($null -eq $owned) {
        Remove-MicuState
        Write-Host '当前没有可确认属于本项目的预览进程；未停止任何其他程序。'
    }
    else {
        Stop-Process -Id $owned.Id -ErrorAction Stop
        if (-not $owned.WaitForExit(5000)) { throw '等待预览进程结束超时；运行记录已保留，请稍后重试。' }
        Remove-MicuState
        Write-Host '米醋保研指南本机预览已停止。'
    }
}
catch {
    $result = 1
    Write-Host ('停止失败：' + $_.Exception.Message) -ForegroundColor Red
}
finally {
    if ($null -ne $lock) { $lock.ReleaseMutex(); $lock.Dispose() }
}
exit $result
