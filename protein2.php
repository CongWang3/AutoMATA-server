<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';

// 处理RefSeq值：移除小数点及后面的数字
function cleanRefSeq($refseq) {
    return preg_replace('/\..*/', '', $refseq); // 移除小数点及之后的所有字符
}

$organisms = array("Homo sapiens", "Bos taurus", "Mus musculus", "Drosophila melanogaster");
$namings   = array("Entry", "RefSeq", "AlphaFoldDB", "Ensembl");
$sql_tables = array("homo_sapiens", "bos_taurus", "mus", "dm");

$organism_index = $_POST["organism"];
$naming_index   = $_POST["naming"];

$organism = $organisms[$organism_index];
$naming   = $namings[$naming_index];
$sql_table = $sql_tables[$organism_index];

// 设置JobID
date_default_timezone_set('Asia/Shanghai');
$jobID = date("YmdHis") . '_' . make_char();

// 转移用户上传的文件
$workdir = "download_data/Jobs/" . $jobID . "/";
// 修改文件权限 修改7
setFilePermission($workdir, 0777);
$dir = iconv("UTF-8", "GBK", $workdir);
if (!file_exists($dir)) {
    mkdir($dir, 0777, true);
}

$fileInfo = $_FILES["upload_file"];
$filePath = $fileInfo["tmp_name"];
$lines = file($filePath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

// 解析表头并校验
$header = explode("\t", trim(array_shift($lines))); // 获取表头

move_uploaded_file($filePath, $workdir . "origin.txt");

$email = $_POST["email"];  // 一审 修改
if ($email != ""){
    $myFile = fopen($workdir . 'email.txt', 'w') or die("Unable to open config file!");
    fwrite($myFile, "email: $email\n from protein2 php");
    fclose($myFile);
}
// 解析数据
$refseqs = [];
$data = [];
foreach ($lines as $line) {
    $columns = explode("\t", trim($line));
    $refseqs[] = $columns[0]; // 第一列是$naming指定的值
    $data[$columns[0]] = array_slice($columns, 1); // 其余列是SAMPLE数据
}

// 显示等待页面
$style_table = "width: 1296px; text-align: center; line-height: 50px; border-collapse: collapse;";
$style_odd = "background-color: #F7F7F7;";
$style_line = "border-right: 1px solid #c0c0c0; width: 648px;";

echo "
<section id='banner'>
    <div class='container padding-medium-2'>
        <div class='hero-content'>
            <h2 class='display-2 fw-semibold'>Waiting</h2>
            <nav class='breadcrumb'>
                <span class='breadcrumb-item active' aria-current='page'>Your JobID is $jobID, please wait a moment.</span>
            </nav>
        </div>
    </div>
</section>
<section id='service' class='padding-medium'>
    <div class='container'>
        <table style='$style_table'>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>JobID</td>
                <td>$jobID</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Protein Nomenclature</td>
                <td>$naming</td>
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

// 连接数据库，插入joblist表
$con = mysqli_connect("localhost", "automata", "123456", "automata");
if (!$con) {
    die('Could not connect: ' . mysqli_connect_error());
}

$status = "Submitted";
$sql = "INSERT INTO joblist (job_id, job_status) VALUES ('$jobID', '$status')";
if (!mysqli_query($con, $sql)) {
    die('Error: ' . mysqli_error($con));
}

// 查询处理
$results = [];
$processedRefseqs = [];
$table = 'protein_' . $sql_table;

foreach ($refseqs as $refseq) {
    // $cleanedRefseq = ($naming == 'RefSeq') ? cleanRefSeq($refseq) : $refseq; // 仅对RefSeq清理小数点
    $cleanedRefseq = cleanRefSeq($refseq); // 一审
    if (isset($processedRefseqs[$cleanedRefseq])) {
        $results[$refseq] = [$refseq, $processedRefseqs[$cleanedRefseq]];
        continue;
    }

    $safeRefseq = mysqli_real_escape_string($con, $refseq);
    if ($naming == 'RefSeq') {
        $sql = "SELECT RefSeq, Symbol FROM $table WHERE $naming LIKE '%$safeRefseq%'";
        $result = mysqli_query($con, $sql);
        if ($result && mysqli_num_rows($result) > 0) {
            while ($row = mysqli_fetch_assoc($result)) {
                $dbRefseqs = explode(';', $row['RefSeq']);
                foreach ($dbRefseqs as $dbRefseq) {
                    $cleanedDbRefseq = cleanRefSeq(trim($dbRefseq));
                    if ($cleanedDbRefseq === $cleanedRefseq) {
                        $results[$refseq] = [$refseq, $row['Symbol']];
                        $processedRefseqs[$cleanedRefseq] = $row['Symbol'];
                        break 2;
                    }
                }
            }
            mysqli_free_result($result);
        }
    } else {
        if ($naming == 'Ensembl') {
            $sql = "SELECT Symbol FROM $table WHERE Protein_stable_ID = '$safeRefseq' LIMIT 1";  // 重传数据库
        }else{
            $sql = "SELECT Symbol FROM $table WHERE $naming = '$safeRefseq' LIMIT 1";
        }
        // $sql = "SELECT Symbol FROM $table WHERE $naming = '$safeRefseq' LIMIT 1";
        $result = mysqli_query($con, $sql);
        if ($result && mysqli_num_rows($result) > 0) {
            $row = mysqli_fetch_assoc($result);
            $results[$refseq] = [$refseq, $row['Symbol']];
            $processedRefseqs[$cleanedRefseq] = $row['Symbol'];
            mysqli_free_result($result);
        }
    }
}
mysqli_close($con);

// 生成输出文件，包含log2计算
$output = "$naming\tSymbol\t" . implode("\t", array_slice($header, 1)) . "\n";
foreach ($refseqs as $refseq) {
    // $symbol = isset($results[$refseq]) ? $results[$refseq][1] : '';
    // $sampleValues = $data[$refseq];
    // $log2Values = array_map(function($value) {
    //     // return $value > 0 ? number_format(log($value, 2), 6) : '';
    //     return $value != 0 ? number_format(log($value+1, 2), 6) : 0;  # 一审
    // }, $sampleValues);
    // $output .= "$refseq\t$symbol\t" . implode("\t", $log2Values) . "\n";

    $symbol = isset($results[$refseq]) ? $results[$refseq][1] : '';
    
    // 确保每个refseq都有完整的样本数据，缺失值补0
    $sampleValues = isset($data[$refseq]) ? $data[$refseq] : array_fill(0, $sampleCount, 0);
    
    // 如果数据长度不足，用0补齐
    if (count($sampleValues) < $sampleCount) {
        $sampleValues = array_merge(
            $sampleValues, 
            array_fill(0, $sampleCount - count($sampleValues), 0)
        );
    }
    
    $log2Values = array_map(function($value) {
        // 处理各种可能的缺失值情况
        if ($value === '' || $value === null || $value === false || trim($value) === '') {
            return 0;
        }
        
        $numericValue = is_numeric($value) ? $value : 0;
        return $numericValue != 0 ? number_format(log($numericValue + 1, 2), 6) : 0;
    }, $sampleValues);
    
    $output .= "$refseq\t$symbol\t" . implode("\t", $log2Values) . "\n";
    
}

// $filename = 'test_protein_output.txt';
$filename = 'processed.txt';
$filepath = $workdir . $filename;

if (file_put_contents($filepath, $output) !== false) {
    $con = mysqli_connect("localhost", "automata", "123456", "automata");
    if (!$con) {
        die('Could not connect: ' . mysqli_connect_error());
    }
    $status = "Finished";
    $sql = "UPDATE joblist SET job_status = '$status' WHERE job_id = '$jobID'";
    if (!mysqli_query($con, $sql)) {
        die('Error: ' . mysqli_error($con));
    }
    mysqli_close($con);

    while (true){  // 修改6
        if (file_exists($filepath)){
            // 文件已存在，跳出循环
            break;
        }
        sleep(0.5); // 暂停 1 秒后继续检测
    }
    setFilePermission($filepath, 0777);

    $download_name = $jobID . '_processed.txt';
    ob_end_clean();
    echo "
    <section id='banner'>
        <div class='container padding-medium-2'>
            <div class='hero-content'>
                <h2 class='display-2 fw-semibold'>Result</h2>
                <nav class='breadcrumb'>
                    <span class='breadcrumb-item active' aria-current='page'>Your JobID is $jobID.</span>
                </nav>
            </div>
        </div>
    </section>
    <section id='service' class='padding-medium'>
        <div class='container'>
            <table style='$style_table'>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>JobID</td>
                    <td>$jobID</td>
                </tr>
                <tr>
                    <td class='line' style='$style_line'>Naming</td>
                    <td>$naming</td>
                </tr>
                <tr>
                    <td class='line' style='$style_line'>Organism</td>
                    <td>$organism</td>
                </tr>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>Data Process Result</td>
                    <td><a href='download.php?file=" . urlencode($filepath) . "' download='$download_name' class='btn btn-primary btn-primary-lin-height'>download</a></td>
                </tr>
            </table>
        </div>
    </section>";
} else {
    ob_end_clean();
    echo "
    <section id='banner'>
        <div class='container padding-medium-2'>
            <div class='hero-content'>
                <h2 class='display-2 fw-semibold'>Result</h2>
                <nav class='breadcrumb'>
                    <span class='breadcrumb-item active' aria-current='page'>Your JobID is $jobID, please wait a moment.</span>
                </nav>
            </div>
        </div>
    </section>
    <section id='service' class='padding-medium'>
        <div class='container'>
            <table style='$style_table'>
                <tr class='odd' style='$style_odd'>
                    <td class='line' style='$style_line'>JobID</td>
                    <td>$jobID</td>
                </tr>
                <tr>
                    <td class='line' style='$style_line'>Naming</td>
                    <td>$naming</td>
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

// 邮件发送
if ($_POST["email"] != "") {
    $email = $_POST["email"];
    $mail = new PHPMailer(true);
    try {
        $mail->CharSet = "UTF-8";
        $mail->SMTPDebug = 0;
        $mail->isSMTP();
        $mail->Host = 'smtp.163.com';
        $mail->SMTPAuth = true;
        $mail->Username = 'wanger0808@163.com';
        $mail->Password = 'DYHQMFHAHHIEEEUZ';
        $mail->SMTPSecure = 'ssl';
        $mail->Port = 465;

        $mail->setFrom('wanger0808@163.com', 'Multi Omics');
        $mail->addAddress($email, 'Joe');
        $mail->addReplyTo('wanger0808@163.com', 'info');

        $mail->isHTML(true);
        $mail->Subject = 'Multi Omics Result';
        $mail->Body = "<p>Dear user, <br />Your JobID is $jobID. Your data has been processed successfully, and the processed data is attached. <br />Thank you for using our service.<br /></p>" . date('Y-m-d H:i:s');
        $mail->AddAttachment($filepath, $download_name);
        $mail->send();
    } catch (Exception $e) {
        echo '邮件发送失败: ', $mail->ErrorInfo;
    }
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

function make_char($length = 8) {
    $chars = array('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
        't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
        'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9');
    $char_txt = '';
    for ($i = 0; $i < $length; $i++) {
        $char_txt .= $chars[array_rand($chars)];
    }
    return $char_txt;
}

include __DIR__ . '/footer.php';
?>