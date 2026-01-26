<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';
require './table/renderer.php';
require './table/renderer_2.php';
require './file_upload_helper.php';


// 显示等待页面（转圈圈）
// 嵌入Python脚本

// 设置JobID
date_default_timezone_set('Asia/Shanghai');
$jobID = date("YmdHis") . '_' . make_char(); // 时间作为job_id
//$jobID = '20250221173424_vrWcDe2W'; //测试使用

// 转移用户上传的文件到 download_data/Jobs/JobID.txt 中
$workdir = "download_data/Jobs/".$jobID."/";
$dir = iconv("UTF-8", "GBK", $workdir );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}

$workdir_result = $workdir."result";  // 放模型训练结果的文件夹
$dir = iconv("UTF-8", "GBK", $workdir_result );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}

// cursor
// 表型文件
// $fileInfo = $_FILES["upload_pheno"];  //获取上传文件对应的字典（对象  Array类型
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . $jobID . '_pheno.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
// // 组学文件
// $fileInfo = $_FILES["upload_file_1"]; 
// $filePath = $fileInfo["tmp_name"]; 
// move_uploaded_file($filePath, $workdir . $jobID . '_omics_1.txt'); 
// $fileInfo = $_FILES["upload_file_2"];  
// $filePath = $fileInfo["tmp_name"];  
// move_uploaded_file($filePath, $workdir . $jobID . '_omics_2.txt'); 
// $fileInfo = $_FILES["upload_file_3"]; 
// $filePath = $fileInfo["tmp_name"]; 
// move_uploaded_file($filePath, $workdir . $jobID . '_omics_3.txt');

// 使用安全的文件上传处理函数
$filesConfig = [
    ['file_key' => 'upload_pheno', 'destination' => $workdir . $jobID . '_pheno.txt', 'required' => true],
    ['file_key' => 'upload_file_1', 'destination' => $workdir . $jobID . '_omics_1.txt', 'required' => true],
    ['file_key' => 'upload_file_2', 'destination' => $workdir . $jobID . '_omics_2.txt', 'required' => true],
    ['file_key' => 'upload_file_3', 'destination' => $workdir . $jobID . '_omics_3.txt', 'required' => true]
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

$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n  from integration php");
    fclose($myFile);
}

// 运行python代码并告知用户JobID
// 告知用户JobID：表格样式 
$style_table = "width: 1296px; text-align: center; line-height: 50px; border-collapse: collapse;"; // 表格样式
$style_odd = "background-color: #F7F7F7;";  // 表格奇数行的样式
$style_line = "border-right: 1px solid #c0c0c0; width: 648px;";  // 中间的竖线
$style_strong = "color: #1e88e5;font-weight: bold;";
$style_text = "line-height: 1.5; margin-bottom: 10px;";
echo "
<section id='banner'>
    <div class='container padding-medium-2'>
        <div class='hero-content'>
            <h2 class='display-2 fw-semibold'>Waiting</span></h2>
            <nav class='breadcrumb'>
                <span class='breadcrumb-item active' aria-current='page'>Your JobID is $jobID, please wait a moment.</span>
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
                <td class='line' style='$style_line'>Running</td>
                <td><img id='running_bar' src='images/progress_bar_new.gif' height='25px'></td>
            </tr>
        </table>
    </div>
</section>";

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


// 运行Python命令
$python3 = "/opt/anaconda/envs/automata/bin/python";  // 用where python找python.exe在哪。太诡异了，pt36的python找不着了，现在用的python路径和base环境的一样
$pyfile = "/xp/www/AutoMATA/code/train_model/integration.py"; // D:\wamp\www\multi_omics_own\code\cnn.py
$outfile = $workdir_result . "/terminal.log";  // 输出终端打印数据到terminal.log文件中
$result = $workdir . $jobID . '_result.txt';
$param_jobID = " --jobID ".$jobID;
$param_pheno = " --pheno_file ".$workdir . $jobID . '_pheno.txt';
$param_omics_1 = " --file_1 ".$workdir . $jobID . '_omics_1.txt';
$param_omics_2 = " --file_2 ".$workdir . $jobID . '_omics_2.txt';
$param_omics_3 = " --file_3 ".$workdir . $jobID . '_omics_3.txt';
$param_outfile = " --output_file ".$result;
$cmd = "" . $python3 ." ".$pyfile. $param_jobID. $param_pheno. $param_omics_1. $param_omics_2. $param_omics_3. $param_outfile. " > " .$outfile." 2>&1 &";
// 加载信息Config
$myFile = fopen($workdir. 'config.txt', 'w') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);


// cursor
// while (true){  // 增加
//     if (file_exists($workdir . $jobID . '_omics_1.txt') && file_exists($workdir . $jobID . '_omics_2.txt') && file_exists($workdir . $jobID . '_omics_3.txt') && file_exists($workdir . $jobID . '_pheno.txt') ){
//         // 文件已存在或者等待时间大于十秒，跳出循环
//         break;
//     }
//     sleep(1); // 暂停 1 秒后继续检测
// }
// 验证所有文件都已成功上传（使用带超时的等待函数）
$requiredFiles = [
    $workdir . $jobID . '_pheno.txt',
    $workdir . $jobID . '_omics_1.txt',
    $workdir . $jobID . '_omics_2.txt',
    $workdir . $jobID . '_omics_3.txt'
];

$allFilesExist = true;
foreach ($requiredFiles as $filePath) {
    if (!waitForFileExists($filePath, 1000, 1)) {
        $allFilesExist = false;
        $errorLog = $workdir . 'upload_error.log';
        @file_put_contents($errorLog, date('Y-m-d H:i:s') . " - 文件不存在: $filePath\n", FILE_APPEND);
        break;
    }
}

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



// 修改文件权限
setFilePermission($workdir, 0777);

system($cmd, $ret);
// // 压缩文件夹$workdir_result，以给用户下载
// $zipFilePath = $workdir_result.".zip";
// make_zip_file_for_folder($zipFilePath, $workdir_result);

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

    while (true){
        if (file_exists($result)){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }
    setFilePermission($result, 0777);

    // 显示下载结果页面
    $download_name='result.txt';
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo "
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
                    <td class='line' style='$style_line'>Result</td>
                    <td><a href='download.php?file=" . urlencode($result) . "' class='btn btn-primary btn-primary-lin-height'>download</a></td>

                </tr>
                
            </table>
        </div>
    </section>";

    // try {
    //     $filePath = '../'.$workdir_result . '/test_result.txt';
    //     echo renderOntologyTable_2($filePath, 'test_result.txt');  // 显示结果
    // } catch (Exception $e) {
    //     echo "Error: " . $e->getMessage();
    // }

}else{
    // 显示处理失败信息
    $con = mysqli_connect("localhost", "root", "123456", "multi_omics");
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
    echo "
    <section id='banner'>
        <div class='container padding-medium-2'>
            <div class='hero-content'>
                <!-- <h2 class='display-2 fw-semibold'>About <span class='text-primary'> Us</span></h2> -->
                <h2 class='display-2 fw-semibold'>Waiting</span></h2>
                <nav class='breadcrumb'>
                    <span class='breadcrumb-item active' aria-current='page'>Your JobID is $jobID, please wait a moment.</span>
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
                    <td class='line' style='$style_line'>Result</td>
                    <td>Integration failure!</td>
                </tr>
            </table>
        </div>
    </section>";
}



// $email
if ($ret == 0){


$email = $_POST["email"];
if ($email != ""){

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
        $mail->Body    = "<p>Dear user, <br/>Your JobID is $jobID. "."Your model using results are attached."."<br /></p>". date('Y-m-d H:i:s');
        // $mail->AltBody = '如果邮件客户端不支持HTML则显示此内容';
        // $mail->AltBody = "Dear user, your JobID is $jobID, you can enter $jobID via 'CheckJob' function to obtain your result.";
        $mail->AddAttachment($result, "result.txt"); // 附件的路径和名称

        $mail->send();
        // echo '邮件发送成功';
    } catch (Exception $e) {
        echo '邮件发送失败: ', $mail->ErrorInfo;
    }

}}

// echo "<p>$geneIDType, $inputType, $organism </p>";

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
