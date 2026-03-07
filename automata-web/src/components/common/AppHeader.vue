<template>
  <nav class="main-menu d-flex navbar fixed-top navbar-expand-lg p-2 py-3 p-lg-4 py-lg-4">
    <div class="container-fluid">
      <div class="main-logo">
        <router-link to="/" class="navbar-brand">
          <img 
            :src="logoPath" 
            alt="AutoMATA Logo" 
            class="img-fluid" 
            width="220" 
            height="44"
          >
        </router-link>
      </div>
      
      <button 
        class="navbar-toggler" 
        type="button" 
        data-bs-toggle="offcanvas" 
        data-bs-target="#offcanvasNavbar"
        aria-controls="offcanvasNavbar"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div 
        class="offcanvas offcanvas-end" 
        tabindex="-1" 
        id="offcanvasNavbar" 
        aria-labelledby="offcanvasNavbarLabel"
      >
        <div class="offcanvas-header">
          <button 
            type="button" 
            class="btn-close" 
            data-bs-dismiss="offcanvas" 
            aria-label="Close"
          ></button>
        </div>

        <div class="offcanvas-body justify-content-end">
          <ul class="navbar-nav menu-list list-unstyled align-items-lg-center d-flex gap-md-3 mb-0">
            <li class="nav-item">
              <router-link 
                to="/" 
                class="nav-link mx-2" 
                :class="{ active: $route.name === 'home' }"
              >
                Home
              </router-link>
            </li>

            <li class="nav-item dropdown">
              <a 
                class="nav-link mx-2 dropdown-toggle align-items-center" 
                role="button" 
                id="dataProcessDropdown"
                data-bs-toggle="dropdown" 
                aria-expanded="false"
              >
                Data Process
              </a>
              <ul class="dropdown-menu" aria-labelledby="dataProcessDropdown">
                <li>
                  <router-link 
                    to="/data-process/genome" 
                    class="dropdown-item"
                  >
                    Genome
                  </router-link>
                </li>
                <li>
                  <router-link 
                    to="/data-process/transcriptome" 
                    class="dropdown-item"
                  >
                    Transcriptome
                  </router-link>
                </li>
                <li>
                  <router-link 
                    to="/data-process/protein" 
                    class="dropdown-item"
                  >
                    Protein
                  </router-link>
                </li>
                <li>
                  <router-link 
                    to="/data-process/integration" 
                    class="dropdown-item"
                  >
                    Integration
                  </router-link>
                </li>
              </ul>
            </li>

            <li class="nav-item dropdown">
              <a 
                class="nav-link mx-2 dropdown-toggle align-items-center" 
                role="button" 
                id="modelDropdown"
                data-bs-toggle="dropdown" 
                aria-expanded="false"
              >
                Model
              </a>
              <ul class="dropdown-menu" aria-labelledby="modelDropdown">
                <li>
                  <router-link 
                    to="/model/train/supervised" 
                    class="dropdown-item"
                  >
                    Train > supervised
                  </router-link>
                </li>
                <li>
                  <router-link 
                    to="/model/train/unsupervised" 
                    class="dropdown-item"
                  >
                    Train > unsupervised
                  </router-link>
                </li>
                <li>
                  <router-link 
                    to="/model/train/semi-supervised" 
                    class="dropdown-item"
                  >
                    Train > semi-supervised
                  </router-link>
                </li>
                <li>
                  <router-link 
                    to="/model/use" 
                    class="dropdown-item"
                  >
                    Use
                  </router-link>
                </li>
              </ul>
            </li>

            <li class="nav-item">
              <router-link 
                to="/analysis" 
                class="nav-link mx-2"
                :class="{ active: $route.path.startsWith('/analysis') }"
              >
                Data Analyse
              </router-link>
            </li>

            <li class="nav-item">
              <router-link 
                to="/help" 
                class="nav-link mx-2"
                :class="{ active: $route.name === 'help' }"
              >
                Help
              </router-link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// <!-- 
// 审查上下文：
// - 设计意图：使用环境变量配置Logo路径，避免硬编码外部资源URL
// - 已知局限：当前使用本地相对路径，在生产环境中需要配置CDN路径
// - 业务背景：提高应用安全性和可靠性，避免外部依赖
// - 测试重点：验证不同环境下的Logo加载是否正常
// -->
const logoPath = computed(() => {
  return import.meta.env.VITE_LOGO_PATH || '/images/logo.png'
})
</script>

<style scoped>
.main-menu {
  background-color: white !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1050;
}

.navbar-brand img {
  max-height: 44px;
  width: auto;
}

.nav-link {
  font-weight: 500;
  color: #333 !important;
  transition: color 0.2s ease;
}

.nav-link:hover,
.nav-link.active {
  color: #0d6efd !important;
}

.dropdown-menu {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
}

.dropdown-item {
  padding: 0.5rem 1.5rem;
  transition: background-color 0.2s ease;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.offcanvas {
  background-color: white;
}

/* 响应式调整 */
@media (max-width: 991.98px) {
  .main-menu {
    padding: 0.5rem 1rem;
  }
}
</style>