<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';
require './file_upload_helper.php';


// 显示等待页面（转圈圈）
// 嵌入R脚本

$geneIDTypes = array("GeneID", "EnsemblID", "Symbol");
$inputTypes = array("FPKM", "RPM", "RPKM", "ReadCounts", "TPM");
$organisms = array("homo_sapiens", "bos_taurus", "mus_musculus", "drosophila_melanogaster" ,"arabidopsis_thaliana" );  // ******待改 要增加物种

$geneIDType_index = $_POST["geneMomen"];  // 获取option的value. 0=Gene ID, 1=Ensemble Gene ID, 2=Gene Symbol
$inputType_index = $_POST["inputType"];  // 获取option的value. 0=FPKM
$organism_index = $_POST["organism"];  // 获取option的value. 0=Homo sapiens

$geneIDType = $geneIDTypes[$geneIDType_index];
$inputType = $inputTypes[$inputType_index];
$organism = $organisms[$organism_index];

// 设置JobID
date_default_timezone_set('Asia/Shanghai');
$jobID = date("YmdHis") . '_' . make_char(); // 时间作为job_id

// 转移用户上传的文件到 download_data/PreProcessFiles/JobID.txt 中
// cursor
// $workdir = "D:/wamp/www/multi_omics_own/download_data/";
// $fileInfo = $_FILES["upload_file"];  //获取上传文件对应的字典（对象  Array类型
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// 转移用户上传的文件到 download_data/Jobs/JobID.txt 中
$workdir = "/xp/www/AutoMATA/download_data/Jobs/".$jobID."/";
$dir = iconv("UTF-8", "GBK", $workdir );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}
// move_uploaded_file($filePath, $workdir . "origin.txt");  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

// 使用安全的文件上传处理函数
$fileResult = safeMoveUploadedFile($_FILES["upload_file"], $workdir . "origin.txt", 60);
if (!$fileResult['success']) {
    $errorLog = $workdir . 'upload_error.log';
    @file_put_contents($errorLog, date('Y-m-d H:i:s') . " - 文件上传失败: " . $fileResult['message'] . "\n", FILE_APPEND);
    
    // 连接数据库更新状态
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if ($con) {
        $status = "Failed";
        $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
        @mysqli_query($con, $sql);
        mysqli_close($con);
    }
    
    die("文件上传失败: " . $fileResult['message'] . "<br>JobID: $jobID<br>请检查文件大小和格式，然后重试。");
}

// 验证文件存在
if (!waitForFileExists($workdir . "origin.txt", 10, 0.2)) {
    $errorLog = $workdir . 'upload_error.log';
    @file_put_contents($errorLog, date('Y-m-d H:i:s') . " - 文件验证失败: " . $workdir . "origin.txt\n", FILE_APPEND);
    
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if ($con) {
        $status = "Failed";
        $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
        @mysqli_query($con, $sql);
        mysqli_close($con);
    }
    
    die("文件验证失败：文件不存在。JobID: $jobID");
}

$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n from dataProcess php for gene");
    fclose($myFile);
}


// 运行R命令并告知用户JobID

// 告知用户JobID：表格样式 
$style_table = "width: 1296px; text-align: center; line-height: 50px; border-collapse: collapse;"; // 表格样式
$style_odd = "background-color: #F7F7F7;";  // 表格奇数行的样式
$style_line = "border-right: 1px solid #c0c0c0; width: 648px;";  // 中间的竖线

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
                <td class='line' style='$style_line'>Gene Nomenclature</td>
                <td>$geneIDType</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Input Data Type</td>
                <td>$inputType</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Organism</td>
                <td>$organism</td>
            </tr>
            <tr class='odd' style='$style_odd'>
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


// 运行R命令
// cmd: Rscript mysql2TPM.R -g EnsemblID -i ./test_ensemblid_count2TPM.txt -o ./combined_ensembl_count_test.txt -d ReadCounts
setFilePermission($workdir, 0777);  // 增加
$infile = $workdir . "origin.txt";  // 处理前的文件
$workdir_result = $workdir."result";  // 一审
$dir = iconv("UTF-8", "GBK", $workdir_result );  # 一审
if (!file_exists($dir)){  # 一审
    mkdir($dir, 0777, true);
}
$outfile = $workdir_result . "/processed.txt";  // 处理后的文件  一审

// $outfile = $workdir . "processed.txt";  // 处理后的文件
// Fatal error: you must specify '--save', '--no-save' or '--vanilla'
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
$rfile = "code/mysql2TPM.R";
$param_g = " -g ".$geneIDType;
$param_d = " -d ".$inputType;
$param_r = " -r ".$organism;
$param_i = " -i ".$infile;
$param_o = " -o ".$outfile;
$param_a = " -a ".$jobID;  # 增加
$param_h = " -h none";
// $cmd = "". $rscript . " ". $rfile. $param_g. $param_a. $param_d. $param_r. $param_i. $param_o. $param_h. " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &
$cmd = "". $rscript . " ". $rfile. $param_a. $param_g. $param_d. $param_r. $param_i. $param_o. " > " . $workdir_result . "/terminal_msg.txt 2>&1 ";  // 一审

// 加载信息Config
$myFile = fopen($workdir . 'config.txt', 'w') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);


while (true){  // 增加
    if (file_exists($infile)){
        // 文件已存在或者等待时间大于十秒，跳出循环
        break;
    }
    sleep(0.2); // 暂停 0.2 秒后继续检测
}
// 修改文件权限
setFilePermission($infile, 0777);
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
        if (file_exists($outfile)){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }
    setFilePermission($outfile, 0777);
    
    // 显示下载结果页面
    $zipFilePath = $workdir_result.".zip";  # 一审
    make_zip_file_for_folder($zipFilePath, $workdir_result);  # 一审
    $download_name = $jobID . '.zip';  # 一审, ！！！一审还要修改187行的超链接！！！！！！！！！！！！！！！！！！！
    
    // $download_name = $jobID . '.txt';
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo "
    <section id='banner'>
        <div class='container padding-medium-2'>
            <div class='hero-content'>
                <!-- <h2 class='display-2 fw-semibold'>About <span class='text-primary'> Us</span></h2> -->
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
                    <td class='line' style='$style_line'>Gene Nomenclature</td>
                    <td>$geneIDType</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Input Data Type</td>
                    <td>$inputType</td>
                </tr>
                <tr>
                    <td class='line' style='$style_line'>Organism</td>
                    <td>$organism</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Data Process Result</td>
                    <td><a href='download.php?file=" . urlencode($zipFilePath) . "' class='btn btn-primary btn-primary-lin-height'>download</a></td>
                </tr>
            </table>
        </div>
    </section>";

}else{
    // 显示处理失败信息
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
    echo "
    <section id='banner'>
        <div class='container padding-medium-2'>
            <div class='hero-content'>
                <!-- <h2 class='display-2 fw-semibold'>About <span class='text-primary'> Us</span></h2> -->
                <h2 class='display-2 fw-semibold'>Result</span></h2>
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
                    <td class='line' style='$style_line'>Gene Nomenclature</td>
                    <td>$geneIDType</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Input Data Type</td>
                    <td>$inputType</td>
                </tr>
                <tr>
                    <td class='line' style='$style_line'>Organism</td>
                    <td>$organism</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Data Process Result</td>
                    <td>Processing failure!</td>
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
        // $mail->Body    = "<p>Dear user, <br />Your JobID is $jobID. To download processed data, please click: <a href='$outfile'>Link</a>" ."<br /></p>". date('Y-m-d H:i:s');
        $mail->Body    = "<p>Dear user, <br />Your JobID is $jobID. Your data has been processed successfully, and the processed data is attached. <br />Thank you for using our service.<br /></p>". date('Y-m-d H:i:s');
       
        // $mail->AltBody = '如果邮件客户端不支持HTML则显示此内容';
        // $mail->AltBody = "Dear user, your JobID is $jobID, you can enter $jobID via 'CheckJob' function to obtain your result.";
        $mail->AddAttachment($zipFilePath, $download_name);  // 添加附件
        $mail->send();
        // echo '邮件发送成功';
    } catch (Exception $e) {
        echo '邮件发送失败: ', $mail->ErrorInfo;
    }

}}

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

// 一审 增加压缩文件夹功能
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

include __DIR__ . '/footer.php';
