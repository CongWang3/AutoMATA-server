<?php
    # 下载文件
    if (isset($_GET['file'])) {
        $file_path = $_GET['file'];
        echo $file_path;
        if (file_exists($file_path)) {
            header('Content-Description: File Transfer');
            header('Content-Type: application/octet-stream');
            header('Content-Disposition: attachment; filename="' . basename($file_path) . '"');
            header('Content-Length: ' . filesize($file_path));
            // 清除输出缓冲区并关闭压缩  即可以在超链接中正常下载图片文件，图片也不会损坏
            while (ob_get_level()) ob_end_clean();
            @ini_set('zlib.output_compression', 'Off');

            readfile($file_path);
            exit;
        } else {
            http_response_code(404);
            echo "文件不存在";
        }
    }
?>
