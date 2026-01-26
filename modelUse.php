<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';
require './table/renderer.php';
require './table/renderer_2.php';

set_time_limit(0);
// 显示等待页面（转圈圈）
// 嵌入Python脚本

// $modelTypes = array("CNN", "LSTM", "RNN", "MLP", "AutoEncoder", "Transformer", "SOM", "RBFN");
$modelTypes = array("CNN", "LSTM", "RNN", "MLP", "AutoEncoder", "Transformer", "SOM", "RBFN", "VAE", "DeepCluster", "LadderNetwork", "Pseudo-Labeling");  # 一审

$modelType_index = $_POST["model_type"];  // 获取option
$modelType = $modelTypes[$modelType_index];  // 模型类型：CNN
// 一审
if ($modelType_index == 6){
    $codeType = "som";  // 运行的代码名称 som.py
}else if ($modelType_index == 8){
     $codeType = "predict_vae";
}else if ($modelType_index == 9){
     $codeType = "predict_deepcluster";
}else if ($modelType_index == 10){
     $codeType = "predict_ladder";
}else if ($modelType_index == 11){
     $codeType = "predict_pseudo";
}else{
    $codeType = "general";  // 运行的代码名称 general.py
}

// if ($modelType_index == 6){
//     $codeType = "som";  // 运行的代码名称 som.py
// }else if ($modelType_index == 4){
//     $codeType = "autoencoder";   // 运行的代码名称 autoencoder.py
// }else{
//     $codeType = "general";  // 运行的代码名称 general.py
// }


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

// 测试集
$fileInfo = $_FILES["upload_file_1"];  //获取上传文件对应的字典（对象  Array类型
$filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
move_uploaded_file($filePath, $workdir . $jobID . '_test.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

// // 模型
// $fileInfo = $_FILES["upload_file_2"];  //获取上传文件对应的字典（对象  Array类型
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . 'model.pt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t



if ($modelType_index == 6){  // som模型专用
    $fileInfo = $_FILES["upload_file_6"];  //获取上传文件对应的字典（对象  Array类型
    $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
    move_uploaded_file($filePath, $workdir . 'model.pth');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

    $fileInfo = $_FILES["upload_file_3"];  //获取上传文件对应的字典（对象  Array类型
    $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
    move_uploaded_file($filePath, $workdir . 'winmap.pkl');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

    while (true){
        if (file_exists($workdir . 'model.pth') && file_exists($workdir . 'winmap.pkl')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }

}elseif ($modelType_index == 4){  // autoencoder模型专用
    $fileInfo = $_FILES["upload_file_4"];  //model_autoencoder.pt
    $filePath = $fileInfo["tmp_name"];  
    move_uploaded_file($filePath, $workdir . 'model_autoencoder.pth');

    $fileInfo = $_FILES["upload_file_5"]; 
    $filePath = $fileInfo["tmp_name"];  
    move_uploaded_file($filePath, $workdir . 'model_cls.pth');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

    while (true){
        if (file_exists($workdir . 'model_autoencoder.pth') && file_exists($workdir . 'model_cls.pth')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }

}elseif ($modelType_index == 8 || $modelType_index == 9 || $modelType_index == 10 || $modelType_index == 11){
    // 一审
    $fileInfo = $_FILES["upload_file_6"];  //model_autoencoder.pt
    $filePath = $fileInfo["tmp_name"];  
    move_uploaded_file($filePath, $workdir . 'scaler.pkl');

    $fileInfo = $_FILES["upload_file_7"]; 
    $filePath = $fileInfo["tmp_name"];  
    move_uploaded_file($filePath, $workdir . 'model.pth');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

    while (true){
        if (file_exists($workdir . 'model.pth') && file_exists($workdir . 'scaler.pkl')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }

}else{// 其他模型通用
    
    $fileInfo = $_FILES["upload_file_2"];  //获取上传文件对应的字典（对象  Array类型
    $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
    move_uploaded_file($filePath, $workdir . 'model.pth');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t

    while (true){
        if (file_exists($workdir . 'model.pth')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }

}


$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n from modelUse php");
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
                <td class='line' style='$style_line'>Model</td>
                <td>$modelType</td>
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

while (true){
    if (file_exists($workdir . $jobID . '_test.txt')){
        // 文件已存在，跳出循环
        break;
    }
    sleep(0.2); // 暂停 1 秒后继续检测
}


// 运行Python命令
$python3 = "/opt/anaconda/envs/automata/bin/python";
if ($$modelType != "SOM"){
    $pyfile = "/xp/www/AutoMATA/code/use_model/".$codeType.".py"; // D:\wamp\www\multi_omics_own\code\cnn.py
}else{
    $pyfile = "/xp/www/AutoMATA/code/use_model/som.py";
}
$outfile = $workdir_result . "/terminal.log";  // 输出终端打印数据到terminal.log文件中

$param_jobID = " --jobID ".$jobID;
$param_model = " --model_type ".$modelType;
// 一审
if ($modelType_index == 8 || $modelType_index == 9 || $modelType_index == 10 || $modelType_index == 11){
    $param_model = " --model_path ".$workdir . 'model.pth';
    $param_scaler = " --scaler_path ".$workdir .'scaler.pkl';
    $param_data = " --data_path ".$workdir . $jobID . '_test.txt';
    $param_output = " --output_path ".$workdir_result."/test_result";
    $cmd = "" . $python3 ." ".$pyfile. $param_model.$param_scaler.$param_data.$param_output." > " .$outfile." 2>&1 &";
}else{
    $param_model = " --model_type ".$modelType;
    $cmd = "" . $python3 ." ".$pyfile. $param_jobID.$param_model." > " .$outfile." 2>&1 &";
}

// $param_jobID = " --jobID ".$jobID;
// $param_model = " --model_type ".$modelType;
// $cmd = "" . $python3 ." ".$pyfile. $param_jobID.$param_model." > " .$outfile." 2>&1 &";


// 加载信息Config
$myFile = fopen($workdir. 'config.txt', 'w') or die("Unable to open config file!");
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

    while (true){
        if (file_exists($workdir_result."/test_result.txt") || file_exists($workdir_result."/test_result_latent_logvar.npy")){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
    // 压缩文件夹$workdir_result，以给用户下载
    $zipFilePath = $workdir_result.".zip";
    make_zip_file_for_folder($zipFilePath, $workdir_result);
    // 设置执行权限0777 供用户下载
    setFilePermission($zipFilePath, 0777);

    // 显示下载结果页面
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
                    <td class='line' style='$style_line'>Model</td>
                    <td>$modelType</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Model Using Results</td>
                    <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($zipFilePath) . "'>download</a></td>
                </tr>
                <tr>
                    <td class='line' style='$style_line'>Note</td>
                    <td>
                        <div class='notes'>
                            <p style='$style_text'><strong style='$style_strong'>test_metrics_result.txt</strong>  is the test metrics result file, which contains the metrics of the model on the test set.</p>
                            <p style='$style_text'><strong style='$style_strong'>test_result.txt</strong> is the test result file. Using the model you uploaded to predict the test set.</p>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
    </section>";
    
    if (file_exists($workdir_result."/test_result.txt")){
        setFilePermission($workdir_result . '/test_result.txt', 0777);
        try {  // 用绝对路径
            $filePath = '/xp/www/AutoMATA/'.$workdir_result . '/test_result.txt';
            echo renderOntologyTable_2($filePath, 'test_result.txt');
        } catch (Exception $e) {
            echo "Error: " . $e->getMessage();
        }
    }
    

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
                    <td class='line' style='$style_line'>Model</td>
                    <td>$modelType</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Model Training Results</td>
                    <td>Testing failure!</td>
                </tr>
            </table>
        </div>
    </section>";
}



// $email
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
        $mail->AddAttachment($zipFilePath, "result.zip"); // 附件的路径和名称

        $mail->send();
        // echo '邮件发送成功';
    } catch (Exception $e) {
        echo '邮件发送失败: ', $mail->ErrorInfo;
    }

}

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


include __DIR__ . '/footer.php';
