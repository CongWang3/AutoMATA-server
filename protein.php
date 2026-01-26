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
        const fileUrl = "./example/test_protein_refseq.txt"; // 文件的实际路径
        const fileName = "test_protein_refseq.txt"; // 下载时保存的文件名

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
            <h2 class="display-2 fw-semibold">Protein</span></h2>
            <!-- <nav class="breadcrumb"> -->
            <nav class="breadcrumb" style="margin-top: -8px;">  <!--一审-->
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <a class="breadcrumb-item text-muted nav-link" href="index.php">Data Process</a>
                <span class="breadcrumb-item active" aria-current="page">Protein</span>
            </nav>

            <!--一审-->
            <nav class="breadcrumb"> 
                <span class="breadcrumb-item active" aria-current="page" style="font-size: 14px; margin-top: -13px;">>Details: This page provide conversion of protein expression data from <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i> and <i>Drosophila Melanogaster</i> in expression value formats to log2(expression value) format. 
            Users can select different nomenclatures for protein, which are UniProt Entry, Refseq Accession, AlphaFoldDB ID, and EnsemblID. Entry names corresponding to different nomenclatures are provided in the generated result file. Click "Example" button to download the example data.
                </span>
            </nav>
        </div>
    </div>
</section>

<!-- 上传数据 -->
<section id="service" class="padding-medium">

    <div class="container">
        <form id="form" class="process_form" name="process_form" method="post" action="protein2.php" onsubmit="JavaScript: return checkInput()" enctype="multipart/form-data"> <!-- onsubmit="javascript:return checkInput()"-->
            <div class="pb-3">
                <label>1. Upload protein expression data</label>
                <input type="file" id="upload_file" name="upload_file" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example()">Example</button>
            </div>
            <div class="pb-3" style="margin-bottom: 22px;">
                <label>2. The protein nomenclature of the input expression data</label> <br>
                <select class="param_select" id="first" name="naming" onChange="change()"> <!-- style="font-size:17px; font-style:italic; -->
                    <option value="0">Entry</option>
                    <option value="1" selected="selected" >RefSeq</option>
                    <option value="2">AlphaFoldDB</option>
                    <option value="3">Ensembl</option>
                </select>

            </div>

            <div class="pb-3" style="margin-bottom: 22px;">
                <label>3. The organism of the input expression data</label> <br>
                <select class="param_select" id="first" name="organism" onChange="change()"> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">Homo sapiens</option>
                    <option value="1">Bos taurus</option>
                    <option value="2">Mus musculus</option>
                    <option value="3">Drosophila melanogaster</option>
                </select>

            </div>


            <div class="pb-3">
                <label>Your Email</label>
                <input type="text" name="email" id="email" placeholder="Write your email here" class="form-control">
            </div>
            <!-- <button type="button" name="submit" onclick="JavaScript: return checkInput()" class="btn btn-primary  px-5 py-3 mt-2 w-100">Submit</button> -->
            <button type="submit" name="submit" class="btn btn-primary  px-5 py-3 mt-2 w-100">Submit</button>
        </form>


        <!--如果只有一个表单项，则需要把submit按钮换成button类型的，再使用onclick()就好了-->
        <!--链接：https://blog.csdn.net/qq_41739987/article/details/109610841#:~:text=%E9%97%AE%E9%A2%98%EF%BC%9A%20%E4%BD%BF%E7%94%A8%E8%A1%A8%E5%8D%95%E7%9A%84onsubmit%E5%B1%9E%E6%80%A7%E8%BF%9B%E8%A1%8C%E5%88%A4%E6%96%AD%E9%9D%9E%E7%A9%BA%E7%9A%84%E6%97%B6%E5%80%99%20return%20false%E4%BB%8D%E7%84%B6%E4%BC%9A%E6%89%A7%E8%A1%8C%E8%A7%A3%E5%86%B3%E6%96%B9%E6%A1%88%E9%A6%96%E5%85%88%E6%A3%80%E6%9F%A5JS%E6%98%AF%E5%90%A6%E5%AD%98%E5%9C%A8%E8%AF%AD%E6%B3%95%E9%94%99%E8%AF%AF%EF%BC%8C%E5%A6%82%E5%9B%BE%E6%89%80%E7%A4%BA%E5%B9%B6%E4%B8%8D%E5%AD%98%E5%9C%A8userName%E8%BF%99%E4%B8%AA%E5%8F%98%E9%87%8F%20%E6%89%80%E4%BB%A5%E6%89%A7%E8%A1%8C%E5%AE%8C%E7%9C%9F%E5%AE%9E%E5%A7%93%E5%90%8D%E4%B8%8D%E8%83%BD%E4%B8%BA%E7%A9%BA%E4%B9%8B%E5%90%8E%E7%94%B1%E4%BA%8EJs%E7%9A%84%E8%AF%AD%E6%B3%95%E9%94%99%E8%AF%AF,%E8%80%8C%E5%AF%BC%E8%87%B4%E5%90%8E%E9%9D%A2%E7%9A%84return%20false%E5%B9%B6%E6%B2%A1%E6%9C%89%E7%94%9F%E6%95%88%20%E6%89%80%E4%BB%A5%E4%BE%9D%E6%97%A7%E4%BC%9A%E6%8F%90%E4%BA%A4%E8%A1%A8%E5%8D%95%E5%A6%82%E6%9E%9C%E5%8F%AA%E6%9C%89%E4%B8%80%E4%B8%AA%E8%A1%A8%E5%8D%95%E9%A1%B9%EF%BC%8C%E5%88%99%E9%9C%80%E8%A6%81%E6%8A%8Asubmit%E6%8C%89%E9%92%AE%E6%8D%A2%E6%88%90button%E7%B1%BB%E5%9E%8B%E7%9A%84%EF%BC%8C%E5%86%8D%E4%BD%BF%E7%94%A8onclick%20%28%29%E5%B0%B1%E5%A5%BD%E4%BA%86%E5%8E%9F%E5%9B%A0%E6%98%AFonsubmit%20%E8%BF%99%E4%B8%AA%E6%96%B9%E6%B3%95%E6%98%AF%E5%9C%A8%E6%8F%90%E4%BA%A4%E8%A1%A8%E5%8D%95%E6%97%B6%E4%BA%A7%E7%94%9F%E7%9A%84%EF%BC%8C%E4%B9%9F%E5%B0%B1%E6%98%AF%E5%85%88%E6%8F%90%E4%BA%A4%E8%A1%A8%E5%8D%95%E5%90%8E%E8%B0%83%E7%94%A8%E6%96%B9%E6%B3%95%E4%BF%AE%E6%94%B9%E5%90%8E%E7%9A%84%E4%BB%A3%E7%A0%81%E5%A6%82%E4%B8%8B%EF%BC%9A_submit%20input%E7%9A%84onclick%E8%BF%94%E5%9B%9E%E4%BA%86false%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%98%E6%98%AF%E4%BC%9A%E6%8F%90%E4%BA%A4-->
        <!--所以在这里设置一个不可见的form表单-->
        <form>
            <input type="hidden">
        </form>


    </div>

</section>

<?php include __DIR__ . '/footer.php' ?>