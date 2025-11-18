import request from '@/utils/request'

const historyAPI = {
  // 获取历史记录列表
  getList(params) {
    return request.get('/history', { params })
  },

  // 获取单个历史记录详情
  getDetail(id) {
    return request.get(`/history/${id}`)
  },

  // 删除历史记录
  delete(id) {
    return request.delete(`/history/${id}`)
  },

  // 导出翻译结果
  export(id, format = 'markdown') {
    return request.get(`/history/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
  },

  // 清理单个记录的 OCR 标签
  cleanTags(id) {
    return request.post(`/history/${id}/clean-tags`)
  },

  // 清理所有记录的 OCR 标签
  cleanAllTags() {
    return request.post('/history/clean-all-tags')
  }
}

export default historyAPI
