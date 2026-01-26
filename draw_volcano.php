<?php include __DIR__ . '/header.php' ?>

<script type="text/javascript">

    var checkInput = function() {  // 检查后缀名 txt csv excel

        // upload_file_1数据集
        file_id = "upload_file_1"
        var obj = document.getElementById(file_id);
        var len = obj.files.length;
        var full_file_name = "";
        for (var i = 0; i < len; i++) {
            full_file_name = obj.files[i].name;  // combined.txt
        }
        var index =full_file_name.lastIndexOf(".");  // 获取文件名后缀的索引
        var suffix = full_file_name.substring(index+1, full_file_name.length);  // txt
        
        if (suffix != "csv" && suffix != "txt" && suffix != "excel"){
            window.alert("Please upload a txt, csv or excel file!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        // upload_file_2 gmt数据集  修改
        var gsea = $("input[name='gsea_analysis']:checked").val();
        if (gsea == "yes"){
            file_id = "upload_file_2"
            var obj = document.getElementById(file_id);
            var len = obj.files.length;
            var full_file_name = "";
            for (var i = 0; i < len; i++) {
                full_file_name = obj.files[i].name;  // combined.txt
            }
            var index =full_file_name.lastIndexOf(".");  // 获取文件名后缀的索引
            var suffix = full_file_name.substring(index+1, full_file_name.length);  // txt
            
            if (suffix != "gmt"){
                window.alert("Please upload a gmt file!");
                var draw_form = document.getElementsByClassName("draw_form")[0];
                draw_form.focus();
                return false;
            }
        }

        var confidence = document.getElementById("fc_thr").value;
        if (confidence == ""){
            window.alert("Please input log2FC threshold!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("padj_thr").value;
        if (confidence == ""){
            window.alert("Please input padj threshold!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("top").value;
        if (confidence == ""){
            window.alert("Please input top!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("top_fc_thr").value;
        if (confidence == ""){
            window.alert("Please input log2FC threshold for TOP genes!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("top_padj_thr").value;
        if (confidence == ""){
            window.alert("Please input padj threshold for TOP genes!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        // window.alert('email')
        // 检查邮件格式
        var email = document.getElementById("email").value; //box
        var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        if (!regex.test(email)) {
            window.alert("Please submit the correct email address");
            // document.getElementById("email").enter.focus();
            var process_form = document.getElementsByClassName("draw_form")[0];
            process_form.focus();
            return false;
        }
        // if (email != ""){
        //     var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        //     if (!regex.test(email)) {
        //         window.alert("Please submit the correct email address");
        //         var draw_form = document.getElementsByClassName("draw_form")[0];
        //         draw_form.focus();
        //         return false;
        //     }
        // }

        return true;
        
    }

    var download_example_file1 = function() {
        // 正儿八经的下载文件功能
        const fileUrl = "./example/draw_example/volcano_example.txt"; // 文件的实际路径
        const fileName = "volcano_example.txt"; // 下载时保存的文件名

        const a = document.createElement("a"); // 创建一个 <a> 标签元素
        a.href = fileUrl; // 设置下载链接
        a.download = fileName; // 设置下载文件名
        document.body.appendChild(a); // 将 <a> 标签添加到页面
        a.click(); // 模拟点击 <a> 标签，触发下载
        document.body.removeChild(a); // 删除 <a> 标签，清理DOM
    }

    var download_example_file2 = function() {
        const fileUrl = "./example/draw_example/volcano_gsea_example.gmt"; // 文件的实际路径
        const fileName = "volcano_gsea_example.gmt"; // 下载时保存的文件名

        const a = document.createElement("a"); // 创建一个 <a> 标签元素
        a.href = fileUrl; // 设置下载链接
        a.download = fileName; // 设置下载文件名
        document.body.appendChild(a); // 将 <a> 标签添加到页面
        a.click(); // 模拟点击 <a> 标签，触发下载
        document.body.removeChild(a); // 删除 <a> 标签，清理DOM

        // window.open("./example/draw_example/volcano_gsea_example.gmt")
    }

    var checkEmail = function() { // 判断email格式是否正确 写的不对
        var email = document.getElementById("email").value; //box
        var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        if (email == '' || !regex.test(email)) {
            window.alert("Please submit the correct email address");
            document.getElementById("email").enter.focus();
            return false;
        } else {
            return true;
        }
    }

    // 修改
    function useGSEA(){
        document.getElementById("gmt_file").style.display="";
    }
    function noUseGSEA(){
        document.getElementById("gmt_file").style.display="none";
    }
</script>


<section id="banner">
    <div class="container padding-medium-2">
        <div class="hero-content">
            <!-- <h2 class="display-2 fw-semibold">About <span class="text-primary"> Us</span></h2> -->
            <h2 class="display-2 fw-semibold">Volcano Plot with GSEA</span></h2>
            <nav class="breadcrumb">
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <a class="breadcrumb-item text-muted nav-link" href="index.php">Data Analysis</a>
                <span class="breadcrumb-item active" aria-current="page">Volcano Plot with GSEA</span>
            </nav>
        </div>
    </div>
</section>


<!-- 上传数据 -->
<section id="service" class="padding-medium">
    <div class="container">
        <form id="form" class="draw_form" name="draw_form" method="post" action="draw_volcano2.php" onsubmit="JavaScript: return checkInput()" enctype="multipart/form-data"> <!-- onsubmit="javascript:return checkInput()"-->
            
            <div class="pb-3">
                <label>1. Upload data set (NOTE: Please make sure the column names of the dataset are gene, logFC, padj. The seperater is '\t'.)</label>
                <input type="file" id="upload_file_1" name="upload_file_1" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example_file1()">Example</button>
            </div>

            <!--修改-->
            <div class="pb-3" style="margin-bottom: 22px;">
                <label>2. Whether to conduct GSEA analysis</label>
                <input type="radio" name="gsea_analysis" value="yes" onclick="useGSEA()"> Yes
                <input type="radio" name="gsea_analysis" value="no" onclick="noUseGSEA()" checked> No</label>
            </div>
            <!--修改-->
            <div class="pb-3" style="display: none;" id = "gmt_file">
                <label>Upload gmt data for GSEA analysis</label>
                <input type="file" id="upload_file_2" name="upload_file_2" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example_file2()">Example</button>
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>3. Input gene names that you want to emphasize (NOTE: Please separate them by English comma, and entered gene names should be included in the uploaded data set)</label>
                <input type="text" name="gene_sig" id="gene_sig" placeholder="e.g. KRAS,FOSL1,MYC" class="form-control">
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>4. Input the threshold of log2FC (NOTE: |log2FC| > threshold. It is generally 0.58, 1 or 2 referenced from doi: 10.1073/pnas.0502674102 and 10.5194/aab-52-65-2009)</label>
                <input type="text" name="fc_thr" id="fc_thr" class="form-control" value="0.5">
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>5. Input the threshold of padj (NOTE: padj < threshold. It is generally 0.05 referenced from doi: 10.5194/aab-52-65-2009)</label>
                <input type="text" name="padj_thr" id="padj_thr" value="0.05" class="form-control">
            </div>


            <div class="pb-3" style="margin-bottom: 20px;">
                <label>6. Input the number of TOP genes (NOTE: The TOP shows the higher-order gene that needs to be displayed)</label>
                <input type="text" name="top" id="top" value="200" class="form-control">
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>7. Input the threshold of log2FC for TOP genes</label>
                <input type="text" name="top_fc_thr" id="top_fc_thr" value="1" class="form-control">
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>8. Input the threshold of padj  for TOP genes</label>
                <input type="text" name="top_padj_thr" id="top_padj_thr" value="0.01" class="form-control">
            </div>


            <div class="pb-3">
                <label>Your Email</label>
                <input type="text" name="email" id="email" placeholder="Write your email here" class="form-control">
            </div>
            <!-- <button type="button" name="submit" onclick="JavaScript: return checkInput()" class="btn btn-primary  px-5 py-3 mt-2 w-100">Submit</button> -->
            <button type="submit" name="submit" class="btn btn-primary  px-5 py-3 mt-2 w-100">Submit</button>

            <div class="pb-3" style="text-align: center; margin-top: 30px;">
                <label style="margin-bottom: 20px;">Example Figure is as follows:</label><br/>
                <img src="images/volcano_example.png" alt="img" style="margin: 0 auto; width: 900px; height: 700px;">
            </div>
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