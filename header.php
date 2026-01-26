<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="format-detection" content="telephone=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <!-- 预加载本地优化后的背景图 -->
    <link rel="preload" as="image" href="images/background.png">
    <!-- 设置网站图标 -->
    <link rel="icon" type="image/png" href="/images/vite.svg">
    <title>AutoMATA</title>

    <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/Swiper/9.4.1/swiper-bundle.min.css" />
    <link rel="stylesheet" type="text/css" href="../icomoon/icomoon.css">

    <!-- 下面改变header横向样式 -->
    <!-- 引入bootstrap https://blog.csdn.net/he1234555/article/details/112132229 -->
    <link href="https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0-alpha3/css/bootstrap.min.css" rel="stylesheet"
    integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">


    <link rel="stylesheet" type="text/css" href="css/vendor.css">
    <!-- style.css改变header的字体大小 -->
    <link rel="stylesheet" href="style.css">


    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;600;700&family=Roboto+Slab&display=swap"
    rel="stylesheet">

    <script src="https://code.iconify.design/iconify-icon/1.0.7/iconify-icon.min.js"></script>

    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

    <!-- Bootstrap JS 需要尽早加载以支持导航下拉菜单 -->
    <script src="https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0-alpha3/js/bootstrap.bundle.min.js" integrity="sha384-ENjdO4Dr2bkBIFxQpeoTz1HIcje39Wm4jDKdf19U8gI4ddQ3GYNS7NTKfAdVQSZe" crossorigin="anonymous"></script>
    
    <?php ini_set('max_execution_time', '0'); ?>
     <?php // set_time_limit(0); // 不限制时间?>
    
</head>

<body  oncontextmenu=self.event.returnValue=false>  <!--屏蔽右键  oncontextmenu=self.event.returnValue=false-->
<nav class="main-menu d-flex navbar fixed-top navbar-expand-lg p-2 py-3 p-lg-4 py-lg-4 ">
    <div class="container-fluid">
      <div class="main-logo">
        <a href="index.php"  target="_blank">
          <!-- <img src="images/logo.png" alt="logo" class="img-fluid"> -->
          <img src="https://xxs-img.oss-cn-hangzhou.aliyuncs.com/img202601261643927.png" alt="logo" class="img-fluid" width="220px" height="44px">
        </a>
      </div>
      
      <!-- 这个button干啥的不知道 -->
      <button class="navbar-toggler" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasNavbar"
        aria-controls="offcanvasNavbar">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvasNavbar" aria-labelledby="offcanvasNavbarLabel">

        <div class="offcanvas-header">
          <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>

        <div class="offcanvas-body justify-content-end">

          <ul class="navbar-nav menu-list list-unstyled align-items-lg-center d-flex gap-md-3 mb-0">
            <li class="nav-item">
              <a href="index.php" target="_blank" class="nav-link mx-2 active">Home</a>
            </li>

            <li class="nav-item dropdown">
              <a class="nav-link mx-2 dropdown-toggle align-items-center" role="button" id="pages"
                data-bs-toggle="dropdown" aria-expanded="false">Data Process</a>
              <ul class="dropdown-menu" aria-labelledby="pages">
                <li><a href="genome.php" class="dropdown-item" target="_blank">Genome</a></li>
                <li><a href="transcriptome.php" class="dropdown-item" target="_blank">Transcriptome</a></li>
                <li><a href="protein.php" class="dropdown-item" target="_blank">Protein</a></li>
                <li><a href="integrationPage.php" class="dropdown-item" target="_blank">Integration</a></li> <!--一审-->

              </ul>
            </li>

            <li class="nav-item dropdown">
              <a class="nav-link mx-2 dropdown-toggle align-items-center" role="button" id="courses"
                data-bs-toggle="dropdown" aria-expanded="false">Model</a>
              <ul class="dropdown-menu" aria-labelledby="courses">
                <!-- <li><a href="modelTrainPage.php" class="dropdown-item" target="_blank">Train</a></li>  训练模型 -->
                <!-- <li><a href="modelUsePage.php" class="dropdown-item" target="_blank">Use</a></li>  使用模型 -->
                <li><a href="modelTrainPage.php" class="dropdown-item" target="_blank">Train > supervised</a></li>  <!--训练模型 一审-->
                <li><a href="modelTrainPage_un.php" class="dropdown-item" target="_blank">Train > unsupervised</a></li> <!--  一审 -->
                <li><a href="modelTrainPage_semi.php" class="dropdown-item" target="_blank">Train > semi-supervised</a></li>  <!-- 一审 新增 -->
                <li><a href="modelUsePage.php" class="dropdown-item" target="_blank">Use</a></li>  <!-- 使用模型 -->
              </ul>
            </li>

            <li class="nav-item">
              <a class="nav-link mx-2" href="dataAnalysisPage.php" target="_blank">Data Analyse</a>
            </li>



            <li class="nav-item">
              <a href="help.php" class="nav-link mx-2" target="_blank">Help</a>
            </li>

            <!-- <li class="nav-item">
              <a href="#" class="nav-link mx-2 text-decoration-underline">Button</a>
            </li> -->
          </ul>
          
          <!-- 登陆注册模块 删除div class="d-none d-lg-flex align-items-center ms-5 -->

        </div>
      </div>

    </div>
    <!-- 登录注册按钮 删除div class="container-fluid d-lg-none" -->
  </nav>
      
<!-- </body>
</html> -->