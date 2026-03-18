<template>
  <div class="task-detail-container">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">任务详情</span>
      </template>
    </el-page-header>
    <el-card class="mt-4">
      <el-result icon="info" title="任务详情" sub-title="任务详情功能正在开发中">
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
const taskId = route.params.id

function goBack() {
  router.back()
}
</script>

<style scoped>
.task-detail-container {
  padding: 20px;
}
.mt-4 {
  margin-top: 16px;
}
</style>
