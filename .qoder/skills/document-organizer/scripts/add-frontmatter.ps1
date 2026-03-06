# 添加 YAML Frontmatter 元数据块
# 用法：.\scripts\add-frontmatter.ps1 -FilePath "文档路径.md" -Title "标题" -Type "类型" -Category "分类" -Author "作者" -Tags @("标签 1","标签 2")

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [Parameter(Mandatory=$true)]
    [string]$Title,
    
    [Parameter(Mandatory=$true)]
    [string]$Type,
    
    [Parameter(Mandatory=$true)]
    [string]$Category,
    
    [Parameter(Mandatory=$true)]
    [string]$Author,
    
    [Parameter(Mandatory=$false)]
    [string[]]$Tags = @("文档", "技术"),
    
    [Parameter(Mandatory=$false)]
    [hashtable]$ExtraFields = @{}
)

# 验证文件存在
if (-not (Test-Path $FilePath)) {
    Write-Error "文件不存在：$FilePath"
    exit 1
}

# 生成时间戳
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

# 构建 tags 字符串
$tagsString = $Tags -join ', '

# 构建 extra fields 字符串
$extraFieldsString = ""
foreach ($key in $ExtraFields.Keys) {
    $extraFieldsString += "$key`: $($ExtraFields[$key])`n"
}

# 生成 frontmatter
$frontmatter = @"
---
title: $Title
type: $Type
category: $Category
created: $timestamp
modified: $timestamp
version: v1.0
author: $Author
status: published
tags: [$tagsString]
related:
  - docs/相关文档.md
$($extraFieldsString.TrimEnd())
---

"@

# 读取原文件内容
try {
    $content = Get-Content -Path $FilePath -Raw -Encoding UTF8
    
    # 检查是否已有 frontmatter
    if ($content -match '^---\s*$') {
        Write-Warning "文件已包含 frontmatter，将替换..."
        # 这里可以添加替换逻辑，暂时跳过
    }
    
    # 组合新内容
    $newContent = $frontmatter + $content
    
    # 写回文件
    $newContent | Set-Content -Path $FilePath -Encoding UTF8 -NoNewline
    
    Write-Host "✅ 成功为文件添加元数据：$FilePath"
    Write-Host "   标题：$Title"
    Write-Host "   类型：$Type / $Category"
    Write-Host "   标签：$tagsString"
    
} catch {
    Write-Error "处理文件失败：$_"
    exit 1
}
