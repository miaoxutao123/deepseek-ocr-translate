import request from '@/utils/request'

const translateAPI = {
  /**
   * 启动翻译任务（后台运行）
   * @param {Object} params - 翻译参数
   * @param {string} params.source_language - 源语言
   * @param {string} params.target_language - 目标语言
   * @param {string} [params.text] - 直接翻译的文本
   * @param {number} [params.history_id] - 从历史记录翻译
   */
  startTranslation(params) {
    return request.post('/translate/start', params)
  },

  /**
   * 获取翻译进度（实时）
   * @param {number} historyId - 历史记录 ID
   */
  getProgress(historyId) {
    return request.get(`/translate/progress/${historyId}`)
  },

  /**
   * 获取翻译结果
   * @param {number} historyId - 历史记录 ID
   */
  getResult(historyId) {
    return request.get(`/translate/result/${historyId}`)
  }
}

export default translateAPI
