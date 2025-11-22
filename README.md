# OCR & Translation System

> 基于 DeepSeek-OCR 和 AI 模型的现代化 PDF OCR 翻译系统
> Modern OCR and translation system powered by DeepSeek-OCR and AI models

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)

---

## ✨ 核心特性 | Key Features

- 📄 **智能 OCR 识别** - 使用 DeepSeek-OCR 提取 PDF 文档文本，支持多种语言
- 🌐 **实时翻译** - 后台异步翻译，实时显示进度和结果，支持暂停/继续/停止
- 📝 **智能分句** - 自动处理标题、跨页断句等复杂情况
- 🔄 **对照显示** - 原文译文并排展示，一目了然
- 📚 **翻译记忆** - 基于向量相似度的术语纠正系统，确保翻译一致性
- ✏️ **划词纠正** - 在翻译结果中选中文本即可创建纠错，支持德文、俄文、英文等
- 🎯 **纠错管理** - 完整的纠错管理界面，支持增删改查、导入导出
- 🔒 **安全认证** - 用户系统，API 密钥加密存储
- 📊 **历史管理** - 查看和管理所有 OCR 和翻译任务
- ⚙️ **灵活配置** - 支持多种 AI API（硅基流动、OpenAI 等）

---

## 🚀 快速开始 | Quick Start

### 环境要求 | Prerequisites

```bash
Python 3.9+
Node.js 18+
poppler-utils  # PDF 处理依赖
```

### 安装步骤 | Installation

**1. 克隆仓库**
```bash
git clone https://github.com/miaoxutao123/deepseek-ocr-translate.git
cd deepseek-ocr-translate
```

**2. 后端设置**
```bash
cd backend
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改 SECRET_KEY
```

**3. 前端设置**
```bash
cd frontend
npm install
```

**4. 运行**
```bash
# 后端（终端 1）
cd backend
python run.py
# 访问 http://localhost:8000

# 前端（终端 2）
cd frontend
npm run dev
# 访问 http://localhost:5173
```

### 生产部署 | Production

```bash
./start_all.sh      # Linux/macOS
start_all.bat       # Windows
```

---

## 📖 使用说明 | Usage

### 1. 注册登录
首次使用需要注册账号

### 2. 配置 API
在「API 配置」页面设置：
- **OCR API**：硅基流动 DeepSeek-OCR
- **翻译 API**：DeepSeek-V3 或其他兼容模型
- **向量 API**（可选）：用于翻译纠错的向量相似度匹配

### 3. OCR 识别
- 上传 PDF 文档
- 等待识别完成
- 查看提取的文本

### 4. 文档翻译
- 选择历史 OCR 任务或直接输入文本
- 设置源语言和目标语言
- 支持编辑待翻译文本
- 支持暂停/继续/停止翻译
- 实时查看翻译进度和结果
- 可导出为 Markdown 文件

### 5. 翻译纠错
#### 在历史记录中添加纠错
- 打开翻译结果详情
- 选中原文或译文片段
- 点击弹出的"创建纠错"按钮
- 或点击"纠正此句"按钮快速纠正整句
- 或点击"手动添加纠错"按钮手动录入

#### 在纠错管理页面
- 查看所有已保存的纠错记录
- 按语言筛选或关键词搜索
- 添加、编辑、删除纠错
- 导出纠错数据备份
- 导入其他来源的纠错数据

#### 纠错自动应用
保存的纠错会在后续翻译中自动应用：
1. 相似度匹配：当遇到相似的句子时，优先使用已纠正的翻译
2. 提示词注入：将高频纠错添加到翻译提示词中，确保一致性
3. 使用统计：记录每条纠错的使用次数

---

## 🛠️ 技术栈 | Tech Stack

**后端** | Backend
- FastAPI - Python Web 框架
- SQLAlchemy + SQLite - 数据库
- pdf2image - PDF 处理
- httpx - HTTP 客户端

**前端** | Frontend
- Vue 3 (Composition API)
- Element Plus - UI 组件库
- Pinia - 状态管理
- Vite - 构建工具

---

## 📁 项目结构 | Project Structure

```
deepseek-ocr-translate/
├── backend/
│   ├── app/
│   │   ├── routers/          # API 路由
│   │   ├── services/         # 业务逻辑
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # 数据验证
│   │   └── utils/            # 工具函数
│   ├── clean_ocr_tags.py     # OCR 标签清理工具
│   ├── requirements.txt      # Python 依赖
│   └── run.py                # 入口文件
│
├── frontend/
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── api/              # API 客户端
│   │   ├── stores/           # 状态管理
│   │   └── router/           # 路由配置
│   └── package.json          # Node 依赖
│
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

---

## 🔧 配置说明 | Configuration

### 环境变量

编辑 `backend/.env`：

```env
SECRET_KEY=your-secret-key-here  # 请务必修改！
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./ocr_translate.db
```

### Poppler 安装

- **Linux**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`
- **Windows**: [下载地址](https://github.com/oschwartz10612/poppler-windows/releases/)

---

## 🔄 工作原理 | How It Works

### OCR 流程
```
PDF → 图片转换 → DeepSeek-OCR 识别 → 跨页句子合并 → 标签清理 → 存储
```

### 翻译流程
```
加载文本 → 智能分句 → 后台逐句翻译 → 应用纠错 → 实时显示 → 保存结果
```

### 翻译纠错原理

#### 1. 数据存储结构
纠错记录存储在 SQLite 数据库中，每条记录包含：
- `source_text`: 原文
- `corrected_translation`: 正确的译文
- `source_language` / `target_language`: 语言对
- `embedding`: 文本的向量表示（768维）
- `usage_count`: 使用次数统计
- `last_used_at`: 最后使用时间

#### 2. 向量嵌入生成
使用 Google Gemini `text-embedding-004` 模型：
- 将原文转换为 768 维向量
- 捕获文本的语义特征
- 支持跨语言相似度计算

#### 3. 相似度匹配算法
```python
# 计算余弦相似度
similarity = dot(vec1, vec2) / (norm(vec1) * norm(vec2))

# 当 similarity >= 0.85 时认为匹配
if similarity >= threshold:
    return corrected_translation
```

#### 4. 翻译时应用策略
**策略一：直接替换**
- 查找相似度 ≥ 0.85 的纠错
- 直接使用纠正后的译文
- 更新使用统计

**策略二：提示词注入**
- 选取高频纠错（前10条）
- 添加到系统提示词：
  ```
  Previous corrections to follow:
  1. "Maschinelles Lernen" → "机器学习"
  2. "neuronale Netze" → "神经网络"
  ...
  Please maintain consistency with these corrections.
  ```

#### 5. 性能优化
- 纠错记录按语言对分组查询
- 向量计算使用 NumPy 加速
- Token 限制（最多 4000 tokens 的纠错）
- 缓存常用纠错的向量

### 技术优势
✅ **高准确率**：向量相似度匹配比简单字符串匹配更智能
✅ **可扩展**：支持任意语言对的纠错
✅ **可追溯**：记录每条纠错的使用情况
✅ **用户友好**：划词即可创建纠错，无需手动对齐

---

## 🛠️ 工具 | Utilities

### 清理 OCR 标签

从历史记录中移除 DeepSeek-OCR 的坐标标签：

```bash
cd backend
python clean_ocr_tags.py --preview   # 预览
python clean_ocr_tags.py --execute   # 执行
```

或在「历史记录」页面点击「清理标签」按钮。

---

## 🤝 贡献 | Contributing

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证 | License

[MIT License](LICENSE) © 2025 miaoxutao123

---

## 🙏 致谢 | Acknowledgments

- [DeepSeek](https://www.deepseek.com/) - 强大的 OCR 和语言模型
- [Silicon Flow](https://siliconflow.cn/) - API 基础设施
- [FastAPI](https://fastapi.tiangolo.com/) - 优秀的 Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式前端框架
- [Element Plus](https://element-plus.org/) - 精美的 UI 组件

---

**注意**: 这是一个开源项目，请确保您拥有使用相关 API 服务的适当权限和密钥。
