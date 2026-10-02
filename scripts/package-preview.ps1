#requires -Version 5.1
[CmdletBinding()]
param([switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$packageRoot = '米醋保研指南'
$packageName = '米醋保研指南-v0.4.0.zip'
$temporaryPath = $null

# Only these source trees and individual root files can enter the archive.
$directoryAllowlist = @(
    '.github', 'archetypes', 'content', 'data', 'dev', 'docs', 'layouts',
    'scripts', 'static', 'tests', 'themes\hugo-book', 'tools\hugo'
)
$fileAllowlist = @(
    'README.md', 'AGENTS.md', 'CONTRIBUTING.md', 'hugo.toml', 'DEPENDENCIES.json',
    'THIRD_PARTY_LICENSES.md', '.gitignore', '.gitattributes',
    '启动预览.cmd', '停止预览.cmd', '构建网站.cmd'
)
$requiredFiles = @(
    'README.md', 'hugo.toml', 'DEPENDENCIES.json', 'THIRD_PARTY_LICENSES.md',
    '启动预览.cmd', '停止预览.cmd', '构建网站.cmd', 'content\_index.md',
    'layouts\baseof.html', 'layouts\home.html',
    'scripts\runtime-common.ps1', 'scripts\start-preview.ps1',
    'scripts\stop-preview.ps1', 'scripts\build-site.ps1', 'scripts\package-preview.ps1',
    'docs\runtime.md', 'docs\runtime-validation.md',
    'static\css\site.css', 'static\js\core.js', 'static\js\site.js',
    'static\images\micu-symbol.png', 'static\images\micu-logo.png',
    'static\fonts\SourceHanSansCN-Regular.otf', 'static\fonts\SourceHanSerifCN-Regular.otf',
    'static\fonts\source-han-sans-LICENSE.txt', 'static\fonts\source-han-serif-LICENSE.txt',
    'tools\hugo\hugo.exe', 'tools\hugo\runtime.json', 'tools\hugo\LICENSE', 'tools\hugo\checksums.txt',
    'themes\hugo-book\theme.toml', 'themes\hugo-book\hugo.toml', 'themes\hugo-book\LICENSE'
)
$excludedSegments = @('.git', '.runtime', 'public', 'dist', '__pycache__', 'node_modules', '.cache', '.test-output', '.test-workspaces', '工作室logo', '参考资料')

function Test-PackageExcluded([string]$RelativePath) {
    foreach ($segment in ($RelativePath -split '\\')) {
        if ($excludedSegments -contains $segment) { return $true }
    }
    $leaf = Split-Path -Leaf $RelativePath
    return $leaf -eq '.hugo_build.lock' -or $leaf -match '\.(pyc|pyo|tmp|part|log|zip)$' -or $RelativePath -match '(^|\\)resources\\_gen(\\|$)'
}

function Add-PackageFile([IO.FileInfo]$File, $Entries) {
    if (($File.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw ('不打包符号链接或重解析点：' + $File.FullName)
    }
    $prefix = $projectRoot + '\'
    if (-not $File.FullName.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw ('打包文件超出项目目录：' + $File.FullName)
    }
    $relative = $File.FullName.Substring($prefix.Length)
    if (-not (Test-PackageExcluded $relative)) { $Entries.Add($relative, $File.FullName) }
}

function Add-PackageDirectory([string]$Directory, $Entries) {
    $item = Get-Item -LiteralPath $Directory -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw ('不遍历符号链接或目录联接：' + $Directory)
    }
    foreach ($child in Get-ChildItem -LiteralPath $Directory -Force) {
        $relative = $child.FullName.Substring($projectRoot.Length + 1)
        if (Test-PackageExcluded $relative) { continue }
        if ($child.PSIsContainer) { Add-PackageDirectory $child.FullName $Entries }
        else { Add-PackageFile $child $Entries }
    }
}

try {
    $missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $projectRoot $_) -PathType Leaf) })
    if ($missing.Count -gt 0) { throw ('必需文件缺失，未生成归档：' + [Environment]::NewLine + ($missing -join [Environment]::NewLine)) }
    $runtime = Get-Content -LiteralPath (Join-Path $projectRoot 'tools\hugo\runtime.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ((Get-FileHash -LiteralPath (Join-Path $projectRoot 'tools\hugo\hugo.exe') -Algorithm SHA256).Hash -ne $runtime.executable_sha256) {
        throw 'Hugo 运行时 SHA-256 与版本清单不一致，未生成归档。'
    }
    $dependencies = Get-Content -LiteralPath (Join-Path $projectRoot 'DEPENDENCIES.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($dependency in $dependencies) {
        $path = Join-Path $projectRoot $dependency.path
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $dependency.sha256) {
                throw ('依赖文件 SHA-256 不匹配：' + $dependency.path)
            }
        }
        elseif (-not (Test-Path -LiteralPath $path -PathType Container)) { throw ('清单中的依赖不存在：' + $dependency.path) }
    }
    $entries = New-Object 'System.Collections.Generic.SortedDictionary[string,string]' ([StringComparer]::Ordinal)
    foreach ($relative in $fileAllowlist) {
        $path = Join-Path $projectRoot $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) { Add-PackageFile (Get-Item -LiteralPath $path -Force) $entries }
    }
    foreach ($relative in $directoryAllowlist) {
        $path = Join-Path $projectRoot $relative
        if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw ('打包源目录不存在：' + $relative) }
        Add-PackageDirectory $path $entries
    }
    foreach ($required in $requiredFiles) {
        if (-not $entries.ContainsKey($required)) { throw ('必需文件不在打包白名单结果中：' + $required) }
    }
    $totalBytes = 0L
    foreach ($path in $entries.Values) { $totalBytes += (Get-Item -LiteralPath $path).Length }
    Write-Host ('依赖与文件清单验证通过：' + $entries.Count + ' 个文件，约 ' + [Math]::Round($totalBytes / 1MB, 2) + ' MiB。')
    if ($ValidateOnly) {
        Write-Host '仅验证，未创建或修改归档。'
        exit 0
    }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $destination = Join-Path $projectRoot 'dist'
    if (Test-Path -LiteralPath $destination) {
        if (((Get-Item -LiteralPath $destination -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'dist 不能是符号链接或目录联接。'
        }
    }
    else { New-Item -ItemType Directory -Path $destination | Out-Null }
    $finalPath = Join-Path $destination $packageName
    $temporaryPath = Join-Path $destination ('.preview-' + [Guid]::NewGuid().ToString('N') + '.part')
    $stream = [IO.File]::Open($temporaryPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try {
        $archive = New-Object IO.Compression.ZipArchive($stream, [IO.Compression.ZipArchiveMode]::Create, $true, [Text.Encoding]::UTF8)
        try {
            foreach ($entry in $entries.GetEnumerator()) {
                $entryName = $packageRoot + '/' + $entry.Key.Replace('\', '/')
                [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $entry.Value, $entryName, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
            }
        }
        finally { $archive.Dispose() }
    }
    finally { $stream.Dispose() }
    $archive = [IO.Compression.ZipFile]::OpenRead($temporaryPath)
    try {
        if ($archive.Entries.Count -ne $entries.Count) { throw '生成的归档文件数量与白名单不一致。' }
        foreach ($entry in $archive.Entries) {
            if (-not $entry.FullName.StartsWith($packageRoot + '/', [StringComparison]::Ordinal)) { throw '归档中出现非预期顶层路径。' }
            $relative = $entry.FullName.Substring($packageRoot.Length + 1).Replace('/', '\')
            if (-not $entries.ContainsKey($relative) -or (Test-PackageExcluded $relative)) { throw ('归档出现非白名单文件：' + $relative) }
        }
    }
    finally { $archive.Dispose() }
    if (Test-Path -LiteralPath $finalPath) { [IO.File]::Replace($temporaryPath, $finalPath, $null) }
    else { [IO.File]::Move($temporaryPath, $finalPath) }
    $temporaryPath = $null
    $hash = (Get-FileHash -LiteralPath $finalPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText(($finalPath + '.sha256'), ($hash + '  ' + $packageName + [Environment]::NewLine), (New-Object Text.UTF8Encoding($false)))
    Write-Host ('本机预览包：' + $finalPath)
    Write-Host ('SHA-256：' + $hash)
    exit 0
}
catch {
    Write-Host ('封包失败：' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
finally {
    if ($temporaryPath -and (Test-Path -LiteralPath $temporaryPath -PathType Leaf)) { Remove-Item -LiteralPath $temporaryPath -Force }
}
