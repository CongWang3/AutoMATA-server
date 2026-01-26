<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';
require './table/renderer.php';
require './file_upload_helper.php';


// 显示等待页面（转圈圈）
// 嵌入R脚本
set_time_limit(0); 

    

// 参数
$org = array("Homo_sapiens", "Bovine", "Mus_musculus", "Drosophila_melanogaster");
$organism = $org[$_POST["organism"]]; 
$fc = $_POST["fc"];
$padj = $_POST["padj"];
$types = array("read_counts", "fpkm");
$type = $types[$_POST["type"]];  // "read_counts", "fpkm"
$corres = array("BH", "BY", "holm", "hochberg", "hommel", "bonferroni", "none");  // 一审 新增
$correction = $corres[$_POST["correction"]];  // 一审 新增

// 设置JobID
date_default_timezone_set('Asia/Shanghai');
$jobID = date("YmdHis") . '_' . make_char(); // 时间作为job_id

// 转移用户上传的文件到 download_data/Jobs/JobID.txt 中
$workdir = "download_data/Jobs/".$jobID."/";
$dir = iconv("UTF-8", "GBK", $workdir );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}
$workdir_result = $workdir."result";  // 放图片的文件夹
$dir = iconv("UTF-8", "GBK", $workdir_result );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}

// cursor
// $fileInfo = $_FILES["upload_file_1"];  //获取上传文件对应的字典（对象  Array类型 
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . $jobID . '_data.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
// 使用安全的文件上传处理函数
$filesConfig = [
    ['file_key' => 'upload_file_1', 'destination' => $workdir . $jobID . '_data.txt', 'required' => true],
    ['file_key' => 'upload_file_2', 'destination' => $workdir . $jobID . '_info.txt', 'required' => true]
];

$uploadResult = batchMoveUploadedFiles($filesConfig, 60); // 最大等待60秒

if (!$uploadResult['success']) {
    // 文件上传失败，记录错误并终止
    $errorLog = $workdir . 'upload_error.log';
    @file_put_contents($errorLog, date('Y-m-d H:i:s') . " - 文件上传失败: " . $uploadResult['message'] . "\n", FILE_APPEND);
    
    // 连接数据库更新状态
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if ($con) {
        $status = "Failed";
        $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
        @mysqli_query($con, $sql);
        mysqli_close($con);
    }
    
    die("文件上传失败: " . $uploadResult['message'] . "<br>JobID: $jobID<br>请检查文件大小和格式，然后重试。");
}

// 验证所有文件都已成功上传
$requiredFiles = [
    $workdir . $jobID . '_data.txt',
    $workdir . $jobID . '_info.txt'
];

$allFilesExist = true;
foreach ($requiredFiles as $filePath) {
    if (!waitForFileExists($filePath, 10, 0.2)) {
        $allFilesExist = false;
        $errorLog = $workdir . 'upload_error.log';
        @file_put_contents($errorLog, date('Y-m-d H:i:s') . " - 文件不存在: $filePath\n", FILE_APPEND);
        break;
    }
}

// $fileInfo = $_FILES["upload_file_2"];  //获取上传文件对应的字典（对象  Array类型 
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . $jobID . '_info.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
if (!$allFilesExist) {
    // 连接数据库更新状态
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if ($con) {
        $status = "Failed";
        $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
        @mysqli_query($con, $sql);
        mysqli_close($con);
    }
    die("文件验证失败：部分文件不存在。JobID: $jobID");
}

$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'Jobs/' . $jobID . '/email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n from all_analysis2 php");
    fclose($myFile);
}


// 大文件上传失败，解决方法。修改php.ini文件<marker为一审>，找到 upload_max_filesize 250M 和 post_max_size 500M, max_execution_time 60000, max_input_time 3000 修改为更大的值。
// php.ini在：D:\wamp\bin\apache\apache2.4.54.2\bin\php.ini
// echo "当前php.ini路径: " . php_ini_loaded_file() . "\n<br>";
// echo "upload_max_filesize: " . ini_get('upload_max_filesize') . "\n";  100M
// echo "post_max_size: " . ini_get('post_max_size') . "\n";  # 以下几乎乘以2或3或4的量
// echo "max_execution_time: " . ini_get('max_execution_time') . "\n";  # 60000
// echo "max_input_time: " . ini_get('max_input_time') . "\n";
// echo "memory_limit: " . ini_get('memory_limit') . "\n";
// echo "max_file_uploads: " . ini_get('max_file_uploads') . "\n";

// // 检查上传错误
// if ($_FILES) {
//     foreach ($_FILES as $file) {
//         if ($file['error'] > 0) {
//             echo "Upload Error: " . $file['error'] . "\n";
//             switch ($file['error']) {
//                 case UPLOAD_ERR_INI_SIZE:
//                     echo "File exceeds upload_max_filesize\n";
//                     break;
//                 case UPLOAD_ERR_FORM_SIZE:
//                     echo "File exceeds MAX_FILE_SIZE in form\n";
//                     break;
//                 case UPLOAD_ERR_PARTIAL:
//                     echo "File only partially uploaded\n";
//                     break;
//                 case UPLOAD_ERR_NO_FILE:
//                     echo "No file was uploaded\n";
//                     break;
//                 case UPLOAD_ERR_NO_TMP_DIR:
//                     echo "Missing temporary folder\n";
//                     break;
//                 case UPLOAD_ERR_CANT_WRITE:
//                     echo "Failed to write file to disk\n";
//                     break;
//             }
//         }
//     }
// }
// phpinfo();  // 查看php.ini文件在哪
// exit(0);  // 退出脚本





// 运行 R代码并告知用户JobID
// 告知用户JobID：表格样式 

$style_table = "width: 1296px; text-align: center; line-height: 50px; border-collapse: collapse;"; // 表格样式
$style_odd = "background-color: #F7F7F7;";  // 表格奇数行的样式
$style_line = "border-right: 1px solid #c0c0c0; width: 648px;";  // 中间的竖线

$basic_info = "
<section id='banner'>
    <div class='container padding-medium-2'>
        <div class='hero-content'>
            <h2 class='display-2 fw-semibold'>Result</span></h2>
            <nav class='breadcrumb'>
                <span class='breadcrumb-item active' aria-current='page'>Your JobID is $jobID.</span>
            </nav>
        </div>
    </div>
</section>

<section id='service' class='padding-medium'>
    <div class='container'>
        <table style = '$style_table'>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>JobID</td>
                <td>$jobID</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Organism</td>
                <td>$organism</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Correction Method</td>
                <td>$correction</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Log2(Fold Change) threshold</td>
                <td>$fc</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>padj threshold</td>
                <td>$padj</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Type</td>
                <td>$type</td>
            </tr>
";
// ob_start(); // 启用输出缓冲
echo $basic_info;
echo"
            <tr>
                <td class='line' style='$style_line'>Running</td>
                <td><img id='running_bar' src='images/progress_bar_new.gif' height='25px'></td>
            </tr>
        </table>
    </div>
</section>
";



// 连接数据库, 插入joblist表
$con = mysqli_connect("localhost", "automata", "123456", "automata");
if (!$con) {
    echo "could not connect to mysql";
    die('Could not connect: ' . mysqli_connect_error());
}
$status = "Submitted";
$sql = "INSERT INTO joblist (job_id, job_status) VALUES ('$jobID', '$status')";
if (!mysqli_query($con, $sql)) {
    die('Error: ' . mysqli_error($con));
}
mysqli_close($con);

while (true){
    if (file_exists($workdir . $jobID . '_info.txt') && file_exists($workdir . $jobID . '_data.txt')){  // svg
        // 文件已存在，跳出循环
        break;
    }
    sleep(0.2); // 暂停 1 秒后继续检测
}


// 运行R命令
// cmd: Rscript cor_heatmap.r -i cor_heatmap_example.txt
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
$expression_file = $workdir . $jobID . '_data.txt';  # 数据路径
$info_file = $workdir . $jobID . '_info.txt';  # 信息路径
if ($type == "read_counts"){
    $rfile = "code/DESeq2_read_count.R";
}else{
    $rfile = "code/limma_fpkm_df.R";
}
$param_i = " -i ".$expression_file;
$param_k = " -k ".$info_file;
$param_j = " -j ".$jobID;
$param_c = " -c ".$fc;
$param_d = " -d ".$padj;
$param_e = " -e ".$correction;  // 一审 新增

// $cmd = "". $rscript . " ". $rfile. $param_i. $param_k. $param_j. $param_c. $param_d. " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &
$cmd = "". $rscript . " ". $rfile. $param_i. $param_k. $param_j. $param_c. $param_d. $param_e. " > " . $workdir . "terminal_msg.txt 2>&1 ";  // 一审 修改

// 加载信息Config
$administrator_workdir = "/xp/www/AutoMATA/download_data/";
$myFile = fopen($administrator_workdir . 'Jobs/' . $jobID . '/config.txt', 'w') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);
system($cmd, $ret);

if ($ret == 0){  // 运行成功
    // 修改joblist表
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if (!$con) {
        echo "could not connect to mysql";
        die('Could not connect: ' . mysqli_connect_error());
    }
    $status = "Finished";
    $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
    if (!mysqli_query($con, $sql)) {
        die('Error: ' . mysqli_error($con));
    }
    mysqli_close($con);

    while (true){  // 修改6
        if (file_exists($workdir_result.'/df_cluster_heatmap.svg')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
    // 修改文件权限 修改7
    setFilePermission($workdir_result, 0777);

    // 显示下载结果页面
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
    // 底部横线  style='border-bottom: 1px solid #cdcdcd;'
    // 一审 修改样式
    echo"
                <tr class='odd' style='$style_odd'>
                    <td style='border-right: 1px solid #c0c0c0; line-height: 400px;'><img src='$workdir_result/volcano.png?t=" . time() ." ' height='400px'></td>
                    <td>
                        <div class='dropdown' style='display: flex; justify-content: space-around;'>
                            <button class='dropdown-toggle btn btn-primary' data-bs-toggle='dropdown' id='volcano' role='button' style='display: flex; align-items: center'><i class='material-icons'>file_download</i>Download Volcano</button>
                            <div class='dropdown-menu' aria-labelledby='volcano'>

                                <li><a href='download.php?file=" . urlencode($workdir_result."/volcano.pdf") . "' class='dropdown-item'>PDF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/volcano.png") . "' class='dropdown-item'>PNG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/volcano.svg") . "' class='dropdown-item'>SVG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/volcano.tiff") . "' class='dropdown-item'>TIFF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/volcano.jpeg") . "' class='dropdown-item'>JPEG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/volcano.bmp") . "' class='dropdown-item'>BMP</a></li>

                            </div>
                        </div>
                    </td>
                </tr>

                <tr>
                    <td style='border-right: 1px solid #c0c0c0; line-height: 400px;'><img src='$workdir_result/df_cluster_heatmap.png?t=" . time() ." ' height='400px'></td>
                    <td>
                        <div class='dropdown' style='display: flex; justify-content: space-around;'>
                            <button class='dropdown-toggle btn btn-primary' data-bs-toggle='dropdown' id='cluster' role='button' style='display: flex; align-items: center'><i class='material-icons'>file_download</i>Download Heatmap</button>
                            <div class='dropdown-menu' aria-labelledby='cluster'>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/df_cluster_heatmap.pdf") . "' class='dropdown-item'>PDF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/df_cluster_heatmap.png") . "' class='dropdown-item'>PNG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/df_cluster_heatmap.svg") . "' class='dropdown-item'>SVG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/df_cluster_heatmap.tiff") . "' class='dropdown-item'>TIFF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/df_cluster_heatmap.jpeg") . "' class='dropdown-item'>JPEG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/df_cluster_heatmap.bmp") . "' class='dropdown-item'>BMP</a></li>
                            </div>
                        </div>
                    </td>                
                </tr>

                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Differential genes and results</td>
                    <td>
                        <div class='dropdown' style='display: flex; justify-content: space-around;'>
                            <button class='dropdown-toggle btn btn-primary' data-bs-toggle='dropdown' id='results' role='button' style='display: flex; align-items: center'><i class='material-icons'>file_download</i>Download Results</button>
                            <div class='dropdown-menu' aria-labelledby='results'>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/select_all.txt") . "' class='dropdown-item'>All DEGs</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/select_up.txt") . "' class='dropdown-item'>UP DEGs</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/select_down.txt") . "' class='dropdown-item'>DOWN DEGs</a></li>
                            </div>
                        </div>
                    </td> 
                </tr>


                <tr style='border-bottom: 1px solid #cdcdcd;'>
                    <td class='line' style='$style_line'>GO and KEGG enrichment analysis</td>
                    <td><a href='all_analysis_sub.php?jobID=$jobID?org=$organism' target='_blank' class='btn btn-primary btn-primary-lin-height'>GO</a> </td>
                </tr>



             </table>

        </div>
    </section>
    ";

    // 实现分页显示差异分析结果 DESeq2_all_select.txt
    // try {
    //     $filePath = '../'.$workdir_result . '/GO_enrichment_result.txt';
    //     echo renderOntologyTable($filePath, 'GO_enrichment_result.txt');
    // } catch (Exception $e) {
    //     echo "Error: " . $e->getMessage();
    // }

}else{ // 显示处理失败信息
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if (!$con) {
        echo "could not connect to mysql";
        die('Could not connect: ' . mysqli_connect_error());
    }
    $status = "Failed";
    $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
    if (!mysqli_query($con, $sql)) {
        die('Error: ' . mysqli_error($con));
    }
    mysqli_close($con);

    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
    echo"
                <tr style='border-bottom: 1px solid #cdcdcd;'>
                    <td class='line' style='$style_line'>Results</td>
                    <td>Results generation failure!</td>
                </tr>
            </table>
        </div>
    </section>
    ";


}



// $email
// 压缩文件夹$workdir_result，以给用户下载
$email = $_POST["email"];
if ($ret == 0){
if ($email != ""){
    $zipFilePath = $workdir_result.".zip";
    make_zip_file_for_folder($zipFilePath, $workdir_result);

    $mail = new PHPMailer(true);                              // Passing `true` enables exceptions
    try {
        //服务器配置
        $mail->CharSet ="UTF-8";                     //设定邮件编码
        $mail->SMTPDebug = 0;                        // 调试模式输出
        $mail->isSMTP();                             // 使用SMTP
        $mail->Host = 'smtp.163.com';                // SMTP服务器
        $mail->SMTPAuth = true;                      // 允许 SMTP 认证
        $mail->Username = 'wanger0808@163.com';                // SMTP 用户名  即邮箱的用户名
        $mail->Password = 'DYHQMFHAHHIEEEUZ';             // SMTP 密码  部分邮箱是授权码(例如163邮箱)
        $mail->SMTPSecure = 'ssl';                    // 允许 TLS 或者ssl协议
        $mail->Port = 465;                            // 服务器端口 25 或者465 具体要看邮箱服务器支持

        $mail->setFrom('wanger0808@163.com', 'Multi Omics');  //发件人
        $mail->addAddress($email, 'Joe');  // 收件人
        //$mail->addAddress('ellen@example.com');  // 可添加多个收件人
        $mail->addReplyTo('wanger0808@163.com', 'info'); //回复的时候回复给哪个邮箱 建议和发件人一致
        //$mail->addCC('cc@example.com');                    //抄送
        //$mail->addBCC('bcc@example.com');                    //密送

        //发送附件
        // $mail->addAttachment('../xy.zip');         // 添加附件
        // $mail->addAttachment('../thumb-1.jpg', 'new.jpg');    // 发送附件并且重命名

        //Content
        $mail->isHTML(true);                                  // 是否以HTML文档格式发送  发送后客户端可直接显示对应HTML内容
        // $mail->Subject = '这里是邮件标题' . time();  // 这里是邮件标题1723129210
        $mail->Subject = 'Multi Omics Result';
        // $mail->Body    = '<h1>test</h1>' . date('Y-m-d H:i:s');
        // 使用链接，点击链接会报错404.所以这里使用附件方法
        $mail->Body    = "<p>Dear user, <br/>"."Your drawing results are attached."."<br /></p>". date('Y-m-d H:i:s');
        // $mail->AltBody = '如果邮件客户端不支持HTML则显示此内容';
        // $mail->AltBody = "Dear user, your JobID is $jobID, you can enter $jobID via 'CheckJob' function to obtain your result.";
        $mail->AddAttachment($zipFilePath, "result.zip"); // 附件的路径和名称

        $mail->send();
        // echo '邮件发送成功';
    } catch (Exception $e) {
        echo '邮件发送失败: ', $mail->ErrorInfo;
    }

}}


// 修改文件/递归修改文件夹中文件权限为0777 
function setFilePermission ($path='', $filemode=0777) {
    if (!is_dir($path))
    return chmod($path, $filemode);
    $dh = opendir($path);
    while (($file = readdir($dh)) !== false) {
    if($file != '.' && $file != '..') {
    $fullpath = $path.'/'.$file;
    if(is_link($fullpath))
    return FALSE;
    elseif(!is_dir($fullpath) && !chmod($fullpath, $filemode))
    return FALSE;
    elseif(!setFilePermission($fullpath, $filemode))
    return FALSE;
    }
    }
    closedir($dh);
    if(!chmod($path, $filemode))
    die('Unable to modify permissions');
    // else
    // echo "true"; 
}

function make_char($length = 8)
{
    $chars = array(
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
        'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
        't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D',
        'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
        'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    );
    // 
    $char_txt = '';
    for ($i = 0; $i < $length; $i++) {
        // make a random char array, length is 8
        $char_txt .= $chars[array_rand($chars)];
    }
    return $char_txt;
}

// 压缩文件夹
function make_zip_file_for_folder ($zip_path = '', $folder_path = '') {
    // Get real path for our folder
    $rootPath = realpath($folder_path);
 
    // Initialize archive object
    $zip = new ZipArchive();
    $zip->open($zip_path, ZipArchive::CREATE | ZipArchive::OVERWRITE);
 
    // Create recursive directory iterator
    /** @var SplFileInfo[] $files */
    $files = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($rootPath),
        RecursiveIteratorIterator::LEAVES_ONLY
    );
 
    foreach ($files as $name => $file)
    {
        // Skip directories (they would be added automatically)
        if (!$file->isDir())
        {
            // Get real and relative path for current file
            $filePath = $file->getRealPath();
            $relativePath = substr($filePath, strlen($rootPath) + 1);
 
            // Add current file to archive
            $zip->addFile($filePath, $relativePath);
        }
    }
 
    // Zip archive will be created only after closing object
    $zip->close();
}


include __DIR__ . '/footer.php';


