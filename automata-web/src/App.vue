<script setup lang="ts">
import Header from './components/Header.vue'
import Footer from './components/Footer.vue'
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <Header />
    <main class="main-content">
      <RouterView />
    </main>
    <Footer />
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  margin-top: 100px;
  /* 为固定页眉留出更多空间 */
  width: 100%;
}

/* 响应式调整 */
@media (max-width: 991.98px) {
  .main-content {
    margin-top: 90px;
  }
}

@media (max-width: 767.98px) {
  .main-content {
    margin-top: 80px;
  }
}
</style>
