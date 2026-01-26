<?php
include __DIR__ . '/header.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './PHPMailer/PHPMailer/src/Exception.php';
require './PHPMailer/PHPMailer/src/PHPMailer.php';
require './PHPMailer/PHPMailer/src/SMTP.php';
require './table/renderer.php';
set_time_limit(0); 

$jobID = $_POST["jobID"];
$org = $_POST["org"];
$type_analysis = $_POST["type_analysis"];

$pvalue_go = $_POST["pvalue_go"];
$qvalue_go = $_POST["qvalue_go"];
$type_go = $_POST["type_go"];
$termNum_go = $_POST["termNum_go"];
// 修改
$correc = array("BH", "BY", "holm", "hochberg", "hommel", "bonferroni", "fdr", "none");
$correction_go = $correc[$_POST["correction_go"]];

if ($org == "Homo_sapiens") {
    $org_kegg = "hsa";
}elseif ($org == "Mus_musculus") {
    $org_kegg = "mmu";
}elseif ($org == "Bovine") {
    $org_kegg = "bos";
}elseif ($org == "Drosophila_melanogaster") {
    $org_kegg = "dme";
}

$pvalue_kegg = $_POST["pvalue_kegg"];
$qvalue_kegg = $_POST["qvalue_kegg"];
$type_kegg = $_POST["type_kegg"];
$termNum_kegg = $_POST["termNum_kegg"];
$correction_kegg = $correc[$_POST["correction_kegg"]];


// 告知用户正在运行GO和KEGG分析
$style_table = "width: 1296px; text-align: center; line-height: 50px; border-collapse: collapse;"; // 表格样式
$style_odd = "background-color: #F7F7F7;";  // 表格奇数行的样式
$style_line = "border-right: 1px solid #c0c0c0; width: 648px;";  // 中间的竖线
$type_analysis_web = strtoupper($type_analysis);
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
                <td>$org</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Analysis Type</td>
                <td>$type_analysis_web</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>pvalue threshold for GO enrichment</td>
                <td>$pvalue_go</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>qvalue threshold for GO enrichment</td>
                <td>$qvalue_go</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Plot Type for GO enrichment</td>
                <td>$type_go</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>The number of terms for GO enrichment</td>
                <td>$termNum_go</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>Correction method for GO enrichment</td>
                <td>$correction_go</td>
            </tr>

            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>pvalue threshold for KEGG enrichment</td>
                <td>$pvalue_kegg</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>qvalue threshold for KEGG enrichment</td>
                <td>$qvalue_kegg</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Plot Type for KEGG enrichment</td>
                <td>$type_kegg</td>
            </tr>
            <tr>
                <td class='line' style='$style_line'>The number of terms for KEGG enrichment</td>
                <td>$termNum_kegg</td>
            </tr>
            <tr class='odd' style='$style_odd'>
                <td class='line' style='$style_line'>Correction method for KEGG enrichment</td>
                <td>$correction_kegg</td>
            </tr>
";
// ob_start(); // 启用输出缓冲
echo $basic_info;
echo"
            <tr style='border-bottom: 1px solid #cdcdcd;'>
                <td class='line' style='$style_line'>Running</td>
                <td><img id='running_bar' src='images/progress_bar_new.gif' height='25px'></td>
            </tr>
        </table>
    </div>
</section>
";

// // 连接数据库, 插入joblist表 Error: Duplicate entry '20250324154151_LRvvCFDW' for key 'joblist.PRIMARY'
$con =  mysqli_connect("localhost", "automata", "123456", "automata");
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

// 运行GO代码
$workdir= "download_data/Jobs/".$jobID."/";
$workdir_result= "download_data/Jobs/".$jobID."/result";
$infile = "download_data/Jobs/".$jobID."/result/select_".$type_analysis.".txt";  # 数据路径
// 删除$infile的最后一列
// 修改
while (true){
    if (file_exists($infile)){  // svg
        // 文件已存在，跳出循环
        break;
    }
    sleep(0.2); // 暂停 1 秒后继续检测
}


// 运行R命令
// cmd: Rscript cor_heatmap.r -i cor_heatmap_example.txt 
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
$rfile = "code/data_analysis_plot/go_enrichment.R";
$param_i = " -i ".$infile;
$param_j = " -j ".$jobID;
$param_a = " -a ".$type_go;
$param_b = " -b ".$org;
$param_c = " -c ".$pvalue_go;
$param_d = " -d ".$qvalue_go;
$param_e = " -e ".$termNum_go;
$param_g = " -g ".$correction_go;  // 修改
$param_f = " -f ".$type_analysis;  // up, down, all, none(default)
if ($type_go == "circle"){
   $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_g. $param_c.  $param_b.  $param_a. $param_d. $param_f.  " > " . $workdir . "terminal_msg_go.txt 2>&1 ";  // &
}elseif ($type_go == "chord" || $type_go == "cluster"|| $type_go == "bubble" || $type_go == "barplot"){
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_g. $param_c.  $param_b.  $param_a. $param_d. $param_e. $param_f. " > " . $workdir . "terminal_msg_go.txt 2>&1 ";  // &
}
// 加载信息Config
$administrator_workdir = "/xp/www/AutoMATA/download_data/";
$myFile = fopen($administrator_workdir . 'Jobs/' . $jobID . '/config.txt', 'w') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);
system($cmd, $ret_go);

// 运行KEGG代码
// 运行R命令
// cmd: Rscript cor_heatmap.r -i cor_heatmap_example.txt 
$rscript = "/opt/anaconda/envs/R_442/bin/Rscript --no-save ";
$rfile = "code/data_analysis_plot/kegg_enrichment.R";
$param_i = " -i ".$infile;
$param_j = " -j ".$jobID;
$param_a = " -a ".$type_kegg;
$param_b = " -b ".$org_kegg;
$param_c = " -c ".$pvalue_kegg;
$param_d = " -d ".$qvalue_kegg;
$param_e = " -e ".$termNum_kegg;
$param_g = " -g ".$correction_kegg;  // 修改
if ($type_kegg == "circle"){
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_g. $param_c.  $param_b.  $param_a. $param_d. $param_f.   " > " . $workdir . "terminal_msg_kegg.txt 2>&1 ";  // &
}elseif ($type_kegg == "chord" || $type_kegg == "cluster" || $type_kegg == "bubble"){
    $cmd = "". $rscript . " ". $rfile. $param_i. $param_j. $param_g. $param_c.  $param_b.  $param_a. $param_d. $param_e. $param_f.  " > " . $workdir . "terminal_msg_kegg.txt 2>&1 ";  // &
}
$myFile = fopen($administrator_workdir . 'Jobs/' . $jobID . '/config.txt', 'a') or die("Unable to open config file!");
fwrite($myFile, "command: $cmd\n");
fclose($myFile);
system($cmd, $ret_kegg);


if ($ret_go == 0 && $ret_kegg == 0){  // 运行成功
    // 修改joblist表
    $con =  mysqli_connect("localhost", "automata", "123456", "automata");
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
        if (file_exists($workdir_result.'/kegg_enrichment.svg')){
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
    echo"
                <tr>
                    <td class='line' style='$style_line'>GO Enrichment results</td>
                    <td><a href='download.php?file=" . urlencode($workdir_result."/GO_enrichment_result.txt") . "' class='btn btn-primary btn-primary-lin-height'>dowload</a> </td>
                </tr>
                <tr class='odd' style='background-color: #F7F7F7; border-bottom: 1px solid #cdcdcd;'>
                    <td style='border-right: 1px solid #c0c0c0; line-height: 400px;'><img src='$workdir_result/go_enrichment.png?t=" . time() ." ' height='400px'></td>
                    <td>
                        <div class='dropdown' style='display: flex; justify-content: space-around;'>
                            <button class='dropdown-toggle btn btn-primary' data-bs-toggle='dropdown' id='go_enrichment' role='button' style='display: flex; align-items: center'><i class='material-icons'>file_download</i>Download GO</button>
                            <div class='dropdown-menu' aria-labelledby='go_enrichment'>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/go_enrichment.pdf") . "' class='dropdown-item'>PDF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/go_enrichment.png") . "' class='dropdown-item'>PNG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/go_enrichment.svg") . "' class='dropdown-item'>SVG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/go_enrichment.tiff") . "' class='dropdown-item'>TIFF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/go_enrichment.jpeg") . "' class='dropdown-item'>JPEG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/go_enrichment.bmp") . "' class='dropdown-item'>BMP</a></li>
                            </div>
                        </div>
                    </td>
                </tr>
                <tr >
                    <td class='line' style='$style_line'>KEGG Enrichment results</td>
                    <td><a href='download.php?file=" . urlencode($workdir_result."/KEGG_enrichment_result.txt") . "' class='btn btn-primary btn-primary-lin-height'>dowload</a></td>
                </tr>
                <tr class='odd' style='background-color: #F7F7F7; border-bottom: 1px solid #cdcdcd;'>
                    <td style='border-right: 1px solid #c0c0c0; line-height: 400px;'><img src='$workdir_result/kegg_enrichment.png?t=" . time() ." ' height='400px'></td>
                    <td>
                        <div class='dropdown' style='display: flex; justify-content: space-around;'>
                            <button class='dropdown-toggle btn btn-primary' data-bs-toggle='dropdown' id='kegg_enrichment' role='button' style='display: flex; align-items: center'><i class='material-icons'>file_download</i>Download KEGG</button>
                            <div class='dropdown-menu' aria-labelledby='kegg_enrichment'>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/kegg_enrichment.pdf") . "' class='dropdown-item'>PDF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/kegg_enrichment.png") . "' class='dropdown-item'>PNG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/kegg_enrichment.svg") . "' class='dropdown-item'>SVG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/kegg_enrichment.tiff") . "' class='dropdown-item'>TIFF</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/kegg_enrichment.jpeg") . "' class='dropdown-item'>JPEG</a></li>
                                <li><a href='download.php?file=" . urlencode($workdir_result."/kegg_enrichment.bmp") . "' class='dropdown-item'>BMP</a></li>
                            </div>
                        </div>
                    </td>
                </tr>

            </table>

        </div>
    </section>
    ";

    // try {
    //     $filePath = '../'.$workdir_result . '/GO_enrichment_result.txt';
    //     echo renderOntologyTable($filePath, 'GO_enrichment_result.txt');
    // } catch (Exception $e) {
    //     echo "Error: " . $e->getMessage();
    // }

    // try {
    //     $filePath = '../'.$workdir_result . '/KEGG_enrichment_result.txt';
    //     echo renderOntologyTable($filePath, 'KEGG_enrichment_result.txt');
    // } catch (Exception $e) {
    //     echo "Error: " . $e->getMessage();
    // }


}else{
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