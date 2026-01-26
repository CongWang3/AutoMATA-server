<?php
/**
 * 文件上传处理辅助函数
 * 提供安全的文件上传处理，包含完整的错误检查和超时机制
 */

/**
 * 获取文件上传错误信息
 */
function getUploadErrorMessage($errorCode) {
    switch ($errorCode) {
        case UPLOAD_ERR_OK:
            return '文件上传成功';
        case UPLOAD_ERR_INI_SIZE:
            return '上传的文件超过了 php.ini 中 upload_max_filesize 选项限制的值';
        case UPLOAD_ERR_FORM_SIZE:
            return '上传文件的大小超过了 HTML 表单中 MAX_FILE_SIZE 选项指定的值';
        case UPLOAD_ERR_PARTIAL:
            return '文件只有部分被上传（上传中断）';
        case UPLOAD_ERR_NO_FILE:
            return '没有文件被上传';
        case UPLOAD_ERR_NO_TMP_DIR:
            return '找不到临时文件夹';
        case UPLOAD_ERR_CANT_WRITE:
            return '文件写入失败（磁盘空间不足或权限问题）';
        case UPLOAD_ERR_EXTENSION:
            return 'PHP扩展阻止了文件上传';
        default:
            return '未知的上传错误';
    }
}

/**
 * 安全地移动上传的文件
 * @param array $fileInfo $_FILES数组中的文件信息
 * @param string $destination 目标文件路径
 * @param int $maxWaitTime 最大等待时间（秒），默认30秒
 * @return array 返回 ['success' => bool, 'message' => string, 'file_path' => string]
 */
function safeMoveUploadedFile($fileInfo, $destination, $maxWaitTime = 30) {
    $result = [
        'success' => false,
        'message' => '',
        'file_path' => $destination
    ];
    
    // 1. 检查文件信息是否存在
    if (!isset($fileInfo) || empty($fileInfo)) {
        $result['message'] = '文件信息不存在';
        return $result;
    }
    
    // 2. 检查上传错误码
    if (!isset($fileInfo['error'])) {
        $result['message'] = '无法获取文件上传错误信息';
        return $result;
    }
    
    if ($fileInfo['error'] !== UPLOAD_ERR_OK) {
        $result['message'] = getUploadErrorMessage($fileInfo['error']);
        return $result;
    }
    
    // 3. 检查临时文件是否存在
    if (empty($fileInfo['tmp_name']) || !file_exists($fileInfo['tmp_name'])) {
        $result['message'] = '临时文件不存在或已被删除';
        return $result;
    }
    
    // 4. 检查文件大小（如果设置了）
    if (isset($fileInfo['size']) && $fileInfo['size'] == 0) {
        $result['message'] = '上传的文件为空';
        return $result;
    }
    
    // 5. 确保目标目录存在
    $destDir = dirname($destination);
    if (!file_exists($destDir)) {
        if (!mkdir($destDir, 0777, true)) {
            $result['message'] = '无法创建目标目录: ' . $destDir;
            return $result;
        }
    }
    
    // 6. 尝试移动文件
    $moveResult = @move_uploaded_file($fileInfo['tmp_name'], $destination);
    
    if (!$moveResult) {
        // 如果移动失败，可能是文件正在上传中，等待一段时间后重试
        $startTime = time();
        $retryCount = 0;
        $maxRetries = 10;
        
        while ($retryCount < $maxRetries && (time() - $startTime) < $maxWaitTime) {
            // 检查临时文件是否仍然存在
            if (!file_exists($fileInfo['tmp_name'])) {
                $result['message'] = '临时文件在上传过程中被删除';
                return $result;
            }
            
            // 检查临时文件是否完整（通过文件大小是否稳定）
            $fileSize1 = filesize($fileInfo['tmp_name']);
            usleep(500000); // 等待0.5秒
            $fileSize2 = filesize($fileInfo['tmp_name']);
            
            // 如果文件大小稳定，尝试再次移动
            if ($fileSize1 == $fileSize2 && $fileSize1 > 0) {
                $moveResult = @move_uploaded_file($fileInfo['tmp_name'], $destination);
                if ($moveResult) {
                    break;
                }
            }
            
            $retryCount++;
            sleep(1); // 等待1秒后重试
        }
        
        if (!$moveResult) {
            $result['message'] = '文件移动失败：可能是文件上传未完成、磁盘空间不足或权限问题';
            return $result;
        }
    }
    
    // 7. 验证目标文件是否存在且大小正确
    $waitStartTime = time();
    while (!file_exists($destination) && (time() - $waitStartTime) < 10) {
        usleep(200000); // 等待0.2秒
    }
    
    if (!file_exists($destination)) {
        $result['message'] = '文件移动后验证失败：目标文件不存在';
        return $result;
    }
    
    // 8. 验证文件大小（如果原始大小已知）
    if (isset($fileInfo['size']) && filesize($destination) != $fileInfo['size']) {
        // 允许小误差（可能是文件系统延迟）
        $sizeDiff = abs(filesize($destination) - $fileInfo['size']);
        if ($sizeDiff > 1024) { // 超过1KB的差异才报错
            $result['message'] = '文件大小不匹配：可能文件上传不完整';
            @unlink($destination); // 删除不完整的文件
            return $result;
        }
    }
    
    // 9. 设置文件权限
    @chmod($destination, 0666);
    
    $result['success'] = true;
    $result['message'] = '文件上传成功';
    return $result;
}

/**
 * 等待文件存在（带超时机制）
 * @param string $filePath 文件路径
 * @param int $maxWaitTime 最大等待时间（秒），默认30秒
 * @param float $checkInterval 检查间隔（秒），默认0.2秒
 * @return bool 文件是否存在
 */
function waitForFileExists($filePath, $maxWaitTime = 30, $checkInterval = 0.2) {
    $startTime = time();
    while (!file_exists($filePath)) {
        if ((time() - $startTime) >= $maxWaitTime) {
            return false;
        }
        usleep($checkInterval * 1000000); // 转换为微秒
    }
    return true;
}

/**
 * 批量处理文件上传
 * @param array $filesConfig 文件配置数组，格式：[['file_key' => 'upload_file_1', 'destination' => '/path/to/file.txt', 'required' => true], ...]
 * @param int $maxWaitTime 最大等待时间（秒）
 * @return array 返回 ['success' => bool, 'message' => string, 'files' => array]
 */
function batchMoveUploadedFiles($filesConfig, $maxWaitTime = 1000) {
    $result = [
        'success' => true,
        'message' => '',
        'files' => []
    ];
    
    $errors = [];
    
    foreach ($filesConfig as $config) {
        $fileKey = $config['file_key'];
        $destination = $config['destination'];
        $required = isset($config['required']) ? $config['required'] : true;
        
        // 检查文件是否存在
        if (!isset($_FILES[$fileKey])) {
            if ($required) {
                $errors[] = "必需的文件 '$fileKey' 不存在";
                $result['files'][$fileKey] = [
                    'success' => false,
                    'message' => "文件 '$fileKey' 不存在"
                ];
            } else {
                $result['files'][$fileKey] = [
                    'success' => true,
                    'message' => "可选文件 '$fileKey' 未上传",
                    'skipped' => true
                ];
            }
            continue;
        }
        
        // 检查是否为空上传（用户没有选择文件）
        if (isset($_FILES[$fileKey]['error']) && $_FILES[$fileKey]['error'] == UPLOAD_ERR_NO_FILE) {
            if ($required) {
                $errors[] = "必需的文件 '$fileKey' 未上传";
                $result['files'][$fileKey] = [
                    'success' => false,
                    'message' => "文件 '$fileKey' 未上传"
                ];
            } else {
                $result['files'][$fileKey] = [
                    'success' => true,
                    'message' => "可选文件 '$fileKey' 未上传",
                    'skipped' => true
                ];
            }
            continue;
        }
        
        // 移动文件
        $fileResult = safeMoveUploadedFile($_FILES[$fileKey], $destination, $maxWaitTime);
        $result['files'][$fileKey] = $fileResult;
        
        if (!$fileResult['success']) {
            if ($required) {
                $errors[] = "文件 '$fileKey' 上传失败: " . $fileResult['message'];
                $result['success'] = false;
            }
        }
    }
    
    if (!empty($errors)) {
        $result['message'] = implode('; ', $errors);
    } else {
        $result['message'] = '所有文件上传成功';
    }
    
    return $result;
}

