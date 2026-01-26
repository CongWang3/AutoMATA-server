<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';


// 显示等待页面（转圈圈）
// 嵌入Python脚本

// 记得添加修改权限功能啊！！
$kfold = "0";  # 记得调整上传方式啊！kfold / split / 单独上传训练测试验证集
$ratio = "0";  # 记得调整上传方式啊！kfold / split / 单独上传训练测试验证集

$codeTypes = array("ladder", "pseudo");
$modelTypes = array("LadderNetwork", "Pseudo-Labeling");
$modelType_index = $_POST["model_type"];  // 获取option
$modelType = $modelTypes[$modelType_index];  // 模型类型：CNN
$codeType = $codeTypes[$modelType_index];  // 运行的代码名称 VAE.py
// if ($modelType_index != 8){
//     $codeType = $codeTypes[$modelType_index];  // 运行的代码名称 cnn.py
// }
$epoch = $_POST["epoch"];  // 字符串类型
$lr = $_POST["lr"];
$es = $_POST["es"];
$bs = $_POST["bs"];  // batch_size
$seed = $_POST["seed"];
$alpha = $_POST["alpha"];

if ($modelType_index == 0){
    // ladder
    $All_loss = array("semi_supervised", "focal", "label_smoothing", "contrastive");
    $lossType_index = $_POST["loss_type_ladder"];
    $loss = $All_loss[$lossType_index];
    $All_loss = array("Semi-Supervised Loss", "Focal Loss", "Label Smoothing Loss", "Contrastive Loss");
    $loss_write = $All_loss[$lossType_index];  // 损失函数名称：CrossEntropyLoss 写在web页面上
}else if ($modelType_index == 1){
    // pesudo
    $All_loss = array("pseudo_label", "focal", "label_smoothing");
    $lossType_index = $_POST["loss_type_pseudo"];
    $loss = $All_loss[$lossType_index];
    $All_loss = array("Pseudo Labeling Loss", "Focal Loss", "Label Smoothing Loss");
    $loss_write = $All_loss[$lossType_index];
}


$opzType_index = $_POST["opz_type"];  // 获取优化器option
$All_opz = array("adam", "sgd", "adamw", "rmsprop");
$opz = $All_opz[$opzType_index];  // 优化器 传入脚本中
$All_opz = array("Adam", "SGD", "AdamW", "RMSprop");
$opz_write = $All_opz[$opzType_index];  // 优化器 写在web页面上

// echo $labels,$loss,$optimizer;

// 设置JobID
date_default_timezone_set('Asia/Shanghai');
$jobID = date("YmdHis") . '_' . make_char(); // 时间作为job_id

// 转移用户上传的文件到 download_data/Jobs/JobID.txt 中
$workdir = "/xp/www/AutoMATA/download_data/Jobs/".$jobID."/";
$dir = iconv("UTF-8", "GBK", $workdir );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}

$workdir_result = $workdir."result";  // 放模型训练结果的文件夹
$dir = iconv("UTF-8", "GBK", $workdir_result );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
if (!file_exists($dir)){
    mkdir($dir, 0777, true);
}

$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n  from modelTrain_semi php");
    fclose($myFile);
}

// 运行python代码并告知用户JobID
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
                <td class='line' style='$style_line'>Model Type</td>
                <td>$modelType</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Epoch</td>
                <td>$epoch</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Learning Rate</td>
                <td>$lr</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>EarlyStopping Patience</td>
                <td>$es</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Batch Size</td>
                <td>$bs</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Random Seed</td>
                <td>$seed</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Loss Function</td>
                <td>$loss_write</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Optimizer</td>
                <td>$opz_write</td>
            </tr>";
echo $basic_info;
            echo "
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

// 判断上传类型
if ($_POST["strategy"] == "upload"){
    // 上传三个数据集
    $kfold = "0";
    $ratio = "0";
    // 训练集
    $fileInfo = $_FILES["upload_file_1"];  //获取上传文件对应的字典（对象  Array类型 
    $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
    move_uploaded_file($filePath, $workdir . $jobID . '_data.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t  文件名train改为data
    // 验证集
    $fileInfo = $_FILES["upload_file_2"];
    $filePath = $fileInfo["tmp_name"];
    move_uploaded_file($filePath, $workdir . $jobID . '_val.txt'); 
    // 测试集
    $fileInfo = $_FILES["upload_file_3"]; 
    $filePath = $fileInfo["tmp_name"];
    move_uploaded_file($filePath, $workdir . $jobID . '_test.txt'); 

    while (true){
        if (file_exists($workdir . $jobID . '_data.txt') && file_exists($workdir . $jobID . '_val.txt') && file_exists($workdir . $jobID . '_test.txt')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
}elseif ($_POST["strategy"] == "split") {
    // 分割数据集
    $kfold = "0";
    $ratio = $_POST["ratio"];
    $fileInfo = $_FILES["upload_file_4"];  //获取上传文件对应的字典（对象  Array类型 
    $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
    move_uploaded_file($filePath, $workdir . $jobID . '_data.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t  文件名train改为data
    while (true){
        if (file_exists($workdir . $jobID . '_data.txt')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
}else{
    // KFold
    $kfold = $_POST["kfold"];
    $ratio = "0";
    // 训练集
    $fileInfo = $_FILES["upload_file_5"];
    $filePath = $fileInfo["tmp_name"]; 
    move_uploaded_file($filePath, $workdir . $jobID . '_data.txt');
    // 测试集
    $fileInfo = $_FILES["upload_file_6"];
    $filePath = $fileInfo["tmp_name"]; 
    move_uploaded_file($filePath, $workdir . $jobID . '_test.txt');
    while (true){
        if (file_exists($workdir . $jobID . '_data.txt') && file_exists($workdir . $jobID . '_test.txt')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
}

// // 训练集
// $fileInfo = $_FILES["upload_file_1"];  //获取上传文件对应的字典（对象  Array类型 
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . $jobID . '_data.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t  文件名train改为data
// // 验证集
// $fileInfo = $_FILES["upload_file_2"];  
// if($fileInfo["name"] != ""){
//     $kfold = "0"; // 整数还是字符
//     $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
//     move_uploaded_file($filePath, $workdir . $jobID . '_val.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
// }else{
//     $kfold = $_POST["kfold"];  // 使用kfold交叉验证
// }
// // 测试集
// $fileInfo = $_FILES["upload_file_3"];  //获取上传文件对应的字典（对象  Array类型
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . $jobID . '_test.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
// // print_r($fileInfo);


// 运行Python命令
$python3 = "/opt/anaconda/envs/automata/bin/python";
// $python3 = "D:/Anaconda3/python";  // 用where python找python.exe在哪。太诡异了，pt36的python找不着了，现在用的python路径和base环境的一样
$pyfile = "/xp/www/AutoMATA/code/train_model/".$codeType.".py"; // D:\wamp\www\multi_omics_own\code\cnn.py
// cmd: python ./code/cnn.py --jobID 20240808232043_OtJF37SH --kfold 0 --epochs 10 --es 10 --lr 0.1
$outfile = $workdir_result . "/terminal.log";  // 输出终端打印数据到terminal.log文件中
$param_jobID = " --jobid ".$jobID;
$param_kfold = " --k_folds ".$kfold;
$param_epochs = " --epochs ".$epoch;
$param_es = " --early_stopping_patience ".$es;
$param_lr = " --learning_rate ".$lr;
$param_bs = " --batch_size ".$bs;
$param_loss = " --loss_function ".$loss;
$param_opz = " --optimizer_function ".$opz;
$param_seed = " --random_seed ".$seed;
$param_ratio = " --ratio ".$ratio;
$param_model_path = " --model_path ".$workdir_result."/model.pth";
$param_scaler = " --scaler_path ".$workdir_result."/scaler.pkl";
$param_test_path = " --evaluation_path ".$workdir_result."/test_result.png";
$param_alpha = " --alpha ".$alpha;

if ($modelType_index == 0){
    // ladder
    $beta = $_POST["beta"];
    $gamma = $_POST["gamma"];
    $param_beta = " --beta ".$beta;
    $param_gamma = " --gamma ".$gamma;
    $cmd = "" . $python3 ." ".$pyfile. $param_jobID.$param_kfold.$param_epochs.$param_es.$param_lr.$param_bs.$param_loss.$param_opz.$param_seed.$param_ratio.$param_model_path.$param_scaler.$param_test_path.$param_beta.$param_gamma.$param_alpha." > " .$outfile." 2>&1 &";
}else if ($modelType_index == 1){
    // pesudo
    $beta = $_POST["pseudo_beta"];
    $conf_threshold = $_POST["threshold"];
    $pseudo_ratio = $_POST["pseudo_ratio"];
    $param_beta = " --beta ".$beta;
    $param_conf_threshold = " --confidence_threshold ".$conf_threshold;
    $param_pseudo_ratio = " --pseudo_ratio ".$pseudo_ratio;
    $cmd = "" . $python3 ." ".$pyfile. $param_jobID.$param_kfold.$param_epochs.$param_es.$param_lr.$param_bs.$param_loss.$param_opz.$param_seed.$param_ratio.$param_model_path.$param_scaler.$param_test_path.$param_beta.$param_conf_threshold.$param_pseudo_ratio.$param_alpha." > " .$outfile." 2>&1 &";

}

// 加载信息Config
$administrator_workdir = "/xp/www/AutoMATA/download_data/";
$myFile = fopen($administrator_workdir . 'Config/' . $jobID . '_config.txt', 'w') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);
system($cmd, $ret);

if ($ret == 0){  // 运行成功
    while (true){
        if (file_exists($workdir_result."/test_result.json")){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }

    // 压缩文件夹$workdir_result，以给用户下载
    $zipFilePath = $workdir_result.".zip";
    make_zip_file_for_folder($zipFilePath, $workdir_result);
    // 设置执行权限0777 供用户下载
    setFilePermission($zipFilePath, 0777);
    setFilePermission($workdir_result, 0777);  // 修改文件夹中所有文件权限


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

    // 显示下载结果页面
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
                    echo "
                <tr>
                    <td class='line' style='$style_line'>Model Training Results</td>
                    
                    <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($zipFilePath) . "'>download</a></td>

                </tr>
                ";
                
                echo "
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Training Log</td>
                    <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($outfile) . "'>download</a></td>

                </tr>
            </table>
        </div>
    </section>";

}else{
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

    // 显示处理失败信息
    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
    echo "
                <tr>
                    <td class='line' style='$style_line'>Model Training Results</td>
                    <td>Training failure!</td>
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
        $mail->Body    = "<p>Dear user, <br/>Your JobID is $jobID. "."Your model training results are attached."."<br /></p>". date('Y-m-d H:i:s');
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
