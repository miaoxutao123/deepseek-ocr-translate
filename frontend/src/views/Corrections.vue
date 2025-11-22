<template>
  <div class="corrections-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>翻译纠错管理</h2>
          <div class="header-actions">
            <el-button type="primary" @click="openAddDialog">
              <el-icon><Plus /></el-icon>
              添加纠错
            </el-button>
            <el-button @click="exportCorrections" :loading="exporting">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button @click="openImportDialog">
              <el-icon><Upload /></el-icon>
              导入
            </el-button>
            <el-button @click="loadCorrections" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-select
          v-model="filters.sourceLanguage"
          placeholder="源语言"
          clearable
          style="width: 120px"
          @change="loadCorrections"
        >
          <el-option
            v-for="lang in languageOptions"
            :key="lang.value"
            :label="lang.label"
            :value="lang.value"
          />
        </el-select>

        <el-input
          v-model="filters.keyword"
          placeholder="搜索原文或译文..."
          style="width: 300px; margin-left: 15px"
          clearable
          @keyup.enter="loadCorrections"
        >
          <template #append>
            <el-button @click="loadCorrections">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 纠错列表 -->
      <el-table
        :data="filteredCorrections"
        v-loading="loading"
        style="margin-top: 20px"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column label="源语言" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">
              {{ getLanguageName(row.source_language) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="原文" min-width="250">
          <template #default="{ row }">
            <div class="text-cell">
              {{ row.source_text }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="译文" min-width="250">
          <template #default="{ row }">
            <div class="text-cell">
              {{ row.corrected_translation }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="使用次数" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.usage_count > 0 ? 'success' : 'info'">
              {{ row.usage_count || 0 }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="editCorrection(row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click="deleteCorrection(row)"
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

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="editDialog.visible"
      :title="editDialog.isEdit ? '编辑纠错' : '添加纠错'"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form label-width="100px">
        <el-form-item label="源语言">
          <el-select v-model="editDialog.form.source_language" placeholder="选择源语言">
            <el-option
              v-for="lang in languageOptions"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="目标语言">
          <el-select v-model="editDialog.form.target_language" disabled>
            <el-option value="zh" label="中文" />
          </el-select>
          <span style="margin-left: 10px; color: #909399; font-size: 12px;">
            目前仅支持翻译为中文
          </span>
        </el-form-item>

        <el-form-item label="原文">
          <el-input
            v-model="editDialog.form.source_text"
            type="textarea"
            :rows="4"
            placeholder="输入需要纠正的原文"
          />
        </el-form-item>

        <el-form-item label="正确译文">
          <el-input
            v-model="editDialog.form.corrected_translation"
            type="textarea"
            :rows="4"
            placeholder="输入正确的中文翻译"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="editDialog.loading"
          @click="submitCorrection"
        >
          {{ editDialog.isEdit ? '保存修改' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="importDialog.visible"
      title="导入纠错数据"
      width="500px"
    >
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".json"
        :on-change="handleFileChange"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 JSON 文件，格式应与导出的文件相同
          </div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="importDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="importDialog.loading"
          @click="importCorrections"
          :disabled="!importDialog.file"
        >
          导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Upload, Refresh, Search } from '@element-plus/icons-vue'
import { correctionAPI } from '@/api/index'

// 数据
const loading = ref(false)
const exporting = ref(false)
const corrections = ref([])
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const filters = ref({
  sourceLanguage: '',
  keyword: ''
})

// 语言选项
const languageOptions = [
  { value: 'en', label: '英文' },
  { value: 'de', label: '德文' },
  { value: 'ru', label: '俄文' },
  { value: 'fr', label: '法文' },
  { value: 'ja', label: '日文' },
  { value: 'ko', label: '韩文' }
]

// 编辑对话框
const editDialog = ref({
  visible: false,
  isEdit: false,
  loading: false,
  editId: null,
  form: {
    source_text: '',
    corrected_translation: '',
    source_language: 'en',
    target_language: 'zh'
  }
})

// 导入对话框
const importDialog = ref({
  visible: false,
  loading: false,
  file: null
})

const uploadRef = ref(null)

// 计算属性 - 过滤后的列表
const filteredCorrections = computed(() => {
  let result = corrections.value

  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(c =>
      c.source_text.toLowerCase().includes(keyword) ||
      c.corrected_translation.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 加载纠错列表
const loadCorrections = async () => {
  loading.value = true
  try {
    const params = {
      limit: pagination.value.pageSize,
      offset: (pagination.value.page - 1) * pagination.value.pageSize
    }

    if (filters.value.sourceLanguage) {
      params.source_language = filters.value.sourceLanguage
    }

    const response = await correctionAPI.list(params)
    corrections.value = response.items || response
    pagination.value.total = response.total || corrections.value.length
  } catch (error) {
    ElMessage.error('加载纠错列表失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 分页处理
const handlePageChange = (page) => {
  pagination.value.page = page
  loadCorrections()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadCorrections()
}

// 打开添加对话框
const openAddDialog = () => {
  editDialog.value = {
    visible: true,
    isEdit: false,
    loading: false,
    editId: null,
    form: {
      source_text: '',
      corrected_translation: '',
      source_language: 'en',
      target_language: 'zh'
    }
  }
}

// 编辑纠错
const editCorrection = (row) => {
  editDialog.value = {
    visible: true,
    isEdit: true,
    loading: false,
    editId: row.id,
    form: {
      source_text: row.source_text,
      corrected_translation: row.corrected_translation,
      source_language: row.source_language,
      target_language: row.target_language || 'zh'
    }
  }
}

// 提交纠错
const submitCorrection = async () => {
  const form = editDialog.value.form

  if (!form.source_text.trim()) {
    ElMessage.warning('请输入原文')
    return
  }

  if (!form.corrected_translation.trim()) {
    ElMessage.warning('请输入正确的译文')
    return
  }

  try {
    editDialog.value.loading = true

    if (editDialog.value.isEdit) {
      // 编辑模式：先删除再创建（因为API可能没有update接口）
      await correctionAPI.delete(editDialog.value.editId)
    }

    await correctionAPI.create({
      source_text: form.source_text.trim(),
      corrected_translation: form.corrected_translation.trim(),
      source_language: form.source_language,
      target_language: form.target_language
    })

    ElMessage.success(editDialog.value.isEdit ? '修改成功' : '添加成功')
    handleDialogClose()
    loadCorrections()
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  } finally {
    editDialog.value.loading = false
  }
}

// 删除纠错
const deleteCorrection = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条纠错吗？\n原文: "${row.source_text.substring(0, 50)}..."`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await correctionAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadCorrections()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 关闭对话框
const handleDialogClose = () => {
  editDialog.value = {
    visible: false,
    isEdit: false,
    loading: false,
    editId: null,
    form: {
      source_text: '',
      corrected_translation: '',
      source_language: 'en',
      target_language: 'zh'
    }
  }
}

// 导出纠错
const exportCorrections = async () => {
  try {
    exporting.value = true

    const params = {}
    if (filters.value.sourceLanguage) {
      params.source_language = filters.value.sourceLanguage
    }

    const response = await correctionAPI.export(params)

    // 创建下载
    const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `corrections_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    exporting.value = false
  }
}

// 打开导入对话框
const openImportDialog = () => {
  importDialog.value = {
    visible: true,
    loading: false,
    file: null
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 处理文件选择
const handleFileChange = (file) => {
  importDialog.value.file = file.raw
}

// 导入纠错
const importCorrections = async () => {
  if (!importDialog.value.file) {
    ElMessage.warning('请选择要导入的文件')
    return
  }

  try {
    importDialog.value.loading = true

    // 读取文件内容
    const text = await importDialog.value.file.text()
    const data = JSON.parse(text)

    await correctionAPI.import(data)

    ElMessage.success('导入成功')
    importDialog.value.visible = false
    loadCorrections()
  } catch (error) {
    if (error instanceof SyntaxError) {
      ElMessage.error('文件格式错误，请确保是有效的JSON文件')
    } else {
      ElMessage.error('导入失败: ' + (error.message || '未知错误'))
    }
  } finally {
    importDialog.value.loading = false
  }
}

// 辅助方法
const getLanguageName = (code) => {
  const lang = languageOptions.find(l => l.value === code)
  return lang ? lang.label : code
}

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
    second: '2-digit',
    hour12: false,
    timeZone: 'Asia/Shanghai'
  })
}

// 生命周期
onMounted(() => {
  loadCorrections()
})
</script>

<style scoped>
.corrections-container {
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

.text-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-cell:hover {
  white-space: normal;
  word-break: break-all;
}
</style>
