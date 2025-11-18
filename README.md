# OCR & Translation System

> 基于 DeepSeek-OCR 和 AI 模型的现代化 PDF OCR 翻译系统
> Modern OCR and translation system powered by DeepSeek-OCR and AI models

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)

---

## ✨ 核心特性 | Key Features

- 📄 **智能 OCR 识别** - 使用 DeepSeek-OCR 提取 PDF 文档文本
- 🌐 **实时翻译** - 后台异步翻译，实时显示进度和结果
- 📝 **智能分句** - 自动处理标题、跨页断句等复杂情况
- 🔄 **对照显示** - 原文译文并排展示，一目了然
- 📚 **翻译记忆** - 术语纠正系统，确保翻译一致性
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
- **向量 API**（可选）：用于翻译纠错

### 3. OCR 识别
- 上传 PDF 文档
- 等待识别完成
- 查看提取的文本

### 4. 文档翻译
- 选择历史 OCR 任务或直接输入文本
- 设置源语言和目标语言
- 实时查看翻译进度和结果

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
PDF → 图片转换 → DeepSeek-OCR 识别 → 跨页句子合并 → 存储

### 翻译流程
加载文本 → 智能分句 → 后台逐句翻译 → 应用纠错 → 实时显示 → 保存结果

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

## 📸 截图 | Screenshots

### OCR 识别界面
![OCR Interface](docs/screenshots/ocr.png)

### 实时翻译
![Translation Progress](docs/screenshots/translation.png)

### 历史管理
![History View](docs/screenshots/history.png)

---

**注意**: 这是一个开源项目，请确保您拥有使用相关 API 服务的适当权限和密钥。
