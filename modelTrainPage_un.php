<?php include __DIR__ . '/header.php' ?>

<script type="text/javascript">

    var checkInput = function() {  // 检查后缀名 txt csv excel

        // upload_file_1 训练集，upload_file_2 验证集，upload_file_3 测试集
        if (document.getElementsByClassName("upload_dataset")[0].style.display == ""){
            var files = ["upload_file_1", "upload_file_2", "upload_file_3"];
        }else if (document.getElementsByClassName("split_dataset")[0].style.display == ""){
            var files = ["upload_file_4"];
            var epoch = document.getElementById("ratio").value;
            if (epoch == ""){
                window.alert("Please input Ratio value");
                var train_form = document.getElementsByClassName("train_form")[0];
                train_form.focus();
                return false;
            }
        }else{
            var files = ["upload_file_5", "upload_file_6"];
            var epoch = document.getElementById("ratio").value;
            if (epoch == ""){
                window.alert("Please input Kfold value");
                var train_form = document.getElementsByClassName("train_form")[0];
                train_form.focus();
                return false;
            }
        }

        for (file_id of files){
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
                var train_form = document.getElementsByClassName("train_form")[0];
                train_form.focus();
                return false;
            }
        }


        // 检查epoch、lr、es是否为空值
        var epoch = document.getElementById("epoch").value;
        if (epoch == ""){
            window.alert("Please input Epoch value");
            var train_form = document.getElementsByClassName("train_form")[0];
            train_form.focus();
            return false;
        }
        // window.alert('lr')
        var lr = document.getElementById("lr").value;
        if (lr == ""){
            window.alert("Please input Learning Rate value");
            var train_form = document.getElementsByClassName("train_form")[0];
            train_form.focus();
            return false;
        }
        // window.alert('es')
        var es = document.getElementById("es").value;
        if (es == ""){
            window.alert("Please input EarlyStopping Patience value");
            var train_form = document.getElementsByClassName("train_form")[0];
            train_form.focus();
            return false;
        }
        var lb = document.getElementById("seed").value;
        if (lb == ""){
            window.alert("Please input random seed value");
            var train_form = document.getElementsByClassName("train_form")[0];
            train_form.focus();
            return false;
        }
        // window.alert(files.length)
        if (files.length == 2){
            var kfold = document.getElementById("kfold").value;
            if (kfold == ""){
                window.alert("Please input K-Fold value");
                var train_form = document.getElementsByClassName("train_form")[0];
                train_form.focus();
                return false;
            }
        }
        
        // window.alert('email')
        // 检查邮件格式
        var email = document.getElementById("email").value; //box
        var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        if (!regex.test(email)) {
            window.alert("Please submit the correct email address");
            // document.getElementById("email").enter.focus();
            var process_form = document.getElementsByClassName("train_form")[0];
            process_form.focus();
            return false;
        }
        // if (email != ""){
        //     var regex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i;
        //     if (!regex.test(email)) {
        //         window.alert("Please submit the correct email address");
        //         var train_form = document.getElementsByClassName("train_form")[0];
        //         train_form.focus();
        //         return false;
        //     }
        // }

        return true;
        
    }

    var download_example = function() {
        // window.open("./example/train_example.zip")
        const fileUrl = "./example/train_unsupervised_example.zip"; // 文件的实际路径
        const fileName = "train_unsupervised_example.zip"; // 下载时保存的文件名

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


    function useUpload(){
        var x = document.getElementsByClassName("upload_dataset");
        var i;
        for (i=0; i < x.length; i++){
            x[i].style.display="";
        }
        var x = document.getElementsByClassName("split_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="none";
        }
        var x = document.getElementsByClassName("kfold_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="none";
        }
    }

    function useSplit(){
        var i;
        var x = document.getElementsByClassName("upload_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="none";
        }
        var x = document.getElementsByClassName("split_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="";
        }
        var x = document.getElementsByClassName("kfold_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="none";
        }
    }

    function useKfold(){
        var i;
        var x = document.getElementsByClassName("upload_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="none";
        }
        var x = document.getElementsByClassName("split_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="none";
        }
        var x = document.getElementsByClassName("kfold_dataset");
        for (i=0; i < x.length; i++){
            x[i].style.display="";
        }
    }

    function change(v){
        if(v==0){
            document.getElementById("loss_type_vae").style.display="";
            document.getElementById("loss_type_deep").style.display="none";
        }else if(v==1){
            document.getElementById("loss_type_vae").style.display="none";
            document.getElementById("loss_type_deep").style.display="";
        }
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
            <h2 class="display-2 fw-semibold">Train your unsupervised model</span></h2>
            <nav class="breadcrumb">
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <a class="breadcrumb-item text-muted nav-link" href="index.php">Model</a>
                <span class="breadcrumb-item active" aria-current="page">Train</span>
            </nav>
        </div>
    </div>
</section>

<!-- 上传数据 -->
<section id="service" class="padding-medium">

    <div class="container">
        
        <form id="form" class="train_form" name="train_form" method="post" action="modelTrain_un.php" onsubmit="JavaScript: return checkInput()" enctype="multipart/form-data"> <!-- onsubmit="javascript:return checkInput()"-->
            
            <!-- <div class="pb-3">
                <label>1. Upload training set (Note: The uploaded dataset should not contain label or index columns)</label>
                <input type="file" id="upload_file_1" name="upload_file_1" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example()">Example</button>
            </div>

            <div class="pb-3">
                <label>2. Validation set</label>  &nbsp;&nbsp;&nbsp;
                <input type="radio" name="val" value="set" checked onclick="uploadVal();"> Upload validation set &nbsp;
                <input type="radio" name="val" value="kfold" onclick="useKfold();"> Use K-Fold cross validation method
            </div>
            <div class="pb-3" id="upload_val" style="margin-bottom: 22px; display: ;" >
                <label>Upload validation set</label>
                <input type="file" id="upload_file_2" name="upload_file_2" class="form-control" data-text="Choose your file">
            </div>

            <div class="pb-3" id="kfold_val" style="margin-bottom: 22px; display: none;" >
                <label>Input K value (note: If you want to use 3-Fold cross validation method, then K value is 3.)</label>
                <input type="text" name="kfold" id="kfold" placeholder="3" class="form-control">
            </div>

            <div class="pb-3" style="margin-bottom: 22px;">
                <label>3. Upload testing set</label>
                <input type="file" id="upload_file_3" name="upload_file_3" class="form-control" data-text="Choose your file">
            </div> -->
            <div class="pb-3" style="margin-bottom: 10px; ">
                <label>1. Select strategy and upload files</label> <br/> <br/>
                <input type="radio" name="strategy" value="upload" checked onclick="useUpload();"> Upload train/validation/testing datasets &nbsp;
                <input type="radio" name="strategy" value="split" onclick="useSplit();"> Upload a dataset to conduct train/validation/testing split &nbsp;
                <input type="radio" name="strategy" value="kfold" onclick="useKfold();"> Use stratified K-Fold cross validation method
            </div>
            
            <!--upload training/validation/testing datasets-->
            <div class="pb-3 upload_dataset" style="margin-bottom: -15px;">
                <label>Upload training set (Note: The uploaded dataset should not contain label or index columns)</label>  <!-- 一审-->
                <input type="file" id="upload_file_1" name="upload_file_1" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example()">Example</button>
            </div>

            <div class="pb-3 upload_dataset">
                <label>Upload validation set (Note: The uploaded dataset should not contain label or index columns)</label>
                <input type="file" id="upload_file_2" name="upload_file_2" class="form-control" data-text="Choose your file">
            </div>

            <div class="pb-3 upload_dataset" style="margin-bottom: 22px;">
                <label>Upload testing set (Note: The uploaded dataset should not contain label or index columns)</label>
                <input type="file" id="upload_file_3" name="upload_file_3" class="form-control" data-text="Choose your file">
            </div>

            <div class="pb-3 split_dataset" style="margin-bottom: -18px; display: none;">
                <label>Upload a dataset (Note: The uploaded dataset should not contain label or index columns)</label>
                <input type="file" id="upload_file_4" name="upload_file_4" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example()">Example</button>
            </div>

            <div class="pb-3 split_dataset" style="margin-bottom: 22px; display: none;" >
                <label>Input a ratio of training:validation:testing (NOTE: The separator is a colon ':')</label>
                <input type="text" name="ratio" id="ratio" value="8:1:1" class="form-control">
            </div>


            <!--KFold-->
            <div class="pb-3 kfold_dataset" style="margin-bottom: -18px; display: none;">
                <label>Upload training set (Note: The uploaded dataset should not contain label or index columns)</label>
                <input type="file" id="upload_file_5" name="upload_file_5" class="form-control example" data-text="Choose your file">
                <button type="button" class="btn btn-primary example" onclick="download_example()">Example</button>
            </div>

            <div class="pb-3 kfold_dataset" id="kfold_val" style="display: none;" >
                <label>Input K value (NOTE: If you want to use 3-Fold cross validation method, then K value is 3.)</label>
                <input type="text" name="kfold" id="kfold" value="3" class="form-control">
            </div>

            <div class="pb-3 kfold_dataset" style="margin-bottom: 22px; display: none;">
                <label>Upload testing set (Note: The uploaded dataset should not contain label or index columns)</label>
                <input type="file" id="upload_file_6" name="upload_file_6" class="form-control" data-text="Choose your file">
            </div>


            
            <div class="pb-3" style="margin-bottom: 22px;">
                <label>2. Choose model</label> <br>
                <!-- 一审 -->
                <select class="param_select" id="first" name="model_type" onChange="change(this.value)"> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">VAE > Variational Autoencoder VAE can generate new samples by learning the probability distribution of the data</option>
                    <option value="1">DeepCluster > Combining k-means and neural networks to cluster data</option>
                    <!-- <option value="2">All > All the above models are trained in parallel with the same set of data</option> -->
                </select>
            </div>

            <div class="pb-3">
                <label>3. Upload training hyperparameters</label> <br>
            </div>
            <div class="pb-3">
                <label>(1) Epoch</label>
                <input type="text" name="epoch" id="epoch" value="10" class="form-control">
            </div>
            <div class="pb-3">
                <label>(2) Learning Rate</label>
                <input type="text" name="lr" id="lr" value="0.001" class="form-control">
            </div>
            <div class="pb-3">
                <label>(3) EarlyStopping Patience</label>
                <input type="text" name="es" id="es" value="5" class="form-control">
            </div>
            <div class="pb-3">
                <label>(4) Batch Size</label>
                <input type="text" name="bs" id="bs" value="32" class="form-control">
            </div>
            <div class="pb-3">
                <label>(5) Random Seed</label>
                <input type="text" name="seed" id="seed" value="42" class="form-control">
            </div>
            <div class="pb-3">
                <label>(6) Loss Function</label>
                <select class="param_select" id="loss_type_vae" name="loss_type_vae""> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">MSE</option>
                    <option value="1">MAE</option>
                    <option value="2">Smooth L1</option>
                    <option value="3">Focal Loss</option>
                    <option value="4">Contrastive Loss</option>
                    <option value="5">Spectral Loss</option>
                    <option value="6">Wasserstein Loss</option>
                    <option value="7">Perceptual Loss</option>
                    <option value="8">Cosine Loss</option>
                    <option value="9">KL Divergence</option>
                    <option value="10">Regularization Loss</option>
                    <option value="11">BCE</option>
                    <option value="12">Huber Loss</option>
                    <option value="13">InfoNCE</option>
                </select>
            <!-- </div>

            <div class="pb-3" style="display: none;">
                <label>(6) Loss Function</label> -->
                <select class="param_select" id="loss_type_deep" name="loss_type_deep"" style="display: none;"> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">Basic DeepCluster Loss</option>
                    <option value="1">Combining Multiple Clustering Losses</option>
                    <option value="2">Center Loss</option>
                    <option value="3">Contrastive Loss</option>
                    <option value="4">Spectral Loss</option>
                    <option value="5">Entropy Loss</option>
                    <option value="6">Compactness Loss</option>
                    <option value="7">Separation Loss</option>
                </select>
            </div>


            <div class="pb-3" style="margin-bottom: 22px;">
                <label>(7) Optimizer</label>
                <select class="param_select" id="third" name="opz_type""> <!-- style="font-size:17px; font-style:italic; -->
                    <option selected="selected" value="0">Adam</option>
                    <option value="1">SGD</option>
                    <option value="2">AdamW</option>
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