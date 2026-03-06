# 重命名文档以符合规范
# 用法：.\scripts\rename-document.ps1 -FilePath "文档路径.md" -Type "类型"

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [Parameter(Mandatory=$true)]
    [string]$Type,
    
    [Parameter(Mandatory=$false)]
    [string]$CustomName = ""
)

# 验证文件存在
if (-not (Test-Path $FilePath)) {
    Write-Error "文件不存在：$FilePath"
    exit 1
}

# 获取目录和文件名
$dir = Split-Path -Parent $FilePath
$fileName = Split-Path -Leaf $FilePath
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)

# 生成新名称
$newName = ""

switch ($Type.ToLower()) {
    'test' {
        # TEST-模块名 -YYYYMMDD.md
        $date = Get-Date -Format 'yyyyMMdd'
        if ($CustomName) {
            $newName = "TEST-$($CustomName)_$date.md"
        } else {
            $newName = "TEST-$($baseName)_$date.md"
        }
    }
    'bugfix' {
        # BUGFIX-问题描述 -YYYYMMDD.md
        $date = Get-Date -Format 'yyyyMMdd'
        if ($CustomName) {
            $newName = "BUGFIX_$($CustomName)_$date.md"
        } else {
            $newName = "BUGFIX_$($baseName)_$date.md"
        }
    }
    'review' {
        # CODE_REVIEW-模块名 -YYYYMMDD.md
        $date = Get-Date -Format 'yyyyMMdd'
        if ($CustomName) {
            $newName = "CODE_REVIEW_$($CustomName)_$date.md"
        } else {
            $newName = "CODE_REVIEW_$($baseName)_$date.md"
        }
    }
    default {
        # 其他类型保持不变或使用自定义名称
        if ($CustomName) {
            $newName = "$CustomName.md"
        } else {
            $newName = $fileName
        }
    }
}

# 清理文件名中的非法字符
$newName = $newName -replace '[<>:"/\\|?*]', '_'

try {
    $targetPath = Join-Path $dir $newName
    
    # 重命名文件
    Rename-Item -Path $FilePath -NewName $newName -Force
    
    Write-Host "✅ 成功重命名文档："
    Write-Host "   原名称：$fileName"
    Write-Host "   新名称：$newName"
    Write-Host "   类型：$Type"
    
} catch {
    Write-Error "重命名文件失败：$_"
    exit 1
}
