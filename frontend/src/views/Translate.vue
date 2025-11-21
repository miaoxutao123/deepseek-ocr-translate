<template>
  <div class="translate-container">
    <el-card>
      <template #header>
        <h2>文档翻译</h2>
      </template>

      <!-- 选择翻译源 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Tab 1: 从历史记录翻译 -->
        <el-tab-pane label="从历史记录翻译" name="history">
          <el-form label-width="120px">
            <el-form-item label="选择 OCR 任务">
              <el-select
                v-model="selectedHistoryId"
                placeholder="请选择已完成的 OCR 任务"
                filterable
                @change="loadOCRResult"
                style="width: 100%"
              >
                <el-option
                  v-for="item in ocrHistories"
                  :key="item.id"
                  :label="`${item.id} - ${item.original_filename}`"
                  :value="item.id"
                >
                  <span>{{ item.original_filename }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    {{ formatTime(item.completed_at) }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="源语言">
              <el-select v-model="sourceLanguage" style="width: 200px">
                <el-option label="自动检测" value="auto" />
                <el-option label="英语" value="en" />
                <el-option label="中文" value="zh" />
                <el-option label="日语" value="ja" />
                <el-option label="韩语" value="ko" />
              </el-select>
            </el-form-item>

            <el-form-item label="目标语言">
              <el-select v-model="targetLanguage" style="width: 200px">
                <el-option label="中文" value="zh" />
                <el-option label="英语" value="en" />
                <el-option label="日语" value="ja" />
                <el-option label="韩语" value="ko" />
              </el-select>
            </el-form-item>

            <!-- OCR 结果编辑 -->
            <el-form-item label="OCR 结果" v-if="ocrText">
              <div class="ocr-edit-header">
                <el-switch
                  v-model="isEditing"
                  active-text="编辑模式"
                  inactive-text="只读模式"
                  :disabled="translating"
                />
              </div>
              <el-input
                type="textarea"
                :rows="12"
                v-model="ocrText"
                :readonly="!isEditing"
                placeholder="OCR 识别结果将显示在这里，可切换为编辑模式修改"
                :class="{ 'editable-textarea': isEditing }"
              />
              <div class="ocr-tips" v-if="isEditing">
                <el-text type="info" size="small">
                  提示：可以手动修改识别错误的内容，段落之间用空行分隔
                </el-text>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startTranslation"
                :loading="translating && !paused"
                :disabled="!selectedHistoryId || (translating && !paused)"
              >
                {{ getStartButtonText() }}
              </el-button>
              <el-button
                v-if="translating"
                :type="paused ? 'success' : 'warning'"
                @click="togglePause"
              >
                {{ paused ? '继续翻译' : '暂停翻译' }}
              </el-button>
              <el-button
                v-if="translating || translationResults.length > 0"
                type="danger"
                @click="stopTranslation"
              >
                停止翻译
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Tab 2: 直接输入文本翻译 -->
        <el-tab-pane label="直接输入文本" name="text">
          <el-form label-width="120px">
            <el-form-item label="输入文本">
              <el-input
                type="textarea"
                :rows="12"
                v-model="inputText"
                placeholder="请输入需要翻译的文本"
                :disabled="translating"
              />
            </el-form-item>

            <el-form-item label="源语言">
              <el-select v-model="sourceLanguage" style="width: 200px">
                <el-option label="自动检测" value="auto" />
                <el-option label="英语" value="en" />
                <el-option label="中文" value="zh" />
                <el-option label="日语" value="ja" />
                <el-option label="韩语" value="ko" />
              </el-select>
            </el-form-item>

            <el-form-item label="目标语言">
              <el-select v-model="targetLanguage" style="width: 200px">
                <el-option label="中文" value="zh" />
                <el-option label="英语" value="en" />
                <el-option label="日语" value="ja" />
                <el-option label="韩语" value="ko" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startTranslation"
                :loading="translating && !paused"
                :disabled="!inputText || (translating && !paused)"
              >
                {{ getStartButtonText() }}
              </el-button>
              <el-button
                v-if="translating"
                :type="paused ? 'success' : 'warning'"
                @click="togglePause"
              >
                {{ paused ? '继续翻译' : '暂停翻译' }}
              </el-button>
              <el-button
                v-if="translating || translationResults.length > 0"
                type="danger"
                @click="stopTranslation"
              >
                停止翻译
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <!-- 翻译进度和实时结果 -->
      <div v-if="translating || translationResults.length > 0" class="translation-progress">
        <el-divider content-position="left">
          <h3>翻译进度</h3>
        </el-divider>

        <!-- 进度条 -->
        <div class="progress-section">
          <el-progress
            :percentage="progressPercentage"
            :status="progressStatus"
            :format="() => `${currentSentence}/${totalSentences}`"
          />
          <p class="progress-message">
            {{ progressMessage }}
            <el-tag v-if="paused" type="warning" size="small" style="margin-left: 10px">已暂停</el-tag>
          </p>
        </div>

        <!-- 实时翻译结果 -->
        <div class="realtime-results">
          <div class="results-header">
            <h4>翻译结果 (实时更新)</h4>
            <el-button
              v-if="!translating && translationResults.length > 0"
              size="small"
              type="primary"
              @click="copyAllTranslations"
            >
              复制全部译文
            </el-button>
          </div>

          <div class="translation-pairs">
            <div
              v-for="(pair, index) in translationResults"
              :key="index"
              class="sentence-pair"
              :class="{ 'translating-now': index === currentSentence - 1 && translating && !paused }"
            >
              <div class="pair-index">{{ index + 1 }}</div>
              <div class="pair-content">
                <div class="source-text">
                  <div class="text-label">原文:</div>
                  <div class="text-content">{{ pair.source }}</div>
                </div>
                <div class="translation-text">
                  <div class="text-label">译文:</div>
                  <div class="text-content">{{ pair.translation }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import translateAPI from '@/api/translate'
import historyAPI from '@/api/history'

// 数据
const activeTab = ref('history')
const selectedHistoryId = ref(null)
const inputText = ref('')
const sourceLanguage = ref('auto')
const targetLanguage = ref('zh')
const ocrText = ref('')
const ocrHistories = ref([])
const isEditing = ref(false)

// 翻译状态
const translating = ref(false)
const paused = ref(false)
const taskId = ref(null)
const currentSentence = ref(0)
const totalSentences = ref(0)
const progressMessage = ref('')
const translationResults = ref([])

// 定时器
let progressTimer = null

// 计算属性
const progressPercentage = computed(() => {
  if (totalSentences.value === 0) return 0
  return Math.round((currentSentence.value / totalSentences.value) * 100)
})

const progressStatus = computed(() => {
  if (!translating.value && currentSentence.value === totalSentences.value && totalSentences.value > 0) {
    return 'success'
  }
  if (paused.value) {
    return 'warning'
  }
  if (!translating.value && currentSentence.value < totalSentences.value) {
    return 'exception'
  }
  return undefined
})

// 获取开始按钮文本
const getStartButtonText = () => {
  if (translating.value && paused.value) {
    return '翻译已暂停'
  }
  if (translating.value) {
    return '翻译中...'
  }
  if (translationResults.value.length > 0 && currentSentence.value < totalSentences.value) {
    return `继续翻译 (从第 ${currentSentence.value + 1} 句)`
  }
  return '开始翻译'
}

// 加载 OCR 历史记录
const loadOCRHistories = async () => {
  try {
    const response = await historyAPI.getList({ task_type: 'ocr', page_size: 100 })
    ocrHistories.value = response.items.filter(item => item.status === 'completed')
  } catch (error) {
    ElMessage.error('加载历史记录失败: ' + (error.message || '未知错误'))
  }
}

// 加载 OCR 结果
const loadOCRResult = async () => {
  if (!selectedHistoryId.value) return

  try {
    const history = await historyAPI.getDetail(selectedHistoryId.value)
    if (history.ocr_result) {
      const ocrData = JSON.parse(history.ocr_result)
      ocrText.value = ocrData.map(page => page.text).join('\n\n')
    }
    // 重置翻译状态
    translationResults.value = []
    currentSentence.value = 0
    totalSentences.value = 0
    paused.value = false
    isEditing.value = false
  } catch (error) {
    ElMessage.error('加载 OCR 结果失败: ' + (error.message || '未知错误'))
  }
}

// 切换标签页
const handleTabChange = () => {
  // 清空上一个标签页的数据
  selectedHistoryId.value = null
  inputText.value = ''
  ocrText.value = ''
  translationResults.value = []
  currentSentence.value = 0
  totalSentences.value = 0
  paused.value = false
  isEditing.value = false
}

// 开始翻译
const startTranslation = async () => {
  // 如果是从暂停状态继续
  if (paused.value && taskId.value) {
    resumeTranslation()
    return
  }

  try {
    translating.value = true
    paused.value = false
    isEditing.value = false  // 开始翻译后禁用编辑
    translationResults.value = []
    currentSentence.value = 0
    totalSentences.value = 0
    progressMessage.value = '正在启动翻译任务...'

    // 准备请求参数
    const params = {
      source_language: sourceLanguage.value,
      target_language: targetLanguage.value
    }

    if (activeTab.value === 'history') {
      // 使用编辑后的文本而不是原始 OCR 结果
      params.text = ocrText.value
      params.original_history_id = selectedHistoryId.value  // 关联原始 OCR 任务
    } else {
      params.text = inputText.value
    }

    // 启动翻译任务
    const response = await translateAPI.startTranslation(params)
    taskId.value = response.task_id

    ElMessage.success('翻译任务已启动')

    // 开始轮询进度
    startProgressPolling()
  } catch (error) {
    translating.value = false
    ElMessage.error('启动翻译失败: ' + (error.message || '未知错误'))
  }
}

// 暂停/继续翻译
const togglePause = async () => {
  if (paused.value) {
    // 继续翻译
    resumeTranslation()
  } else {
    // 暂停翻译
    pauseTranslation()
  }
}

// 暂停翻译
const pauseTranslation = async () => {
  try {
    await translateAPI.pauseTranslation(taskId.value)
    paused.value = true
    progressMessage.value = `已暂停，当前进度: ${currentSentence.value}/${totalSentences.value}`
    ElMessage.info('翻译已暂停，可随时继续')
  } catch (error) {
    ElMessage.error('暂停失败: ' + (error.message || '未知错误'))
  }
}

// 继续翻译
const resumeTranslation = async () => {
  try {
    await translateAPI.resumeTranslation(taskId.value)
    paused.value = false
    progressMessage.value = '正在继续翻译...'
    ElMessage.success('继续翻译')
    // 确保轮询在运行
    if (!progressTimer) {
      startProgressPolling()
    }
  } catch (error) {
    ElMessage.error('继续翻译失败: ' + (error.message || '未知错误'))
  }
}

// 停止翻译
const stopTranslation = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停止翻译吗？已翻译的内容将保留。',
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (taskId.value) {
      await translateAPI.stopTranslation(taskId.value)
    }

    translating.value = false
    paused.value = false
    if (progressTimer) {
      clearInterval(progressTimer)
      progressTimer = null
    }
    progressMessage.value = `翻译已停止，完成 ${currentSentence.value}/${totalSentences.value} 句`
    ElMessage.info('翻译已停止')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败: ' + (error.message || '未知错误'))
    }
  }
}

// 开始轮询进度
const startProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }

  progressTimer = setInterval(async () => {
    try {
      const progress = await translateAPI.getProgress(taskId.value)

      currentSentence.value = progress.current
      totalSentences.value = progress.total

      // 更新暂停状态
      if (progress.status === 'paused') {
        paused.value = true
        progressMessage.value = progress.message || `已暂停，当前进度: ${progress.current}/${progress.total}`
      } else {
        progressMessage.value = progress.message || ''
      }

      // 更新翻译结果
      if (progress.translations && progress.translations.length > 0) {
        translationResults.value = progress.translations
      }

      // 检查是否完成
      if (progress.status === 'completed') {
        translating.value = false
        paused.value = false
        clearInterval(progressTimer)
        progressTimer = null
        ElMessage.success('翻译完成！')
      } else if (progress.status === 'failed') {
        translating.value = false
        paused.value = false
        clearInterval(progressTimer)
        progressTimer = null
        ElMessage.error('翻译失败: ' + (progress.error || '未知错误'))
      } else if (progress.status === 'stopped') {
        translating.value = false
        paused.value = false
        clearInterval(progressTimer)
        progressTimer = null
      }
    } catch (error) {
      console.error('获取进度失败:', error)
    }
  }, 1000) // 每秒轮询一次
}

// 复制全部译文
const copyAllTranslations = () => {
  const text = translationResults.value.map(pair => pair.translation).join('\n\n')
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

// 生命周期
loadOCRHistories()

onUnmounted(() => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }
})
</script>

<style scoped>
.translate-container {
  padding: 20px;
}

.ocr-edit-header {
  margin-bottom: 10px;
}

.editable-textarea :deep(.el-textarea__inner) {
  border-color: #409eff;
  background-color: #f5f9ff;
}

.ocr-tips {
  margin-top: 5px;
}

.translation-progress {
  margin-top: 30px;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-message {
  text-align: center;
  color: #909399;
  margin-top: 10px;
}

.realtime-results {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h4 {
  margin: 0;
}

.translation-pairs {
  max-height: 600px;
  overflow-y: auto;
}

.sentence-pair {
  display: flex;
  gap: 15px;
  padding: 15px;
  margin-bottom: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fff;
  transition: all 0.3s;
}

.sentence-pair:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.sentence-pair.translating-now {
  border-color: #409eff;
  background-color: #ecf5ff;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    background-color: #ecf5ff;
  }
  50% {
    background-color: #d9ecff;
  }
}

.pair-index {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  line-height: 40px;
  text-align: center;
  background-color: #f5f7fa;
  border-radius: 50%;
  font-weight: bold;
  color: #606266;
}

.pair-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.source-text,
.translation-text {
  display: flex;
  gap: 10px;
}

.text-label {
  flex-shrink: 0;
  width: 50px;
  font-weight: bold;
  color: #606266;
}

.source-text .text-label {
  color: #909399;
}

.translation-text .text-label {
  color: #409eff;
}

.text-content {
  flex: 1;
  line-height: 1.6;
  word-break: break-word;
}

.text-cell {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}
</style>
