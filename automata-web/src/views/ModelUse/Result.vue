<template>
  <div class="result-container">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">模型使用结果</span>
      </template>
    </el-page-header>
    <el-card class="mt-4">
      <div v-if="loading" class="text-center">
        <el-skeleton :rows="6" animated />
      </div>
      <div v-else>
        <el-result
          icon="info"
          :title="jobStatusTitle"
          :sub-title="jobSubtitle"
        >
          <template #extra>
            <el-button type="primary" @click="goBack">返回上一页</el-button>
            <el-button
              v-if="downloadUrl"
              type="success"
              :href="downloadUrl"
              target="_blank"
            >
              下载结果（zip）
            </el-button>
          </template>
        </el-result>

        <div v-if="jobError" class="mt-3 text-danger">
          {{ jobError }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { jobsApi } from '@/api/jobs'

const route = useRoute()
const router = useRouter()
const resultId = route.params.id

const loading = ref(true)
const jobStatus = ref<string>('Submitted')
const jobError = ref<string>('')
const downloadUrl = ref<string>('')

const jobStatusTitle = computed(() => {
  if (jobStatus.value === 'Completed') return '模型应用完成'
  if (jobStatus.value === 'Failed') return '模型应用失败'
  if (jobStatus.value === 'Cancelled') return '模型应用已取消'
  return '模型应用进行中'
})

const jobSubtitle = computed(() => {
  if (jobStatus.value === 'Completed') return '结果已生成，可以下载查看'
  if (jobStatus.value === 'Failed') return '请查看错误信息后重新提交'
  if (jobStatus.value === 'Cancelled') return '任务已取消'
  return `当前状态：${jobStatus.value}`
})

function goBack() {
  router.back()
}

onMounted(async () => {
  try {
    loading.value = true
    if (!resultId) return

    const task = await jobsApi.getJobDetail(resultId as string)
    jobStatus.value = task.status
    jobError.value = task.error_message || ''

    if (task.status === 'Completed') {
      downloadUrl.value = await jobsApi.getDownloadUrl(resultId as string)
    }
  } catch (e: any) {
    console.error('加载结果失败:', e)
    jobError.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.result-container {
  padding: 20px;
}
.mt-4 {
  margin-top: 16px;
}
</style>
