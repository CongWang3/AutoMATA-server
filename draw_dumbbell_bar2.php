<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';


// 显示等待页面（转圈圈）
// 嵌入R脚本
set_time_limit(0);  // 修改1
// 参数
$x_label = $_POST["x_label"];
$mark_fams = $_POST["mark_fams"];


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
// 数据集
$fileInfo = $_FILES["upload_file_1"];  //获取上传文件对应的字典（对象  Array类型 
$filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
move_uploaded_file($filePath, $workdir . $jobID . '_data1.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
$fileInfo = $_FILES["upload_file_2"];  //获取上传文件对应的字典（对象  Array类型 
$filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
move_uploaded_file($filePath, $workdir . $jobID . '_data2.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

// print_r($fileInfo);
$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n from draw_dumbbbell_bar2 php");
    fclose($myFile);
}

// 运行 R代码并告知用户JobID
// 告知用户JobID：表格样式 
$style_table = "width: 1296px; text-align: center; line-height: 50px; border-collapse: collapse;"; // 表格样式
$style_odd = "background-color: #F7F7F7;";  // 表格奇数行的样式
$style_line = "border-right: 1px solid #c0c0c0; width: 648px;";  // 中间的竖线
echo"
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
                <td class='line' style='$style_line'>Plot Type</td>
                <td>Dumbbell Plot</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Label for the x-axis</td>
                <td>$x_label</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Emphatic term</td>
                <td>$mark_fams</td>
            </tr>
            <tr class='odd' style='$style_odd'>
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

// 运行R命令
// cmd: Rscript cor_heatmap.r -i cor_heatmap_example.txt
$infile = $workdir . $jobID . '_data.txt';  # 数据路径
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
$rfile = "./code/data_analysis_plot/dumbbell_bar.R";
$param_i = " -i ".$infile;
$param_j = " -j ".$jobID;
$param_a = " -a ".$x_label;
$param_b = " -b ".$mark_fams;
$param_c = " -c ".$infile;  // 随便整个 因为R脚本里会修改文件名
if ($x_label != "" && $mark_fams != ""){
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_b. $param_a. $param_c. " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &
}elseif($x_label=="" && $mark_fams!=""){
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_b. $param_c.  " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &

}elseif($x_label!="" && $mark_fams==""){
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_a. $param_c.  " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &

}else{  //都没有
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_c.  " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &

}
// 加载信息Config
$administrator_workdir = "/xp/www/AutoMATA/download_data/";
$myFile = fopen($administrator_workdir . 'Jobs/' . $jobID . '/config.txt', 'w') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);
while (true){
    if (file_exists($workdir . $jobID . '_data1.txt') && file_exists($workdir . $jobID . '_data2.txt')){
        // 文件已存在，跳出循环
        break;
    }
    sleep(1); // 暂停 1 秒后继续检测
}
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
        if (file_exists($workdir_result.'/dumbbell_bar.svg')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
    // 修改文件权限 修改7
    setFilePermission($workdir_result, 0777);

    // 显示下载结果页面
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo"
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
                <td class='line' style='$style_line'>Plot Type</td>
                <td>Dumbbell Plot</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Label for the x-axis</td>
                <td>$x_label</td>
            </tr>
            <tr style='border-bottom: 1px solid #cdcdcd;'>
                <td class='line' style='$style_line'>Emphatic term</td>
                <td>$mark_fams</td>
            </tr>
            <tr>
                <td style='border-right: 1px solid #c0c0c0; line-height: 450px;'><img src='$workdir_result/dumbbell_bar.png?t=" . time() ." ' height='400px'></td>
                <td>
                    <div class='dropdown' style='display: flex; justify-content: space-around;'>
                        <button class='dropdown-toggle btn btn-primary' data-bs-toggle='dropdown' id='courses' role='button' style='display: flex; align-items: center'><i class='material-icons'>file_download</i>Download Figure</button>
                        <div class='dropdown-menu' aria-labelledby='courses'>
                            <li><a href='download.php?file=" . urlencode($workdir_result."/dumbbell_bar.pdf") . "' class='dropdown-item'>PDF</a></li>
                            <li><a href='download.php?file=" . urlencode($workdir_result."/dumbbell_bar.png") . "' class='dropdown-item'>PNG</a></li>
                            <li><a href='download.php?file=" . urlencode($workdir_result."/dumbbell_bar.svg") . "' class='dropdown-item'>SVG</a></li>
                            <li><a href='download.php?file=" . urlencode($workdir_result."/dumbbell_bar.tiff") . "' class='dropdown-item'>TIFF</a></li>
                            <li><a href='download.php?file=" . urlencode($workdir_result."/dumbbell_bar.jpeg") . "' class='dropdown-item'>JPEG</a></li>
                            <li><a href='download.php?file=" . urlencode($workdir_result."/dumbbell_bar.bmp") . "' class='dropdown-item'>BMP</a></li>
                        </div>
                    </div>
                </td>             
            </tr>
        </table>
    </div>
</section>
    ";
}else{ // 显示处理失败信息
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo"
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
                <td class='line' style='$style_line'>Plot Type</td>
                <td>Dumbbell Plot</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Label for the x-axis</td>
                <td>$x_label</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Emphatic term</td>
                <td>$mark_fams</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Plot</td>
                <td>Image generation failure!</td>
            </tr>
        </table>
    </div>
</section>
    
    ";
}




// $email
if ($ret == 0){
$email = $_POST["email"];
if ($email != ""){
    // 压缩文件夹$workdir_result，以给用户下载
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

// echo "<p>$geneIDType, $inputType, $organism </p>";

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

