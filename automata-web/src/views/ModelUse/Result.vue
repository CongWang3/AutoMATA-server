<template>
  <div class="result-container">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">模型使用结果</span>
      </template>
    </el-page-header>
    <el-card class="mt-4">
      <el-result icon="info" title="模型使用结果" sub-title="模型使用结果功能正在开发中">
        <template #extra>
          <el-button type="primary" @click="goBack">返回上一页</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const resultId = route.params.id

function goBack() {
  router.back()
}
</script>

<style scoped>
.result-container {
  padding: 20px;
}
.mt-4 {
  margin-top: 16px;
}
</style>
