# 移动文档到目标分类目录
# 用法：.\scripts\move-to-category.ps1 -FilePath "文档路径.md" -Category "分类"

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [Parameter(Mandatory=$true)]
    [string]$Category,
    
    [Parameter(Mandatory=$false)]
    [string]$BaseDocsPath = "docs"
)

# 验证文件存在
if (-not (Test-Path $FilePath)) {
    Write-Error "文件不存在：$FilePath"
    exit 1
}

# 分类映射表
$categoryMap = @{
    'architecture' = 'overview/architecture'
    'design' = 'design'
    'implementation' = 'design'
    'api' = 'api'
    'data' = 'design'
    'testing' = 'testing'
    'test' = 'testing'
    'bugfix' = 'testing'
    'reviews' = 'reviews'
    'review' = 'reviews'
    'navigation' = 'guides'
    'management' = 'guides'
    'project' = 'delivery'
    'overview' = 'overview'
}

# 获取目标目录
if (-not $categoryMap.ContainsKey($Category)) {
    Write-Warning "未知分类：$Category，将移动到 docs/ 根目录"
    $targetDir = $BaseDocsPath
} else {
    $targetDir = Join-Path $BaseDocsPath $categoryMap[$Category]
}

# 创建目标目录（如果不存在）
if (-not (Test-Path $targetDir)) {
    Write-Host "创建目录：$targetDir"
    New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
}

# 获取文件名
$fileName = Split-Path -Leaf $FilePath

# 构建目标路径
$targetPath = Join-Path $targetDir $fileName

try {
    # 移动文件
    Move-Item -Path $FilePath -Destination $targetPath -Force
    
    Write-Host "✅ 成功移动文档："
    Write-Host "   从：$FilePath"
    Write-Host "   到：$targetPath"
    Write-Host "   分类：$Category → $($categoryMap[$Category])"
    
} catch {
    Write-Error "移动文件失败：$_"
    exit 1
}
