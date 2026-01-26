

<?php
// include __DIR__ . '/header.php';
// header('Content-Type: image/png');

// if (extension_loaded('gd')) {
//     echo 'GD库已安装';  // 已安装
// } else {
//     echo 'GD库未安装';
// }


// $workdir_result = "download_data/Jobs/20250416102823_4wHCGM4j/result/figure.png"; // 用相对路径
// // echo '<img src="images/background.png" alt="img" class="img-fluid">';
// if (file_exists($workdir_result)) {
//     echo '文件存在';
//     // echo '<img src="$workdir_result"  height="400px" />';
//     echo "<img src='$workdir_result?t=" . time() . "' height='400px'>";  // 避免浏览器缓存旧版本图片。
//     // echo "<img src='download_data/Jobs/20250416102823_4wHCGM4j/result/figure.png?t=" . time() . "' height='400px'>";  // 出现图片
// } else {
//     echo '图片文件不存在';
// }
// error_reporting(E_ALL);
// ini_set('display_errors', 1);
// // $workdir_result = "/xp/www/AutoMATA/download_data/Jobs/20250416102823_4wHCGM4j/result";
// $workdir_result = "download_data/Jobs/20250416102823_4wHCGM4j/result";
// echo "<img src='$workdir_result/figure.png?t=" . time() ." ' height='400px'>";  // 可以直接显示
// echo "<li><a href='download.php?file=" . urlencode($workdir_result."/figure.png") . "' class='dropdown-item'>PDF</a></li>";  //这样下载图片
// $workdir_result = "download_data/Jobs/20250416102823_4wHCGM4j";
// echo "<a href='download.php?file=" . urlencode($workdir_result."/20250416102823_4wHCGM4j_test.txt") . "' class='btn btn-primary btn-primary-lin-height'>dowload</a>";


$workdir = "download_data/Jobs/"."20250424195118_wQvcf5pI"."/";
setFilePermission($workdir, 0777);

// $jobID = "test_genome";
$organism = "homo_sapiens";
$inputType = "FPKM";
$geneIDType = "GeneID";
$infile = $workdir . "origin.txt";  // 处理前的文件
$outfile = $workdir . "processed.txt";  // 处理后的文件
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
$rfile = "/xp/www/AutoMATA/code/mysql2TPM.R";
$param_g = " -g ".$geneIDType;
$param_d = " -d ".$inputType;
$param_r = " -r ".$organism;
$param_i = " -i ".$infile;
$param_o = " -o ".$outfile;
// $param_a = " -a ".$jobID;  # 增加
// $param_h = " -h none";
while (true){  // 修改6
    if (file_exists($infile)){
        // 文件已存在，跳出循环
        echo "finish";
        break;
    }
    echo "continue";
    sleep(1); // 暂停 0.2 秒后继续检测
}
setFilePermission($infile, 0777);

// $cmd = "". $rscript . " ". $rfile. $param_g. $param_a. $param_d. $param_r. $param_i. $param_o. $param_h. " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &
$cmd = "". $rscript . " ". $rfile. $param_g. $param_d. $param_r. $param_i. $param_o. $param_h;  // &
echo $cmd;
system($cmd, $ret);

if ($ret == 0){
    echo "ret = 0";

}else{
    echo "failure";
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
    else
    echo "true modify permissions";
    
}
// header('Content-Type: image/png');
// imagepng($workdir_result); // 输出图像
// imagedestroy($workdir_result); // 释放内存
// exit(); // 终止脚本，避免额外输出
// echo '<img src="$workdir_result" />';
// ob_start();
// header('Content-Type: image/png');
// echo ob_get_contents();
// ob_end_clean();

// echo "<img src='$workdir_result' height='400px'>";

// 修改文件权限
// chmodr('/xp/www/AutoMATA/download_data/Jobs/20250415144031_VEPduZxq/result/autoencoder/terminal.log', 0777);
// function chmodr($path, $filemode) {

//     if (!is_dir($path))
//     return chmod($path, $filemode);
//     $dh = opendir($path);
//     while (($file = readdir($dh)) !== false) {
//     if($file != '.' && $file != '..') {
//     $fullpath = $path.'/'.$file;
//     if(is_link($fullpath))
//     return FALSE;
//     elseif(!is_dir($fullpath) && !chmod($fullpath, $filemode))
//     return FALSE;
//     elseif(!chmodr($fullpath, $filemode))
//     return FALSE;
//     }
//     }
//     closedir($dh);
//     if(chmod($path, $filemode))
//     echo "true";
//     else
//     echo "false";
//     }

// 发邮件
// use PHPMailer\PHPMailer\PHPMailer;
// use PHPMailer\PHPMailer\Exception;

// require './PHPMailer/PHPMailer/src/Exception.php';
// require './PHPMailer/PHPMailer/src/PHPMailer.php';
// require './PHPMailer/PHPMailer/src/SMTP.php';

// $mail = new PHPMailer(true);                              // Passing `true` enables exceptions
// try {
//     //服务器配置
//     $mail->CharSet ="UTF-8";                     //设定邮件编码
//     $mail->SMTPDebug = 0;                        // 调试模式输出
//     $mail->isSMTP();                             // 使用SMTP
//     $mail->Host = 'smtp.163.com';                // SMTP服务器
//     $mail->SMTPAuth = true;                      // 允许 SMTP 认证
//     $mail->Username = 'wanger0808@163.com';                // SMTP 用户名  即邮箱的用户名
//     $mail->Password = 'DYHQMFHAHHIEEEUZ';             // SMTP 密码  部分邮箱是授权码(例如163邮箱)
//     $mail->SMTPSecure = 'ssl';                    // 允许 TLS 或者ssl协议
//     $mail->Port = 465;                            // 服务器端口 25 或者465 具体要看邮箱服务器支持

//     $mail->setFrom('wanger0808@163.com', 'Mailer');  //发件人
//     $mail->addAddress('1309316202@qq.com', 'Joe');  // 收件人
//     //$mail->addAddress('ellen@example.com');  // 可添加多个收件人
//     $mail->addReplyTo('wanger0808@163.com', 'info'); //回复的时候回复给哪个邮箱 建议和发件人一致
//     //$mail->addCC('cc@example.com');                    //抄送
//     //$mail->addBCC('bcc@example.com');                    //密送

//     //发送附件
//     // $mail->addAttachment('../xy.zip');         // 添加附件
//     // $mail->addAttachment('../thumb-1.jpg', 'new.jpg');    // 发送附件并且重命名

//     //Content
//     $mail->isHTML(true);                                  // 是否以HTML文档格式发送  发送后客户端可直接显示对应HTML内容
//     // $mail->Subject = '这里是邮件标题' . time();  // 这里是邮件标题1723129210
//     $mail->Subject = 'Multi Omics Result';
//     $mail->Body    = '<h1>这里是邮件内容</h1>' . date('Y-m-d H:i:s');
//     $mail->AltBody = '如果邮件客户端不支持HTML则显示此内容';

//     $mail->send();
//     echo '邮件发送成功';
// } catch (Exception $e) {
//     echo '邮件发送失败: ', $mail->ErrorInfo;
// }

// include __DIR__ . '/footer.php';


