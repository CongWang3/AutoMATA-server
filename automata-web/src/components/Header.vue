<template>
    <nav class="main-menu d-flex navbar fixed-top navbar-expand-lg p-2 py-3 p-lg-4 py-lg-4"
        :class="{ 'scrolled': isScrolled }">
        <div class="container-fluid">
            <div class="main-logo">
                <a href="/" class="navbar-brand">
                    <img src="https://xxs-img.oss-cn-hangzhou.aliyuncs.com/img202601261643927.png" alt="AutoMATA Logo"
                        class="img-fluid" width="220" height="44">
                </a>
            </div>

            <!-- 移动端切换按钮 -->
            <button class="navbar-toggler" type="button" @click="toggleMobileMenu" :aria-expanded="isMobileMenuOpen">
                <span class="navbar-toggler-icon"></span>
            </button>

            <!-- 导航菜单 -->
            <div class="collapse navbar-collapse" :class="{ show: isMobileMenuOpen }">
                <ul class="navbar-nav menu-list list-unstyled align-items-lg-center d-flex gap-md-3 mb-0 ms-auto">
                    <li class="nav-item">
                        <a href="/" class="nav-link mx-2 active">
                            Home
                        </a>
                    </li>

                    <li class="nav-item dropdown">
                        <a class="nav-link mx-2 dropdown-toggle" role="button" @click="toggleDropdown('data')"
                            @blur="hideDropdown('data')">
                            Data Process
                        </a>
                        <ul class="dropdown-menu" :class="{ show: activeDropdown === 'data' }">
                            <li><a href="/data-process/genome" class="dropdown-item">Genome</a></li>
                            <li><a href="/data-process/transcriptome" class="dropdown-item">Transcriptome</a></li>
                            <li><a href="/data-process/protein" class="dropdown-item">Protein</a></li>
                            <li><a href="/data-process/integration" class="dropdown-item">Integration</a></li>
                            <li><a href="/data-process/pvalue-integration" class="dropdown-item">pvalue Integration</a></li>
                        </ul>
                    </li>

                    <li class="nav-item dropdown">
                        <a class="nav-link mx-2 dropdown-toggle" role="button" @click="toggleDropdown('model')"
                            @blur="hideDropdown('model')">
                            Model
                        </a>
                        <ul class="dropdown-menu" :class="{ show: activeDropdown === 'model' }">
                            <li><a href="/model/train/supervised" class="dropdown-item">Train > supervised</a></li>
                            <li><a href="/model/train/unsupervised" class="dropdown-item">Train > unsupervised</a></li>
                            <li><a href="/model/train/semi-supervised" class="dropdown-item">Train > semi-supervised</a>
                            </li>
                            <li><a href="/model/use" class="dropdown-item">Use</a></li>
                        </ul>
                    </li>

                    <li class="nav-item dropdown">
                        <a class="nav-link mx-2 dropdown-toggle" role="button" @click="toggleDropdown('analysis')"
                            @blur="hideDropdown('analysis')">
                            Data Analysis
                        </a>
                        <ul class="dropdown-menu" :class="{ show: activeDropdown === 'analysis' }">
                            <li><a href="/data-analysis" class="dropdown-item">All Analysis Tools</a></li>
                            <li class="dropdown-divider"></li>
                            <li><a href="/data-analysis/pca" class="dropdown-item">PCA</a></li>
                            <li><a href="/data-analysis/heatmap" class="dropdown-item">Correlation Heatmap</a></li>
                            <li><a href="/data-analysis/volcano" class="dropdown-item">Volcano Plot</a></li>
                            <li><a href="/data-analysis/venn" class="dropdown-item">Venn Diagram</a></li>
                            <li><a href="/data-analysis/cluster" class="dropdown-item">Gene Cluster Heatmap</a></li>
                            <li class="dropdown-divider"></li>
                            <li><a href="/data-analysis/go" class="dropdown-item">GO Enrichment</a></li>
                            <li><a href="/data-analysis/kegg" class="dropdown-item">KEGG Enrichment</a></li>
                            <li><a href="/data-analysis/ppi" class="dropdown-item">PPI Network</a></li>
                            <li class="dropdown-divider"></li>
                            <li><a href="/data-analysis/comprehensive" class="dropdown-item">Comprehensive Analysis</a></li>
                        </ul>
                    </li>

                    <li class="nav-item">
                        <a href="/help" class="nav-link mx-2">
                            Help
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isMobileMenuOpen = ref(false)
const activeDropdown = ref('')
const isScrolled = ref(false)

const handleScroll = () => {
    isScrolled.value = window.scrollY > 50
}

onMounted(() => {
    window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll)
})

const toggleMobileMenu = () => {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
    activeDropdown.value = ''
}

const toggleDropdown = (dropdownName: string) => {
    if (activeDropdown.value === dropdownName) {
        activeDropdown.value = ''
    } else {
        activeDropdown.value = dropdownName
    }
}

const hideDropdown = (dropdownName: string) => {
    setTimeout(() => {
        if (activeDropdown.value === dropdownName) {
            activeDropdown.value = ''
        }
    }, 150)
}
</script>

<style scoped>
.main-menu {
    background-color: transparent !important;
    z-index: 1050;
    transition: background-color 0.3s ease;
}

.main-menu.scrolled {
    background-color: white !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.navbar-brand img {
    max-height: 44px;
    width: auto;
}

.nav-link {
    color: #333 !important;
    font-weight: 500;
    transition: all 0.3s ease;
    cursor: pointer;
}

.nav-link:hover,
.nav-link.active {
    color: #0d6efd !important;
}

.dropdown-menu {
    border: none;
    border-radius: 8px;
    margin-top: 0.5rem;
}

.dropdown-item {
    padding: 0.5rem 1.5rem;
    transition: all 0.2s ease;
}

.dropdown-item:hover {
    background-color: #f8f9fa;
    color: #0d6efd;
}

.dropdown-divider {
    height: 0;
    margin: 0.5rem 0;
    overflow: hidden;
    border-top: 1px solid #e9ecef;
}

/* 移动端适配 */
@media (max-width: 991.98px) {
    .navbar-collapse {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem;
    }

    .menu-list {
        flex-direction: column !important;
        align-items: flex-start !important;
    }

    .nav-item {
        width: 100%;
        margin-bottom: 0.5rem;
    }

    .dropdown-menu {
        position: static;
        transform: none !important;
        box-shadow: none;
        border: 1px solid #eee;
        margin-top: 0.25rem;
    }
}

/* 桌面端下拉菜单悬停效果 */
@media (min-width: 992px) {
    .dropdown:hover .dropdown-menu {
        display: block;
    }
}
</style>