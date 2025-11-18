import request from '@/utils/request'

// 用户认证
export const authAPI = {
  // 注册
  register(data) {
    return request.post('/auth/register', data)
  },

  // 登录
  login(data) {
    return request.post('/auth/login', data)
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request.get('/auth/me')
  },

  // 保存API配置
  saveApiConfig(data) {
    return request.post('/auth/api-config', data)
  },

  // 获取API配置
  getApiConfig() {
    return request.get('/auth/api-config')
  }
}

// OCR相关
export const ocrAPI = {
  // 上传文件
  uploadFile(file, sourceLanguage = 'auto') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_language', sourceLanguage)
    formData.append('auto_process', 'true')  // 启用后台自动处理
    return request.post('/ocr/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取OCR结果
  getResult(historyId) {
    return request.get(`/ocr/result/${historyId}`)
  },

  // 获取OCR状态
  getStatus(historyId) {
    return request.get(`/ocr/status/${historyId}`)
  }
}

// 翻译相关
export const translateAPI = {
  // 翻译文本或OCR结果
  translate(data) {
    return request.post('/translate', data)
  },

  // 获取翻译结果
  getResult(historyId) {
    return request.get(`/translate/result/${historyId}`)
  }
}

// 纠错相关
export const correctionAPI = {
  // 创建纠错
  create(data) {
    return request.post('/corrections', data)
  },

  // 获取纠错列表
  list(params) {
    return request.get('/corrections', { params })
  },

  // 删除纠错
  delete(id) {
    return request.delete(`/corrections/${id}`)
  },

  // 导入纠错
  import(data) {
    return request.post('/corrections/import', data)
  },

  // 导出纠错
  export(params) {
    return request.get('/corrections/export', { params })
  }
}

// 历史记录相关
export const historyAPI = {
  // 获取历史列表
  list(params) {
    return request.get('/history', { params })
  },

  // 获取历史详情
  get(id) {
    return request.get(`/history/${id}`)
  },

  // 删除历史
  delete(id) {
    return request.delete(`/history/${id}`)
  },

  // 导出翻译结果
  export(id, format) {
    return request.get(`/history/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
  }
}
