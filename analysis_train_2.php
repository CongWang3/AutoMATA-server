<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';
require './table/renderer.php';


// 显示等待页面（转圈圈）
// 嵌入R脚本
// set_time_limit(0); // 不限制时间
// 参数
$org = array("Homo_sapiens", "Bovine", "Mus_musculus", "Drosophila_melanogaster");
$organism = $org[$_POST["organism"]]; // "Homo_sapiens"
$fc = $_POST["fc"];
$padj = $_POST["padj"];
$data_types = array("read_counts", "fpkm");
$data_type = $data_types[$_POST["data_type"]];  // "read_counts", "fpkm"

$geneIDTypes = array("GeneID", "EnsemblID", "Symbol");
$geneIDType_index = $_POST["geneMomen"];  // 获取option的value. 0=Gene ID, 1=Ensemble Gene ID, 2=Gene Symbol
$geneIDType = $geneIDTypes[$geneIDType_index];  // 

$codeTypes = array("cnn", "lstm", "rnn", "mlp", "autoencoder", "transformer", "som", "rbfn");
$modelTypes = array("CNN", "LSTM", "RNN", "MLP", "AutoEncoder", "Transformer", "SOM", "RBFN", "all");
$modelType_index = $_POST["model_type"];  // 获取option
$modelType = $modelTypes[$modelType_index];  // 模型类型：CNN
if ($modelType_index != 8){
    $codeType = $codeTypes[$modelType_index];  // 运行的代码名称 cnn.py
}
$epoch = $_POST["epoch"];  // 字符串类型
$lr = $_POST["lr"];
$es = $_POST["es"];
$labels = $_POST["labels"];  // 多分类
$bs = $_POST["bs"];  // batch_size
$seed = $_POST["seed"];

$lossType_index = $_POST["loss_type"];  // 获取损失函数option
$All_loss = array("crossentropy", "focalloss", "nllloss");
$loss = $All_loss[$lossType_index];  // 损失函数名称：crossentropy 传入脚本中
$All_loss = array("CrossEntropyLoss", "FocalLoss", "NLLLoss");
$loss_write = $All_loss[$lossType_index];  // 损失函数名称：CrossEntropyLoss 写在web页面上

$opzType_index = $_POST["opz_type"];  // 获取优化器option
$All_opz = array("adam", "sgd", "rmsprop");
$opz = $All_opz[$opzType_index];  // 优化器 传入脚本中
$All_opz = array("Adam", "SGD", "RMSprop");
$opz_write = $All_opz[$opzType_index];  // 优化器 写在web页面上

$corres = array("BH", "BY", "holm", "hochberg", "hommel", "bonferroni", "none");  // 一审 新增
$correction = $corres[$_POST["correction"]];  // 一审 新增

// 设置JobID
date_default_timezone_set('Asia/Shanghai');
$jobID = date("YmdHis") . '_' .make_char(); // 时间作为job_id

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
    fwrite($myFile, "email: $email\n from analysis_train_2 php");
    fclose($myFile);
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
// $ratio = "0";
// // 测试集
// $fileInfo = $_FILES["upload_file_3"];  //获取上传文件对应的字典（对象  Array类型
// $filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
// move_uploaded_file($filePath, $workdir . $jobID . '_test.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
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

    // 复制文件为数据分析做准备。
    copy($workdir . $jobID . '_data.txt',$workdir . $jobID . '_data_origin.txt');
    while(true){
        if (file_exists($workdir . $jobID . '_data_origin.txt')){
            break;
        }
        sleep(0.2);
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





// 样本信息
$fileInfo = $_FILES["upload_file_info"];  //获取上传文件对应的字典（对象  Array类型 
$filePath = $fileInfo["tmp_name"];  // 获取上传文件保存的临时路径，return D:\wamp\tmp\phpD798.tmp
move_uploaded_file($filePath, $workdir . $jobID . '_info.txt');  // 移动文件 并保存为txt格式 文件的分割符号必须为\t
while (true){
    if (file_exists($workdir . $jobID . '_info.txt')){
        // 文件已存在，跳出循环
        break;
    }
    sleep(0.2); // 暂停 1 秒后继续检测
}


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
                <td class='line' style='$style_line'>Data Type</td>
                <td>$data_type</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Gene Nomenclature</td>
                <td>$geneIDType</td>
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
                <td class='line' style='$style_line'>Label Number</td>
                <td>$labels</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Loss Function</td>
                <td>$loss_write</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Optimizer</td>
                <td>$opz_write</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Organism</td>
                <td>$organism</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Log2(Fold Change) threshold</td>
                <td>$fc</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>padj threshold</td>
                <td>$padj</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Random Seed</td>
                <td>$seed</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Correction Method</td>
                <td>$correction</td>
            </tr>

";
ob_start(); // 启用输出缓冲
echo $basic_info;
echo"
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

// 1. 先用上传的数据直接训练模型
// 先训练 再转置训练数据以下一步分析
if ($modelType === "all"){
    // 读取每个模型文件夹中的test_result.txt，写一个结果表格
    // 初始化一个数组来存储所有test_result.txt数据
    $allData = [];

    // 加载信息Config
    $administrator_workdir = "/xp/www/AutoMATA/download_data/";
    $myFile = fopen($administrator_workdir . 'Config/' . $jobID . '_config.txt', 'a') or die("Unable to open config file!");

    foreach ($codeTypes as $model){
        // $model是每个模型类型
        // 建立文件夹
        $workdir_result_model = $workdir_result."/". $model;  // 放模型训练结果的文件夹  'D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\'+jobID+'\\result\\cnn\\'
        $dir = iconv("UTF-8", "GBK", $workdir_result_model );  # iconv方法是为了防止中文乱码，保证可以创建识别中文目录
        if (!file_exists($dir)){
            mkdir($dir, 0777, true);
        }
        // 运行每个模型
        $python3 = "/opt/anaconda/envs/automata/bin/python";
        $pyfile = "/xp/www/AutoMATA/code/train_model/".$model.".py"; // D:\wamp\www\multi_omics_own\code\cnn.py
        $outfile = $workdir_result_model . "/terminal_train.log";  // 输出终端打印数据到terminal.log文件中
        $param_jobID = " --jobID ".$jobID;
        $param_kfold = " --kfold ".$kfold;
        $param_ratio = " --ratio ".$ratio;
        $param_epochs = " --epochs ".$epoch;
        $param_es = " --es ".$es;
        $param_lr = " --lr ".$lr;
        $param_bs = " --bs ".$bs;
        $param_loss = " --loss_function ".$loss;
        $param_opz = " --optimizer_function ".$opz;
        $param_labels = " --output_size ".$labels;
        $param_seed = " --random_seed ".$seed;
        $param_type = " --type all";
        $cmd = "" . $python3 ." ".$pyfile. $param_jobID.$param_kfold.$param_seed.$param_ratio.$param_epochs.$param_lr.$param_bs.$param_loss.$param_opz.$param_labels.$param_type." > " .$outfile." 2>&1 &";
        
        // 写加载信息Config
        fputs($myFile, "command: $cmd\n");
        system($cmd, $ret_train);

        
        if ($ret_train != 0){
            // 显示处理失败信息

            // $con = mysqli_connect("localhost", "automata", "123456", "automata");
            // if (!$con) {
            //     echo "could not connect to mysql";
            //     die('Could not connect: ' . mysqli_connect_error());
            // }
            // $status = "Failed";
            // $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
            // if (!mysqli_query($con, $sql)) {
            //     die('Error: ' . mysqli_error($con));
            // }
            // mysqli_close($con);

            // ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
            // echo $basic_info;
            // echo "
            //             <tr>
            //                 <td class='line' style='$style_line'>Model Training Results</td>
            //                 <td>Training failure!</td>
            //             </tr>
            //         </table>
            //     </div>
            // </section>";
            // echo "Error: $model training failed.";
            // fclose($myFile);
            // exit(1);
        }

        else{

            while (true){
                if (file_exists($workdir_result_model."/test_result.txt")){
                    // 文件已存在，跳出循环
                    break;
                }
                sleep(1); // 暂停 1 秒后继续检测
            }

            // 压缩文件夹$workdir_result，以给用户下载 放在表格后面
            $zipFilePath = $workdir_result_model.".zip";
            make_zip_file_for_folder($zipFilePath, $workdir_result_model);
            // 设置执行权限0777 供用户下载
            setFilePermission($zipFilePath, 0777);
            setFilePermission($workdir_result_model."/test_result.txt", 0777);

            // 初始化一个数组来存储当前文件的数据
            $data = [
                'acc' => null,
                'precision' => null,
                'recall' => null,
                'f1' => null,
                'zip' => null,
            ];
            // 读取文件内容
            $fileContent = file_get_contents($workdir_result_model."/test_result.txt");
            $lines = explode("\n", $fileContent);  // 按行分割
            foreach ($lines as $line) {  // 遍历每一行
                if (strpos($line, 'acc = ') !== false) {
                    $data['acc'] = trim(str_replace('acc = ', '', $line));
                } elseif (strpos($line, 'precision = ') !== false) {
                    $data['precision'] = trim(str_replace('precision = ', '', $line));
                } elseif (strpos($line, 'recall = ') !== false) {
                    $data['recall'] = trim(str_replace('recall = ', '', $line));
                } elseif (strpos($line, 'f1 = ') !== false) {
                    $data['f1'] = trim(str_replace('f1 = ', '', $line));
                }
            }
            $data['zip'] = $zipFilePath;


            // 将当前文件夹的数据添加到总数据中
            $allData[] = [
                strtoupper($model), // 模型名称
                $data['acc'],
                $data['precision'],
                $data['recall'],
                $data['f1'],
                $data['zip'],
            ];

        }
    }
    unset($model);
    fclose($myFile);

}else{
    // single
    // 运行Python命令
    $python3 = "/opt/anaconda/envs/automata/bin/python";  // 用where python找python.exe在哪。太诡异了，pt36的python找不着了，现在用的python路径和base环境的一样
    $pyfile = "/xp/www/AutoMATA/code/train_model/".$codeType.".py"; // D:\wamp\www\multi_omics_own\code\cnn.py
    // cmd: python ./code/cnn.py --jobID 20240808232043_OtJF37SH --kfold 0 --epochs 10 --es 10 --lr 0.1
    $outfile = $workdir_result . "/terminal_train.log";  // 输出终端打印数据到terminal.log文件中
    $param_jobID = " --jobID ".$jobID;
    $param_kfold = " --kfold ".$kfold;
    $param_epochs = " --epochs ".$epoch;
    $param_es = " --es ".$es;
    $param_lr = " --lr ".$lr;
    $param_bs = " --bs ".$bs;
    $param_loss = " --loss_function ".$loss;
    $param_opz = " --optimizer_function ".$opz;
    $param_labels = " --output_size ".$labels;
    $param_seed = " --random_seed ".$seed;
    $param_ratio = " --ratio ".$ratio;
    $param_type = " --type single";
    $cmd = "" . $python3 ." ".$pyfile. $param_jobID.$param_kfold.$param_ratio.$param_seed.$param_epochs.$param_lr.$param_bs.$param_loss.$param_opz.$param_labels.$param_type." > " .$outfile." 2>&1 &";
    // 加载信息Config
    $administrator_workdir = "/xp/www/AutoMATA/download_data/";
    $myFile = fopen($administrator_workdir . 'Config/' . $jobID . '_config.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "command: $cmd\n");
    fclose($myFile);
    system($cmd, $ret_train);


    if ($ret_train != 0){
        // 显示处理失败信息
        // $con = mysqli_connect("localhost", "automata", "123456", "automata");
        // if (!$con) {
        //     echo "could not connect to mysql";
        //     die('Could not connect: ' . mysqli_connect_error());
        // }
        // $status = "Failed";
        // $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
        // if (!mysqli_query($con, $sql)) {
        //     die('Error: ' . mysqli_error($con));
        // }
        // mysqli_close($con);

        // ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
        // echo $basic_info;
        // echo "
        //             <tr>
        //                 <td class='line' style='$style_line'>Model Training Results</td>
        //                 <td>Training failure!</td>
        //             </tr>
        //         </table>
        //     </div>
        // </section>";
        // exit(1);
    }else{  // 运行成功
        while (true){
            if (file_exists($workdir_result."/test_result.txt")){
                // 文件已存在，跳出循环
                break;
            }
            sleep(1); // 暂停 1 秒后继续检测
        }
        
        // 压缩文件夹$workdir_result，以给用户下载 放在表格后面 
        // $zipFilePath = $workdir_result.".zip";
        $zipFilePath = $workdir."model_result.zip";  // 修改
        make_zip_file_for_folder($zipFilePath, $workdir_result);
        // 设置执行权限0777 供用户下载
        setFilePermission($zipFilePath, 0777);
        setFilePermission($workdir_result, 0777);  // 修改文件夹中所有文件权限

    }

}

// 2. 做ID conversion，为差异分析做准备。注意这时会把value转为log2(TPM+1)，不要log2(TPM+1)，要read count或FPKM
if ($_POST["strategy"] == "split"){
    // 改名
    while (true){  // 修改6
        if (rename($workdir . $jobID . '_data.txt', $workdir . $jobID . '_data_train.txt') && rename($workdir . $jobID . '_data_origin.txt', $workdir . $jobID . '_data.txt')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }
}

// 修改 ID -> Symbol
if ($geneIDType != "Symbol"){
    if ($organism == "Homo_sapiens"){
        $o = "homo_sapiens";
    }elseif ($organism == "Bovine"){
        $o = "bos_taurus";
    }elseif ($organism == "Mus_musculus"){
        $o = "mus_musculus";
    }else{
        $o = "drosophila_melanogaster";
    }

    // 修改文件权限
    setFilePermission($workdir, 0777);

    $infile = $workdir . $jobID . '_data.txt';  # 数据路径
    $outfile = $workdir . $jobID . '_data.txt';  # 输出路径
    
    $rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
    $rfile = "code/mysql2TPM.R";
    $param_g = " -g ".$geneIDType;
    $param_r = " -r ".$o;
    $param_i = " -i ".$infile;
    $param_o = " -o ".$outfile;
    $param_a = " -a ".$jobID;
}
if ($geneIDType == "GeneID"){
    // 替换organism bos_taurus
    $param_h = " -h "."GeneID";

    $cmd = "". $rscript . " ". $rfile. $param_g. $param_a. $param_h. $param_r. $param_i. $param_o. " > " . $workdir_result . "/terminal_msg_data_process.txt 2>&1 ";  // &
    $myFile = fopen($workdir . 'config.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "command: $cmd\n");
    fclose($myFile);
    system($cmd, $ret);

}elseif ($geneIDType == "EnsemblID"){
    $param_h = " -h "."EnsemblID";
    $cmd = "". $rscript . " ". $rfile. $param_g. $param_a. $param_h. $param_r. $param_i. $param_o. " > " . $workdir_result . "/terminal_msg_data_process.txt 2>&1 ";  // &
    $myFile = fopen($workdir . 'config.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "command: $cmd\n");
    fclose($myFile);
    system($cmd, $ret);
}

if ($ret == 0){// 运行成功
    while (true){  // 修改6
        if (file_exists($outfile)){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.2); // 暂停 1 秒后继续检测
    }
    setFilePermission($outfile, 0777);
}



// 3. 差异分析
// 分析数据
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript  --no-save ";
$expression_file = $workdir . $jobID . '_data.txt';  # 数据路径

// 修改数据内容，做转置并删除最后一行对数据文件
$lines = file($expression_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);  // 读取文件内容，忽略空行
if (empty($lines)) {
    die("The input file is empty or unreadable.");
}
// 将每行分割为以制表符分隔的数组，形成二维矩阵
$matrix = array_map(function($line) {
    return explode("\t", $line);
}, $lines);
// 转置矩阵（使用array_map和展开运算符）
$transposed = array_map(null, ...$matrix);
// 删除最后一行
array_pop($transposed);
// 将转置后的数据转换为字符串格式
$outputContent = implode("\n", array_map(function($row) {
    return implode("\t", $row);
}, $transposed));
// 写入输出文件
file_put_contents($expression_file, $outputContent);


// 运行分析脚本
$info_file = $workdir . $jobID . '_info.txt';  # 信息路径
if ($data_type == "read_counts"){
    $rfile = "code/DESeq2_read_count.R";
}else{
    $rfile = "code/limma_fpkm_df.R";
}
$param_i = " -i ".$expression_file;
$param_k = " -k ".$info_file;
$param_j = " -j ".$jobID;
$param_c = " -c ".$fc;
$param_d = " -d ".$padj;
$param_e = " -e ".$correction;
$cmd = "". $rscript . " ". $rfile. $param_i. $param_k. $param_e. $param_j. $param_c. $param_d. " > " . $workdir . "terminal_msg.txt 2>&1 ";  // &
// 加载信息Config
$administrator_workdir = "/xp/www/AutoMATA/download_data/";
$myFile = fopen($administrator_workdir . 'Jobs/' . $jobID . '/config.txt', 'a') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);
system($cmd, $ret_analysis);



// 连接训练结果和分析结果，修改数据库
// if $ret_train != 0，说明训练失败，显示处理模型训练失败信息
// if $ret_train == 0, 说明训练成功，显示不同模型的训练结果
ob_end_clean();
if ($ret_analysis == 0 && $ret_train == 0){
    // 训练和分析运行成功
    // 连接数据库, 插入joblist表
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


    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
    // 显示训练结果
    if ($modelType === "all"){
            echo "
            <tr style='$style_odd'>
                <td colspan='2' style='$style_top_line'><b>Model Testing Results: </b></td>
            </tr>
        </table>";

        echo "
        <table style = '$style_table'>
            <tr style='$style_subtable_line'><th>Model</th><th>Acc</th><th>Precision</th><th>Recall</th><th>F1</th><th>Result</th></tr>";
            foreach ($allData as $row){
                echo "<tr>";
                echo "<td>". htmlspecialchars($row[0]). "</td>";  //模型名称
                for ($i = 1; $i <=4; $i++){  //acc, precision, recall, f1
                    echo "<td>" . htmlspecialchars($row[$i]) . "</td>";
                }
                // echo '<td><a class = "btn btn-primary btn-primary-lin-height" href="' . htmlspecialchars($row[5]) . '">download</a></td>';  // 超链接
                echo '<td><a class="btn btn-primary" href="download.php?file=' . urlencode($row[5]) . '">download</a></td>';
                echo "</tr>";
            }
        
        echo "</table>";
    
    }else{
        echo "
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Model Training Results</td>
                    <td><a href='download.php?file=" . urlencode($zipFilePath) . "' class='btn btn-primary btn-primary-lin-height'>download</a></td>
                </tr>
                ";
                if ($modelType == "AutoEncoder")
                {
                    $autoencoder = $workdir_result . '/model_autoencoder.pth';  //模型文件1
                    $cls = $workdir_result . '/model_cls.pth';  //模型文件2
                    echo "
                    <tr>
                        <td class='line' style='$style_line'>Model</td>
                        <td>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($autoencoder) . "'>download sub model1</a>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($cls) . "'>download sub model2</a>
                        </td>
                    </tr>
                    ";
                }elseif ($modelType == "SOM") {
                    $model1 = $workdir_result . '/model.pth';  //模型文件1
                    $model2 = $workdir_result . '/winmap.pkl';  //模型文件2
                    echo "
                    <tr>
                        <td class='line' style='$style_line'>Model</td>
                        <td>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($model1) . "'>download sub model1</a>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($model2) . "'>download sub model2</a>
                        </td>
                    </tr>
                    ";
                }else{
                    $modelFilePath = $workdir_result . '/model.pth';  //模型文件
                    echo "
                    <tr>
                        <td class='line' style='$style_line'>Model</td>
                        <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($modelFilePath) . "'>download</a></td>
                    </tr>
                    ";
                }
                echo "
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Training Log</td>
                    <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($workdir_result . "/terminal_train.log") . "'>download</a></td>
                </tr>  
            </table>";
    }


    while (true){  // 修改6
        if (file_exists($workdir_result.'/df_cluster_heatmap.svg')){
            // 文件已存在，跳出循环
            break;
        }
        sleep(1); // 暂停 1 秒后继续检测
    }
    // 修改文件权限 修改7
    setFilePermission($workdir_result, 0777);

    // 显示分析结果
    echo "
        <table style = '$style_table'>
            <tr>
                <td style='border-right: 1px solid #c0c0c0; line-height: 400px;'><img src='$workdir_result/volcano.png' height='400px'></td>
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

            <tr class='odd' style='$style_odd'>
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

            <tr>
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


            <tr style='border-bottom: 1px solid #cdcdcd; background-color: #F7F7F7;' class='odd'>
                <td class='line' style='$style_line'>GO and KEGG enrichment analysis</td>
                <td><a href='all_analysis_sub.php?jobID=$jobID?org=$organism' target='_blank' class='btn btn-primary btn-primary-lin-height'>GO</a> </td>
            </tr>
                    
        </table>";


    // 在最后最后echo这个
    echo "
    </div>
    </section>";
}elseif ($ret_analysis == 0 && $ret_train != 0){
    // 分析成功，训练失败，显示处理模型训练失败信息
    // 连接数据库, 插入joblist表
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if (!$con) {
        echo "could not connect to mysql";
        die('Could not connect: ' . mysqli_connect_error());
    }
    $status = "Train_Failed";
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

    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
    // 显示训练失败
    echo "
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Model Training Results</td>
                <td>Results generation failure!</td>
            </tr>";

    
    // 显示分析结果
    echo"
            <tr>
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

            <tr class='odd' style='$style_odd'>
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

            <tr>
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


}elseif ($ret_analysis != 0 && $ret_train == 0){
    // 训练成功，分析失败，显示处理分析失败信息
    // 连接数据库, 插入joblist表
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if (!$con) {
        echo "could not connect to mysql";
        die('Could not connect: ' . mysqli_connect_error());
    }
    $status = "Analysis_Failed";
    $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
    if (!mysqli_query($con, $sql)) {
        die('Error: ' . mysqli_error($con));
    }
    mysqli_close($con);

    while (true){
        if (file_exists($workdir_result."/test_result.txt")){
            break;
        }
        sleep(1);
    }

    ob_end_clean();  // php 清除前面的输出, php覆盖之前的echo页面
    echo $basic_info;
    // 显示训练结果
    if ($modelType === "all"){
            echo "
            <tr style='$style_odd'>
                <td colspan='2' style='$style_top_line'><b>Model Testing Results: </b></td>
            </tr>
        </table>";

        echo "
        <table style = '$style_table'>
            <tr style='$style_subtable_line'><th>Model</th><th>Acc</th><th>Precision</th><th>Recall</th><th>F1</th><th>Result</th></tr>";
            foreach ($allData as $row){
                echo "<tr>";
                echo "<td>". htmlspecialchars($row[0]). "</td>";  //模型名称
                for ($i = 1; $i <=4; $i++){  //acc, precision, recall, f1
                    echo "<td>" . htmlspecialchars($row[$i]) . "</td>";
                }
                // echo '<td><a class = "btn btn-primary btn-primary-lin-height" href="' . htmlspecialchars($row[5]) . '">download</a></td>';  // 超链接
                echo '<td><a class="btn btn-primary" href="download.php?file=' . urlencode($row[5]) . '">download</a></td>';
                echo "</tr>";
            }
        
        echo "</table>";
    
    }else{
        echo "
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Model Training Results</td>
                    <td><a href='download.php?file=" . urlencode($zipFilePath) . "' class='btn btn-primary btn-primary-lin-height'>download</a></td>
                </tr>
                ";
                if ($modelType == "AutoEncoder")
                {
                    $autoencoder = $workdir_result . '/model_autoencoder.pth';  //模型文件1
                    $cls = $workdir_result . '/model_cls.pth';  //模型文件2
                    echo "
                    <tr>
                        <td class='line' style='$style_line'>Model</td>
                        <td>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($autoencoder) . "'>download sub model1</a>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($cls) . "'>download sub model2</a>
                        </td>
                    </tr>
                    ";
                }elseif ($modelType == "SOM") {
                    $model1 = $workdir_result . '/model.pth';  //模型文件1
                    $model2 = $workdir_result . '/winmap.pkl';  //模型文件2
                    echo "
                    <tr>
                        <td class='line' style='$style_line'>Model</td>
                        <td>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($model1) . "'>download sub model1</a>
                            <a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($model2) . "'>download sub model2</a>
                        </td>
                    </tr>
                    ";
                }else{
                    $modelFilePath = $workdir_result . '/model.pth';  //模型文件
                    echo "
                    <tr>
                        <td class='line' style='$style_line'>Model</td>
                        <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($modelFilePath) . "'>download</a></td>
                    </tr>
                    ";
                }
                echo "
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Training Log</td>
                    <td><a class='btn btn-primary btn-primary-lin-height' href='download.php?file=" . urlencode($workdir_result . "/terminal_train.log") . "'>download</a></td>
                </tr>  
            </table>";
    }

    echo"
            <table style = '$style_table'>
                <tr style='border-bottom: 1px solid #cdcdcd;'>
                    <td class='line' style='$style_line'>Analysis Results</td>
                    <td>Results generation failure!</td>
                </tr>
            </table>
        </div>
    </section>
    ";


}else{
    // 训练 分析都失败
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

    echo"
            <table style = '$style_table'>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Model Training Results</td>
                    <td>Training failure!</td>
                </tr>
                <tr style='border-bottom: 1px solid #cdcdcd;'>
                    <td class='line' style='$style_line'>Analysis Results</td>
                    <td>Results generation failure!</td>
                </tr>
            </table>
        </div>
    </section>
    ";


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