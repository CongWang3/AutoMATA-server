<?php include __DIR__ . '/header.php' ?>

<script type="text/javascript">

    var checkInput = function() {  // 检查后缀名 txt csv excel
        // window.alert("test")
        var obj = document.getElementById("upload_file");
        var len = obj.files.length;
        var full_file_name = "";
        for (var i = 0; i < len; i++) {
            full_file_name = obj.files[i].name;  // combined.txt
        }
        var index =full_file_name.lastIndexOf(".");  // 获取文件名后缀的索引
        var suffix = full_file_name.substring(index+1, full_file_name.length);  // txt

        
        if (suffix != "csv" && suffix != "txt" && suffix != "excel"){
            window.alert("Please upload a txt, csv or excel file!");
            var process_form = document.getElementsByClassName("process_form")[0];
            process_form.focus();
            return false;
        }

        // window.alert("email")
        // 检查邮件格式
        var email = document.getElementById("email").value; //box
        var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        if (!regex.test(email)) {
            window.alert("Please submit the correct email address");
            // document.getElementById("email").enter.focus();
            var process_form = document.getElementsByClassName("process_form")[0];
            process_form.focus();
            return false;
        }
        // window.alert(email)
        // if (email != ""){
        //     var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        //     if (!regex.test(email)) {
        //         window.alert("Please submit the correct email address");
        //         // document.getElementById("email").enter.focus();
        //         var process_form = document.getElementsByClassName("process_form")[0];
        //         process_form.focus();
        //         return false;
        //     } else {
        //         return true;
        //     }
        // }

        return true;
        
    }

    var download_example = function() {
        const fileUrl = "./example/test_refseq_fpkm_mrna.txt"; // 文件的实际路径
        const fileName = "refseq_accession_fpkm2TPM_mrna.txt"; // 下载时保存的文件名

        const a = document.createElement("a"); // 创建一个 <a> 标签元素
        a.href = fileUrl; // 设置下载链接
        a.download = fileName; // 设置下载文件名
        document.body.appendChild(a); // 将 <a> 标签添加到页面
        a.click(); // 模拟点击 <a> 标签，触发下载
        document.body.removeChild(a); // 删除 <a> 标签，清理DOM

        // window.open("./example/test_geneid_fpkm2TPM.txt")
    }

</script>

<!-- <style>
    引入css
    <?php include __DIR__ . '/../static/css/show.css' ?>  /*因为chrome直接用link加载css时会把css转为html，这是不对的，所以要用这样子加载*/
</style> -->
<!-- <section id="banner" style="background-image:url(images/background-img.jpg);"> -->
<section id="banner">
    <div class="container padding-medium-2">
        <div class="hero-content">
            <!-- <h2 class="display-2 fw-semibold">About <span class="text-primary"> Us</span></h2> -->
            <h2 class="display-2 fw-semibold">Transcriptome</span></h2>
            <!-- <nav class="breadcrumb"> -->
            <nav class="breadcrumb" style="margin-top: -8px;">  <!--一审-->
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <a class="breadcrumb-item text-muted nav-link" href="index.php">Data Process</a>
                <span class="breadcrumb-item active" aria-current="page">Transcriptome</span>
            </nav>

            <!--一审-->
            <nav class="breadcrumb"> 
                <span class="breadcrumb-item active" aria-current="page" style="font-size: 14px; margin-top: -13px;">>Details: This page provide conversion of mRNA expression data from <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i> and <i>Drosophila Melanogaster</i> in RPKM, TPM, ReadCounts, FPKM and RPM formats to log2(TPM+1) format. 
            Users can select different nomenclatures for mRNA, which are Refseq Accession, Transcript name and EnsemblID. Transcript names corresponding to different nomenclatures are provided in the generated result file. Click "Example" button to download the example data.
                </span>
            </nav>
            
        </div>
    </div>
</section>

<!-- 上传数据 -->
<section id="service" class="padding-medium">

    <div class="container">
        <form id="form" class="process_form" name="process_form" action="dataProcess_transcriptome.php" method="post" onsubmit="javascript:return checkInput()" enctype="multipart/form-data"> <!-- onsubmit="javascript:return checkInput()"-->
            <div class="pb-3">
                <label>1. Upload mRNA expression data</label>
                <input type="file" id="upload_file" name="upload_file" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example()">Example</button>
            </div>


            <div class="pb-3" style="margin-bottom: 22px;">
                <label>2. The mRNA nomenclature used in the input expression data</label> <br>
                <select class="param_select" id="first" name="geneMomen" onChange="change()">  <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">RefSeq accession (e.g. NM_001422116)</option>
                    <option value="1">Ensembl ID (e.g. ENST00000641515)</option>
                    <option value="2">Transcript name (e.g. OR4F5-201)</option>
                </select>

            </div>

            <div class="pb-3" style="margin-bottom: 22px;">
                <label>3. The type of the input expression data</label> <br>
                <select class="param_select" id="first" name="inputType" onChange="change()">  <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">FPKM</option>
                    <option value="1">RPM</option>
                    <option value="2">RPKM</option>
                    <option value="3">Read Counts</option>
                    <option value="4">TPM</option>
                </select>
            </div>

            <div class="pb-3" style="margin-bottom: 22px;">
                <label>4. The organism of the input expression data</label> <br>
                <select class="param_select" id="first" name="organism" onChange="change()">  <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">Homo sapiens</option>
                    <option value="1">Bos taurus</option>
                    <option value="2">Mus musculus</option>
                    <option value="3">Drosophila melanogaster</option>
                </select>

            </div>


            <div class="pb-3">
                <label>Your Email</label>
                <input type="text" name="email" placeholder="Write your email here" class="form-control">
            </div>
            <button type="submit" name="submit" class="btn btn-primary  px-5 py-3 mt-2 w-100">Submit</button>
        </form>
    </div>

</section>

<?php include __DIR__ . '/footer.php' ?>