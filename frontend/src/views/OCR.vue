<template>
  <div>
    <el-alert
      v-if="!userStore.hasApiConfig"
      title="请先配置API密钥"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      <template #default>
        请前往 <router-link to="/settings">API配置</router-link> 页面配置OCR和翻译服务的API密钥
      </template>
    </el-alert>

    <el-card>
      <template #header>
        <h3>上传文件进行OCR识别</h3>
      </template>

      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".png,.jpg,.jpeg,.pdf,.docx,.txt"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PNG、JPG、PDF、Word、TXT 格式，文件大小不超过 1GB
          </div>
        </template>
      </el-upload>

      <div v-if="file" style="margin-top: 20px">
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          开始识别
        </el-button>
      </div>

      <!-- Progress display -->
      <el-card v-if="uploading && progressMessage" style="margin-top: 20px">
        <div style="margin-bottom: 10px">
          <strong>{{ progressMessage }}</strong>
        </div>
        <el-progress
          v-if="totalPages > 0"
          :percentage="progressPercentage"
          :status="progressStatus"
        />
      </el-card>
    </el-card>

    <el-card v-if="result" style="margin-top: 20px">
      <template #header>
        <div style="display: flex; justify-content: space-between">
          <h3>OCR结果</h3>
          <el-button type="primary" @click="goToTranslate">翻译此文档</el-button>
        </div>
      </template>

      <div v-for="(page, index) in result.pages" :key="index" class="ocr-result">
        <h4>第 {{ page.page_number }} 页</h4>
        <el-input
          type="textarea"
          v-model="page.text"
          :rows="10"
          readonly
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ocrAPI } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const file = ref(null)
const uploading = ref(false)
const result = ref(null)
const historyId = ref(null)
const progressMessage = ref('')
const currentPage = ref(0)
const totalPages = ref(0)
const progressStatus = ref('')

const progressPercentage = computed(() => {
  if (totalPages.value === 0) return 0
  return Math.round((currentPage.value / totalPages.value) * 100)
})

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
}

const handleUpload = async () => {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  progressMessage.value = '正在上传文件...'
  currentPage.value = 0
  totalPages.value = 0
  result.value = null
  progressStatus.value = ''

  try {
    // 上传文件并自动开始后台处理
    const uploadResult = await ocrAPI.uploadFile(file.value)
    historyId.value = uploadResult.history_id

    progressMessage.value = '文件已上传，后台处理中...'
    ElMessage.success('文件已上传，正在后台处理，您可以关闭此页面')

    // 开始轮询状态
    pollStatus()

  } catch (error) {
    console.error('Upload error:', error)
    progressMessage.value = '上传失败'
    progressStatus.value = 'exception'
    ElMessage.error('OCR处理失败: ' + (error.message || '未知错误'))
    uploading.value = false
  }
}

const pollStatus = async () => {
  if (!historyId.value) return

  try {
    const status = await ocrAPI.getStatus(historyId.value)

    console.log('OCR Status:', status)

    if (status.status === 'COMPLETED') {
      // 处理完成，获取结果
      const ocrResult = await ocrAPI.getResult(historyId.value)
      result.value = ocrResult
      progressMessage.value = '识别完成！'
      progressStatus.value = 'success'
      uploading.value = false
      ElMessage.success('OCR识别完成')
    } else if (status.status === 'FAILED') {
      // 处理失败
      progressMessage.value = '处理失败: ' + (status.error_message || '未知错误')
      progressStatus.value = 'exception'
      uploading.value = false
      ElMessage.error('OCR处理失败: ' + (status.error_message || '未知错误'))
    } else if (status.status === 'PROCESSING') {
      // 处理中，继续轮询
      progressMessage.value = '正在处理中...'
      if (status.total_pages) {
        totalPages.value = status.total_pages
      }
      setTimeout(pollStatus, 2000) // 2秒后再次轮询
    } else if (status.status === 'PENDING') {
      // 等待中
      progressMessage.value = '等待处理...'
      setTimeout(pollStatus, 2000)
    }
  } catch (error) {
    console.error('Poll status error:', error)
    // 如果是网络错误，继续轮询
    if (uploading.value) {
      setTimeout(pollStatus, 3000)
    }
  }
}

const goToTranslate = () => {
  router.push(`/translate/${historyId.value}`)
}
</script>

<style scoped>
.ocr-result {
  margin-bottom: 20px;
}

.ocr-result h4 {
  margin-bottom: 10px;
  color: #409eff;
}
</style>
