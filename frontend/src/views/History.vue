<template>
  <div class="history-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>历史记录</h2>
          <div class="header-actions">
            <el-button @click="cleanAllTags" :loading="cleaningAll" type="warning" plain>
              <el-icon><MagicStick /></el-icon>
              清理所有OCR标签
            </el-button>
            <el-button @click="refreshList" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-radio-group v-model="filters.taskType" @change="handleFilterChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="ocr">OCR识别</el-radio-button>
          <el-radio-button label="translate">翻译</el-radio-button>
          <el-radio-button label="correct">校正</el-radio-button>
        </el-radio-group>

        <el-radio-group v-model="filters.status" @change="handleFilterChange" style="margin-left: 20px">
          <el-radio-button label="">全部状态</el-radio-button>
          <el-radio-button label="pending">等待中</el-radio-button>
          <el-radio-button label="processing">处理中</el-radio-button>
          <el-radio-button label="completed">已完成</el-radio-button>
          <el-radio-button label="failed">失败</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 任务列表 -->
      <el-table
        :data="filteredHistories"
        v-loading="loading"
        style="margin-top: 20px"
        @row-click="handleRowClick"
        :row-class-name="getRowClassName"
      >
        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="filename">
              <el-icon><Document /></el-icon>
              <span>{{ row.original_filename }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="任务类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)">
              {{ getTaskTypeName(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="250">
          <template #default="{ row }">
            <div class="status-cell">
              <el-tag :type="getStatusColor(row.status)">
                {{ getStatusName(row.status) }}
              </el-tag>

              <!-- 调试信息 -->
              <div v-if="row.status === 'processing' || row.status === 'PROCESSING'" style="font-size: 11px; color: #999; margin-top: 4px;">
                Debug: {{ row.current_page }}/{{ row.total_pages }} ({{ row.status }})
              </div>

              <!-- 真实进度条 -->
              <div v-if="(row.status === 'processing' || row.status === 'PROCESSING') && row.total_pages && row.total_pages > 0" class="progress-info">
                <el-progress
                  :percentage="getProgressPercentage(row)"
                  :format="() => `${row.current_page || 0}/${row.total_pages}`"
                  :stroke-width="8"
                  :color="getProgressColor(row)"
                />
                <span class="progress-message">{{ row.progress_message }}</span>
              </div>

              <!-- 不确定进度条（兜底） -->
              <el-progress
                v-else-if="row.status === 'processing' || row.status === 'PROCESSING'"
                :percentage="100"
                :indeterminate="true"
                :duration="3"
                style="margin-top: 5px; width: 100%;"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="完成时间" width="180">
          <template #default="{ row }">
            {{ row.completed_at ? formatTime(row.completed_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              @click.stop="viewDetail(row)"
              :disabled="row.status !== 'completed'"
            >
              查看结果
            </el-button>
            <el-button
              size="small"
              type="warning"
              plain
              @click.stop="cleanTags(row)"
              :disabled="!row.ocr_result"
              :loading="cleaningIds.has(row.id)"
            >
              清理标签
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click.stop="deleteHistory(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialog.visible"
      :title="detailDialog.title"
      width="70%"
      @close="handleDialogClose"
    >
      <div v-if="detailDialog.data">
        <!-- 错误信息 -->
        <el-alert
          v-if="detailDialog.data.status === 'failed' && detailDialog.data.error_message"
          title="处理失败"
          type="error"
          :description="detailDialog.data.error_message"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <!-- OCR 结果 -->
        <div v-if="detailDialog.data.ocr_result" class="result-section">
          <h3>OCR 识别结果</h3>
          <el-tabs v-if="ocrPages.length > 0" type="border-card">
            <el-tab-pane
              v-for="page in ocrPages"
              :key="page.page_number"
              :label="`第 ${page.page_number} 页`"
            >
              <div class="page-result">
                <el-tag v-if="page.confidence" size="small">
                  置信度: {{ (page.confidence * 100).toFixed(1) }}%
                </el-tag>
                <pre class="result-text">{{ page.text }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
          <el-empty v-else description="暂无识别结果" />
        </div>

        <!-- 翻译结果 -->
        <div v-if="detailDialog.data.translation_result" class="result-section">
          <h3>翻译结果</h3>
          <div v-if="translationPairs.length > 0">
            <div class="translation-pairs-container">
              <div
                v-for="(pair, index) in translationPairs"
                :key="index"
                class="translation-pair"
              >
                <div class="pair-header">
                  <span class="pair-index">{{ index + 1 }}</span>
                </div>
                <div class="pair-content">
                  <div class="original">
                    <h4>原文</h4>
                    <pre>{{ pair.source }}</pre>
                  </div>
                  <el-divider />
                  <div class="translated">
                    <h4>译文</h4>
                    <pre>{{ pair.translation }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无翻译结果" />
        </div>

        <!-- 任务信息 -->
        <div class="task-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务ID">
              {{ detailDialog.data.id }}
            </el-descriptions-item>
            <el-descriptions-item label="任务类型">
              {{ getTaskTypeName(detailDialog.data.task_type) }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusColor(detailDialog.data.status)">
                {{ getStatusName(detailDialog.data.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文件名">
              {{ detailDialog.data.original_filename }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(detailDialog.data.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="完成时间">
              {{ detailDialog.data.completed_at ? formatTime(detailDialog.data.completed_at) : '未完成' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Refresh, MagicStick } from '@element-plus/icons-vue'
import historyAPI from '@/api/history'

// 数据
const loading = ref(false)
const histories = ref([])
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const filters = ref({
  taskType: '',
  status: ''
})

const detailDialog = ref({
  visible: false,
  title: '',
  data: null
})

// 清理状态
const cleaningAll = ref(false)
const cleaningIds = ref(new Set())

// 自动刷新定时器
let autoRefreshTimer = null

// 计算属性
const filteredHistories = computed(() => {
  let result = histories.value

  if (filters.value.status) {
    result = result.filter(h => h.status === filters.value.status)
  }

  return result
})

const ocrPages = computed(() => {
  if (!detailDialog.value.data?.ocr_result) return []
  try {
    return JSON.parse(detailDialog.value.data.ocr_result)
  } catch (e) {
    console.error('Failed to parse OCR result:', e)
    return []
  }
})

const translationPairs = computed(() => {
  if (!detailDialog.value.data?.translation_result) return []
  try {
    const result = JSON.parse(detailDialog.value.data.translation_result)
    // 新格式：数组 [{source: "...", translation: "..."}]
    if (Array.isArray(result) && result.length > 0 && result[0].source !== undefined) {
      return result
    }
    // 旧格式兼容（如果有的话）
    return []
  } catch (e) {
    console.error('Failed to parse translation result:', e)
    return []
  }
})

// 方法
const loadHistories = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }

    if (filters.value.taskType) {
      params.task_type = filters.value.taskType
    }

    const response = await historyAPI.getList(params)
    histories.value = response.items
    pagination.value.total = response.total

    // 检查是否有处理中的任务
    const hasProcessing = histories.value.some(h =>
      h.status === 'pending' || h.status === 'processing'
    )

    // 如果有处理中的任务，启动自动刷新
    if (hasProcessing && !autoRefreshTimer) {
      startAutoRefresh()
    } else if (!hasProcessing && autoRefreshTimer) {
      stopAutoRefresh()
    }
  } catch (error) {
    ElMessage.error('加载历史记录失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const refreshList = () => {
  loadHistories()
}

const handleFilterChange = () => {
  pagination.value.page = 1
  loadHistories()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadHistories()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadHistories()
}

const handleRowClick = (row) => {
  if (row.status === 'completed') {
    viewDetail(row)
  } else if (row.status === 'failed') {
    viewDetail(row)
  }
}

const viewDetail = async (row) => {
  try {
    const detail = await historyAPI.getDetail(row.id)
    detailDialog.value = {
      visible: true,
      title: `${getTaskTypeName(detail.task_type)} - ${detail.original_filename}`,
      data: detail
    }
  } catch (error) {
    ElMessage.error('加载详情失败: ' + (error.message || '未知错误'))
  }
}

const handleDialogClose = () => {
  detailDialog.value = {
    visible: false,
    title: '',
    data: null
  }
}

const deleteHistory = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${row.original_filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await historyAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadHistories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 清理单个记录的标签
const cleanTags = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要清理 "${row.original_filename}" 中的 OCR 标签吗？`,
      '清理标签',
      {
        confirmButtonText: '清理',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaningIds.value.add(row.id)

    const response = await historyAPI.cleanTags(row.id)

    if (response.removed_chars > 0) {
      ElMessage.success(`清理成功，移除了 ${response.removed_chars} 个字符`)
    } else {
      ElMessage.info('未发现需要清理的标签')
    }

    loadHistories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败: ' + (error.message || '未知错误'))
    }
  } finally {
    cleaningIds.value.delete(row.id)
  }
}

// 清理所有记录的标签
const cleanAllTags = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理所有历史记录中的 OCR 标签吗？此操作将清除坐标数组和特殊标记。',
      '批量清理',
      {
        confirmButtonText: '清理',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaningAll.value = true

    const response = await historyAPI.cleanAllTags()

    if (response.cleaned_records > 0) {
      ElMessage.success(
        `清理完成！处理了 ${response.cleaned_records} 条记录，` +
        `移除了 ${response.total_removed_chars} 个字符`
      )
    } else {
      ElMessage.info('未发现需要清理的记录')
    }

    loadHistories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败: ' + (error.message || '未知错误'))
    }
  } finally {
    cleaningAll.value = false
  }
}

// 自动刷新
const startAutoRefresh = () => {
  if (autoRefreshTimer) return

  autoRefreshTimer = setInterval(() => {
    loadHistories()
  }, 3000) // 每3秒刷新一次
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// 辅助方法
const getTaskTypeName = (type) => {
  const names = {
    ocr: 'OCR识别',
    translate: '翻译',
    correct: '校正'
  }
  return names[type] || type
}

const getTaskTypeColor = (type) => {
  const colors = {
    ocr: 'primary',
    translate: 'success',
    correct: 'warning'
  }
  return colors[type] || 'info'
}

const getStatusName = (status) => {
  const names = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return names[status] || status
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return colors[status] || 'info'
}

const getRowClassName = ({ row }) => {
  if (row.status === 'processing') return 'processing-row'
  if (row.status === 'failed') return 'failed-row'
  return ''
}

const getProgressPercentage = (row) => {
  if (!row.total_pages || row.total_pages === 0) return 0
  return Math.round((row.current_page || 0) / row.total_pages * 100)
}

const getProgressColor = (row) => {
  const percentage = getProgressPercentage(row)
  if (percentage < 30) return '#909399'
  if (percentage < 70) return '#E6A23C'
  return '#67C23A'
}

const formatTime = (time) => {
  if (!time) return '-'

  // 后端返回的是 UTC 时间（带 Z 后缀），JavaScript 会自动转换为本地时间
  const date = new Date(time)

  // 检查时间是否有效
  if (isNaN(date.getTime())) return '-'

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'Asia/Shanghai'  // 明确指定中国时区
  })
}

// 生命周期
onMounted(() => {
  loadHistories()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.history-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filters {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.filename {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  width: 100%;
}

.progress-info {
  width: 100%;
  margin-top: 8px;
}

.progress-message {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.processing-row) {
  background-color: #fef0f0;
  animation: pulse 2s ease-in-out infinite;
}

:deep(.failed-row) {
  background-color: #fef0f0;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.result-section {
  margin-bottom: 30px;
}

.result-section h3 {
  margin-bottom: 15px;
  color: #303133;
}

.page-result {
  padding: 15px;
}

.result-text {
  margin-top: 10px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
}

.translation-pairs-container {
  max-height: 600px;
  overflow-y: auto;
}

.translation-pair {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.pair-header {
  background-color: #f5f7fa;
  padding: 10px 15px;
  border-bottom: 1px solid #ebeef5;
}

.pair-index {
  font-weight: bold;
  color: #409eff;
  font-size: 14px;
}

.pair-content {
  padding: 15px;
}

.translation-pair .original,
.translation-pair .translated {
  margin-bottom: 0;
}

.translation-pair h4 {
  margin-bottom: 10px;
  color: #606266;
  font-size: 14px;
}

.translation-pair pre {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}

.translation-result {
  padding: 15px;
}

.translation-result .original,
.translation-result .translated {
  margin-bottom: 15px;
}

.translation-result h4 {
  margin-bottom: 10px;
  color: #606266;
}

.translation-result pre {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
}

.task-info {
  margin-top: 30px;
}
</style>
