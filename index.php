<?php include __DIR__ . '/header.php' ?>

<!-- 自己改图片 和 title 还没实现搜索Job功能<form id="form" class="d-flex justify-content-between position-relative" -->
<section id="hero">
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-8 col-lg-3 offset-md-2 padding-large ps-lg-0 pe-lg-5">
                <!-- <h2 class="display-2 fw-semibold">Analyze multi-omics data with computational AI</h2> -->
                <h2 class="display-2 fw-semibold" id="title" style="margin-top: -100px;">AutoMATA: a deep learning-enhanced bioinformatics platform for multi-omics data processing, exploration and modelling</h2>
                <!-- <p class="secondary-font my-4 pb-2">平台介绍</p>  -->
                <!-- <div>
                    <form id="form" class="d-flex justify-content-between position-relative"> -->
                        <!-- <input type="text" name="email" placeholder="Search Your Job using JobID" class="form-control w-100"> -->
                        <!-- <button class="btn btn-primary px-4 py-2 position-absolute end-0" style="height: -webkit-fill-available;"><iconify-icon icon="ion:search" class="fs-4 py-1" style="vertical-align: middle;"></iconify-icon></button> -->
                        <button type="submit" class="btn btn-primary  px-5 py-3 mt-2 w-100" onclick="window.open('analysis_train.php')">GO to train and analysis</button>
                    <!-- </form>
                </div> -->

            </div>
            <div class="col-md-6 col-lg-7 d-block d-md-none d-lg-block p-0">
                <!-- <img src="images/billboard-img.jpg" alt="img" class="img-fluid"> -->
                <img src="https://xxs-img.oss-cn-hangzhou.aliyuncs.com/img202601261354486.png" alt="img" class="img-fluid">
            </div>
        </div>
    </div>
</section>

<!-- 自己改为 每个模块的功能介绍 -->
<section id="service" class="padding-medium">
    <div class="container">
        <div class="text-center">
            <!-- <h2 class="display-5 fw-semibold">Why to <span class="text-primary"> choose us</span></h2> -->
            <h2 class="display-5 fw-semibold">We provide</h2>
            <!-- <p class="secondary-font">Get many features from us exactly what you are looking for.</p> -->
        </div>

        <div class="row g-md-4 mt-2">
            <div class="col-md-4 mt-4">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="fluent:notepad-person-24-regular"></iconify-icon>
                    </div>

                    <div class="ps-3">
                        <h4 class="py-2 m-0">Data Process</h4>
                        <p>Data processing functions for gene, mRNA, protein expression data </p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mt-4">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="la:certificate"></iconify-icon>
                    </div>

                    <div class="ps-3">
                        <h4 class="py-2 m-0">Model</h4>
                        <p>Training and application of deep learning models</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mt-4">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="mdi:virtual-meeting"></iconify-icon>
                    </div>

                    <div class="ps-3">
                        <h4 class="py-2 m-0">Data Analyse</h4>
                        <p>Multiple data visualisation and analysis functions</p>
                    </div>
                </div>
            </div>


        </div>


        <div class="text-center" style="margin-top: 50px;">
            <!-- <h2 class="display-5 fw-semibold">Why to <span class="text-primary"> choose us</span></h2> -->
            <h2 class="display-5 fw-semibold">Visitor map</h2>
            <!-- <p class="secondary-font">Get many features from us exactly what you are looking for.</p> -->
        </div>

        <div style="height: 200px; width: 1320px; justify-content: center; display: flex; align-items: center;">
            <!-- <script type="text/javascript" id="mapmyvisitors" src="//mapmyvisitors.com/map.js?d=1TQ78vsdHNfZUbF05j2pZNDFqKuRfJibShpoQVkLxrM&cl=ffffff&w=a"></script> -->
             <div style="height: 160px; width: 200px;">
                <script type="text/javascript" id="mmvst_globe" src="//mapmyvisitors.com/globe.js?d=cqZLq_ySx-fpAgoz0lOwvqtxCyvs3kjVSQmT9tr-SHA"></script>
                <!-- <a href="https://mapmyvisitors.com/web/1c0h6"  title="Visit tracker"><img src="https://mapmyvisitors.com/map.png?d=1TQ78vsdHNfZUbF05j2pZNDFqKuRfJibShpoQVkLxrM&cl=ffffff" /></a> -->
             </div>
        </div>





    </div>
</section>



 <!-- 自己改为 多少个组学、多少数据分析功能、模型 -->
<!-- <section id="achivement" style="background-color: #f5f5f5;">
    <div class="container padding-medium">
        <div class="row">
            <div class="col-md-3">
                <div class="text-center">
                    <img src="images/topic.png" alt="img" class="img-fluid">
                    <h4 class="py-2 mt-3 m-0">Multi-Omics</h4>
                    <p class="text-uppercase">Multiple omics data</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <img src="images/student.png" alt="img" class="img-fluid">
                    <h4 class="py-2 mt-3 m-0">Model</h4>
                    <p class="text-uppercase">Train your own model</p>
                    <p class="text-uppercase">Use our model to predict</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <img src="images/instruction.png" alt="img" class="img-fluid">
                    <h4 class="py-2 mt-3 m-0">Data Analysis</h4>
                    <p class="text-uppercase">Mutiple data analysis functions</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <img src="images/award.png" alt="img" class="img-fluid">
                    <h4 class="py-2 mt-3 m-0">Comprehensive</h4>
                    <p class="text-uppercase">Comprehensive Platform</p>
                </div>
            </div>

        </div>
    </div>
</section>
 -->

<?php include __DIR__ . '/footer.php' ?>