<template>
  <div class="loading-spinner" :class="{ 'fullscreen': fullscreen }">
    <div class="spinner-overlay" v-if="fullscreen"></div>
    <div class="spinner-content">
      <div class="spinner" :class="size">
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
      </div>
      <div v-if="text" class="spinner-text">{{ text }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loading?: boolean
  text?: string
  fullscreen?: boolean
  size?: 'small' | 'medium' | 'large'
}

withDefaults(defineProps<Props>(), {
  loading: true,
  text: '',
  fullscreen: false,
  size: 'medium'
})
</script>

<style scoped>
.loading-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
}

.spinner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(2px);
}

.spinner-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10000;
}

.spinner {
  position: relative;
  width: 40px;
  height: 40px;
}

.spinner.small {
  width: 24px;
  height: 24px;
}

.spinner.large {
  width: 64px;
  height: 64px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-radius: 50%;
  animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner.small .spinner-ring {
  border-width: 2px;
}

.spinner.large .spinner-ring {
  border-width: 6px;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
  border-top-color: #0d6efd;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
  border-top-color: #20c997;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
  border-top-color: #fd7e14;
}

.spinner-ring:nth-child(4) {
  animation-delay: 0s;
  border-top-color: #dc3545;
}

.spinner-text {
  margin-top: 12px;
  font-size: 14px;
  color: #6c757d;
  text-align: center;
}

@keyframes spinner-ring {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>