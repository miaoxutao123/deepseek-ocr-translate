<template>
  <el-card>
    <template #header>
      <h3>API配置</h3>
    </template>

    <el-alert
      title="安全提示"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      API密钥会被加密存储在服务器端，但请妥善保管，不要泄露给他人
    </el-alert>

    <el-form :model="form" label-width="150px">
      <el-divider content-position="left">OCR配置</el-divider>

      <el-form-item label="OCR API Base">
        <el-input v-model="form.ocr_api_base" placeholder="https://api.siliconflow.cn/v1" />
      </el-form-item>

      <el-form-item label="OCR API Key">
        <el-input v-model="form.ocr_api_key" type="password" show-password placeholder="输入硅基流动API密钥" />
      </el-form-item>

      <el-form-item label="OCR Model">
        <el-input v-model="form.ocr_model" placeholder="deepseek-ai/deepseek-vl2" />
      </el-form-item>

      <el-divider content-position="left">翻译配置</el-divider>

      <el-form-item label="翻译 API Base">
        <el-input v-model="form.translate_api_base" placeholder="https://api.openai.com/v1" />
      </el-form-item>

      <el-form-item label="翻译 API Key">
        <el-input v-model="form.translate_api_key" type="password" show-password placeholder="输入OpenAI API密钥" />
      </el-form-item>

      <el-form-item label="翻译 Model">
        <el-input v-model="form.translate_model" placeholder="gpt-4o-mini" />
      </el-form-item>

      <el-divider content-position="left">向量嵌入配置</el-divider>

      <el-form-item label="Embedding API Base">
        <el-input v-model="form.embedding_api_base" placeholder="https://generativelanguage.googleapis.com/v1beta" />
      </el-form-item>

      <el-form-item label="Embedding API Key">
        <el-input v-model="form.embedding_api_key" type="password" show-password placeholder="输入Gemini API密钥" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存配置
        </el-button>
        <el-button @click="handleLoad">
          重新加载
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const saving = ref(false)

const form = reactive({
  ocr_api_base: '',
  ocr_api_key: '',
  ocr_model: 'deepseek-ai/deepseek-vl2',
  translate_api_base: '',
  translate_api_key: '',
  translate_model: 'gpt-4o-mini',
  embedding_api_base: 'https://generativelanguage.googleapis.com/v1beta',
  embedding_api_key: ''
})

const handleLoad = async () => {
  await userStore.fetchApiConfig()
  if (userStore.apiConfig) {
    form.ocr_api_base = userStore.apiConfig.ocr_api_base || ''
    form.ocr_model = userStore.apiConfig.ocr_model || 'deepseek-ai/deepseek-vl2'
    form.translate_api_base = userStore.apiConfig.translate_api_base || ''
    form.translate_model = userStore.apiConfig.translate_model || 'gpt-4o-mini'
    form.embedding_api_base = userStore.apiConfig.embedding_api_base || ''
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await userStore.saveApiConfig(form)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  handleLoad()
})
</script>
