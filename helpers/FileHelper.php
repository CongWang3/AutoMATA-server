<?php
class FileHelper {
    public static function makeChar($length = 8) {
        $chars = array_merge(range('a', 'z'), range('A', 'Z'), range('0', '9'));
        $result = '';
        for ($i = 0; $i < $length; $i++) {
            $result .= $chars[array_rand($chars)];
        }
        return $result;
    }
    
    public static function setFilePermission($path, $filemode = 0777) {
        if (!is_dir($path)) {
            return chmod($path, $filemode);
        }
        
        $dh = opendir($path);
        while (($file = readdir($dh)) !== false) {
            if ($file != '.' && $file != '..') {
                $fullpath = $path . '/' . $file;
                if (is_link($fullpath)) {
                    return false;
                } elseif (!is_dir($fullpath)) {
                    chmod($fullpath, $filemode);
                } else {
                    self::setFilePermission($fullpath, $filemode);
                }
            }
        }
        closedir($dh);
        return chmod($path, $filemode);
    }
    
    public static function makeZip($zipPath, $folderPath) {
        $rootPath = realpath($folderPath);
        $zip = new ZipArchive();
        $zip->open($zipPath, ZipArchive::CREATE | ZipArchive::OVERWRITE);
        
        $files = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($rootPath),
            RecursiveIteratorIterator::LEAVES_ONLY
        );
        
        foreach ($files as $file) {
            if (!$file->isDir()) {
                $filePath = $file->getRealPath();
                $relativePath = substr($filePath, strlen($rootPath) + 1);
                $zip->addFile($filePath, $relativePath);
            }
        }
        
        $zip->close();
    }
}