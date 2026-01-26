<?php include __DIR__ . '/header.php' ?>

<script type="text/javascript">

    function getURLParameter(name) { 
        return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null; 
    }

    function getUrlParams(name){ // 获取url参数
        const params = new URLSearchParams(window.location.search);
        var all = params.get('jobID');
        // 以？分割
        var jobID = all.split("?")[0];
        var org = all.split("?")[1].split("=")[1];
        
        document.getElementById("jobID").value = jobID;
        document.getElementById("org").value = org;
    }

    var checkInput = function() {  // 检查后缀名 txt csv excel
        getUrlParams();


        // 检查confidence、lr、es是否为空值
        var confidence = document.getElementById("pvalue_go").value;
        if (confidence == ""){
            window.alert("Please input pvalue for GO enrichment!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("qvalue_go").value;
        if (confidence == ""){
            window.alert("Please input qvalue for GO enrichment!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("termNum_go").value;
        if (confidence == ""){
            window.alert("Please input the number of terms to be displayed for GO enrichment!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("pvalue_kegg").value;
        if (confidence == ""){
            window.alert("Please input pvalue for KEGG enrichment!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("qvalue_kegg").value;
        if (confidence == ""){
            window.alert("Please input qvalue for KEGG enrichment!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }

        var confidence = document.getElementById("termNum_kegg").value;
        if (confidence == ""){
            window.alert("Please input the number of terms to be displayed for KEGG enrichment!");
            var draw_form = document.getElementsByClassName("draw_form")[0];
            draw_form.focus();
            return false;
        }


        // window.alert('email')
        // 检查邮件格式
        var email = document.getElementById("email").value; //box
        // var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        // if (!regex.test(email)) {
        //     window.alert("Please submit the correct email address");
        //     // document.getElementById("email").enter.focus();
        //     var process_form = document.getElementsByClassName("draw_form")[0];
        //     process_form.focus();
        //     return false;
        // }
        if (email != ""){
            var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
            if (!regex.test(email)) {
                window.alert("Please submit the correct email address");
                var draw_form = document.getElementsByClassName("draw_form")[0];
                draw_form.focus();
                return false;
            }
        }

        return true;
        
    }

    var download_example = function() {
        const fileUrl = "./example/draw_example/go_enrichment_example.txt"; // 文件的实际路径
        const fileName = "go_enrichment_example.txt"; // 下载时保存的文件名

        const a = document.createElement("a"); // 创建一个 <a> 标签元素
        a.href = fileUrl; // 设置下载链接
        a.download = fileName; // 设置下载文件名
        document.body.appendChild(a); // 将 <a> 标签添加到页面
        a.click(); // 模拟点击 <a> 标签，触发下载
        document.body.removeChild(a); // 删除 <a> 标签，清理DOM
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



</script>


<section id="banner">
    <div class="container padding-medium-2">
        <div class="hero-content">
            <!-- <h2 class="display-2 fw-semibold">About <span class="text-primary"> Us</span></h2> -->
            <h2 class="display-2 fw-semibold">GO and KEGG Enrichment</span></h2>
            <nav class="breadcrumb">
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <a class="breadcrumb-item text-muted nav-link" href="index.php">Data Analysis</a>
                <span class="breadcrumb-item active" aria-current="page">GO and KEGG Enrichment</span>
            </nav>
        </div>
    </div>
</section>


<!-- 上传数据 -->
<section id="service" class="padding-medium">
    <div class="container">
        <form id="form" class="draw_form" name="draw_form" method="post" action="all_analysis_sub2.php" onsubmit="JavaScript: return checkInput()" enctype="multipart/form-data"> <!-- onsubmit="javascript:return checkInput()"-->

            <div class="pb-3" style="margin-bottom: 16px;">
                <label style="margin-bottom: 16px;">Analysis type: </label>  &nbsp;&nbsp;&nbsp;
                <input type="radio" name="type_analysis" value="up" checked> UP DEGs &nbsp;
                <input type="radio" name="type_analysis" value="down"> DOWN DEGs &nbsp; 
                <input type="radio" name="type_analysis" value="all"> ALL DEGs &nbsp; 
            </div>

            <!-- 一审 -->
            <div class="pb-3" style="margin-bottom: 20px;">
                <label style="margin-bottom: 16px;">1. Input threshold for GO enrichment analysis</label>  &nbsp;&nbsp;&nbsp; <br/>
                <label>pvalue (NOTE: The threshold range is [0, 1]) </label>  &nbsp;&nbsp;&nbsp;
                <input  type="text" name="pvalue_go" id="pvalue_go" value="0.1" class="form-control">
                <label>qvalue (NOTE: The threshold range is [0, 1]) </label>  &nbsp;&nbsp;&nbsp;
                <input type="text" name="qvalue_go" id="qvalue_go" value="0.1" class="form-control">
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>2. Plot type of GO enrichment</label>  &nbsp;&nbsp;&nbsp;
                <input type="radio" name="type_go" value="bubble" checked> Bubble &nbsp;
                <input type="radio" name="type_go" value="barplot"> Barplot &nbsp; 
                <input type="radio" name="type_go" value="chord"> Chord &nbsp;
                <input type="radio" name="type_go" value="cluster"> Cluster &nbsp; 
                <input type="radio" name="type_go" value="circle"> Circle &nbsp;
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>3. Correction Method for GO enrichment analysis</label>
                <select class="param_select" id="correction_go" name="correction_go"> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">BH < Benjamini-Hochberg</option>
                    <option value="1">BY < Benjamini-Yekutieli</option>
                    <option value="2">holm < Holm's step-down procedure</option>
                    <option value="3">hochberg < Hochberg's step-up procedure</option>
                    <option value="5">hommel < Hommel's procedure</option>
                    <option value="6">bonferroni < Bonferroni correction</option>
                    <option value="7">fdr < False Discovery Rate</option>
                    <option value="8">none</option>
                </select>
            </div>


            <div class="pb-3" id="termNum_div" style="margin-top: -15px; margin-bottom: 20px;" >
                <label>Input the number of terms for each ontology to be displayed for GO enrichment</label>  &nbsp;&nbsp;&nbsp;
                <input type="text" name="termNum_go" id="termNum_go" value="5" class="form-control">
            </div>


            <!-- 一审 -->
            <div class="pb-3" style="margin-bottom: 20px;">
                <label style="margin-bottom: 16px;">4. Input threshold for KEGG enrichment analysis</label>  &nbsp;&nbsp;&nbsp; <br/>
                <label>pvalue (NOTE: The threshold range is [0, 1]) </label>  &nbsp;&nbsp;&nbsp;
                <input  type="text" name="pvalue_kegg" id="pvalue_kegg" value="0.1" class="form-control">
                <label>qvalue (NOTE: The threshold range is [0, 1]) </label>  &nbsp;&nbsp;&nbsp;
                <input type="text" name="qvalue_kegg" id="qvalue_kegg" value="0.1" class="form-control">
                
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>5. Plot type of KEGG enrichment</label>  &nbsp;&nbsp;&nbsp;
                <input type="radio" name="type_kegg" value="bubble" checked>Bubble &nbsp;
                <input type="radio" name="type_kegg" value="chord"> Chord &nbsp;
                <input type="radio" name="type_kegg" value="cluster"> Cluster &nbsp; 
            </div>

            <div class="pb-3" style="margin-bottom: 20px;">
                <label>6. Correction Method for KEGG enrichment analysis</label>
                <select class="param_select" id="correction_kegg" name="correction_kegg"> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">BH < Benjamini-Hochberg</option>
                    <option value="1">BY < Benjamini-Yekutieli</option>
                    <option value="2">holm < Holm's step-down procedure</option>
                    <option value="3">hochberg < Hochberg's step-up procedure</option>
                    <option value="5">hommel < Hommel's procedure</option>
                    <option value="6">bonferroni < Bonferroni correction</option>
                    <option value="7">fdr < False Discovery Rate</option>
                    <option value="8">none</option>
                </select>
            </div>


            <div class="pb-3" id="termNum_div" style="margin-top: -15px; margin-bottom: 20px;" >
                <label>Input the number of terms for each ontology to be displayed for KEGG enrichment</label>  &nbsp;&nbsp;&nbsp;
                <input type="text" name="termNum_kegg" id="termNum_kegg" value="5" class="form-control">
            </div>

            <div class="pb-3" id="param" style="margin-top: -15px; margin-bottom: 20px;display: none;" >  <!---display: none;-->
                <label>parameters</label>  &nbsp;&nbsp;&nbsp;
                <input type="text" name="jobID" id="jobID" value= "" class="form-control">
                <input type="text" name="org" id="org" value= "" class="form-control">
            </div>




            <div class="pb-3">
                <label>Your Email</label>
                <input type="text" name="email" id="email" placeholder="Write your email here" class="form-control">
            </div>

            <button type="submit" name="submit" class="btn btn-primary  px-5 py-3 mt-2 w-100">Submit</button>

            <!-- <div class="pb-3" style="text-align: center; margin-top: 30px;">
                <label style="margin-bottom: 20px;">Example Figure is as follows:</label><br/>
                <img src="images/go_example.png" alt="img" style="margin: 0 auto; width: 1100px; height: 650px;">
            </div> -->
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