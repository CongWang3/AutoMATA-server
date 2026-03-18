<template>
    <footer id="footer" class="bg-white text-dark">
        <div class="container padding-medium">
            <div class="row">
                <!-- 联系信息 -->
                <div class="col-md-4 my-3">
                    <h5 class="text-uppercase fw-bold mb-4">Contact us</h5>
                    <p>
                        <i class="fas fa-map-marker-alt social-icon text-primary fs-5 me-2"
                            style="vertical-align:text-bottom"></i>
                        <span class="fw-bold">Address: </span> Northwest A&F University
                    </p>
                    <p>
                        <i class="fas fa-envelope social-icon text-primary fs-5 me-2"
                            style="vertical-align:text-bottom"></i>
                        <span class="fw-bold">Email: </span>
                        wangc@nwsuaf.edu.cn <br />
                        &emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;fuyi.li@nwafu.edu.cn
                    </p>
                </div>

                <!-- 链接菜单 -->
                <div class="col-md-2 my-3">
                    <div class="footer-menu">
                        <h5 class="text-uppercase fw-bold mb-4">Links</h5>
                        <ul class="menu-list list-unstyled">
                            <li class="menu-item mb-2">
                                <a href="/" class="footer-link">Home</a>
                            </li>
                            <li class="menu-item mb-2">
                                <a href="/data-process/genome" class="footer-link">Data Process</a>
                            </li>
                            <li class="menu-item mb-2">
                                <a href="/model/train/supervised" class="footer-link">Model</a>
                            </li>
                            <li class="menu-item mb-2">
                                <a href="/data-analysis" class="footer-link">Data Analyse</a>
                            </li>
                            <li class="menu-item mb-2">
                                <a href="/help" class="footer-link">Help</a>
                            </li>
                        </ul>
                    </div>
                </div>

                <!-- 文章链接 -->
                <div class="col-md-2 my-3">
                    <div class="footer-menu">
                        <h5 class="text-uppercase fw-bold mb-4">article</h5>
                        <ul class="menu-list list-unstyled">
                            <li class="menu-item mb-2">
                                <a href="https://github.com/ABILiLab/AutoMATA" target="_blank">AutoMATA</a>
                            </li>
                        </ul>
                    </div>
                </div>

                <!-- 社交媒体 -->
                <div class="col-md-3 my-3">
                    <div class="footer-menu">
                        <h5 class="text-uppercase fw-bold mb-4">Follow us</h5>
                        <div class="social-links mt-4">
                            <ul class="d-flex list-unstyled gap-3">
                                <li class="social">
                                    <a href="https://www.facebook.com/home.php">
                                        <i class="fab fa-facebook-f social-icon fs-4"></i>
                                    </a>
                                </li>
                                <li class="social">
                                    <a href="https://x.com/i/flow/login">
                                        <i class="fab fa-twitter social-icon fs-4"></i>
                                    </a>
                                </li>
                                <li class="social">
                                    <a href="https://www.pinterest.com/#top">
                                        <i class="fab fa-pinterest-p social-icon fs-4"></i>
                                    </a>
                                </li>
                                <li class="social">
                                    <a href="https://www.instagram.com/">
                                        <i class="fab fa-instagram social-icon fs-4"></i>
                                    </a>
                                </li>
                                <li class="social">
                                    <a href="https://www.youtube.com/">
                                        <i class="fab fa-youtube social-icon fs-4"></i>
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 版权信息
        <div class="copyright-section py-3 border-top">
            <div class="container">
                <div class="row">
                    <div class="col-12 text-center">
                        <p class="mb-0 text-muted">
                            &copy; {{ currentYear }} AutoMATA. All rights reserved.
                        </p>
                    </div>
                </div>
            </div>
        </div> -->
    </footer>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'

export default defineComponent({
    name: 'Footer',
    setup() {
        const currentYear = ref(new Date().getFullYear())

        onMounted(() => {
            // 可以在这里添加任何需要在组件挂载后执行的逻辑
        })

        return {
            currentYear
        }
    }
})
</script>

<style scoped>
#footer {
    margin-top: auto;
}

.row {
    /* align-items: center; */
    justify-content: center;
    margin-left: 3%;
}


/* 确保所有链接悬停时只改变文字颜色 */
.footer-link {
    color: inherit;
    text-decoration: none;
    transition: color 0.3s ease;
}

.footer-link:hover {
    color: #198754 !important;
    background-color: transparent !important;
}

.social-icon {
    transition: transform 0.3s ease, color 0.3s ease;
}

.social-icon:hover {
    transform: translateY(-2px);
    color: #198754 !important;
}

.social a {
    color: inherit;
    transition: color 0.3s ease;
}

.social a:hover {
    color: #198754 !important;
    background-color: transparent !important;
}

.copyright-section {
    background-color: rgba(0, 0, 0, 0.05);
}

.padding-medium {
    padding-top: 3rem;
    padding-bottom: 3rem;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .padding-medium {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .my-3 {
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    h5 {
        font-size: 1.1rem;
    }
}
</style>