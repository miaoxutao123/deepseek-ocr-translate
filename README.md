# OCR & Translation System

> A modern OCR and translation system built with FastAPI + Vue 3, powered by AI APIs (Silicon Flow, OpenAI-compatible endpoints)

[中文文档](#中文文档) | [English](#english-documentation)

## 项目结构

```
ocrandtranslate/
├── backend/                 # 后端 (FastAPI)
│   ├── app/                # 应用代码
│   │   ├── routers/       # API 路由
│   │   ├── services/      # 业务逻辑
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic schemas
│   │   └── utils/         # 工具函数
│   ├── .env               # 环境配置（不提交）
│   ├── .env.example       # 环境配置示例
│   ├── requirements.txt   # Python 依赖
│   └── run.py            # 启动脚本
│
├── frontend/               # 前端 (Vue 3 + Element Plus)
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── components/   # 公共组件
│   │   ├── api/          # API 调用
│   │   ├── stores/       # Pinia 状态管理
│   │   └── router/       # 路由配置
│   ├── vite.config.js    # Vite 配置
│   └── package.json      # Node.js 依赖
│
├── logs/                   # 运行日志
├── uploads/                # 上传文件目录
│
├── start_all.sh           # 启动脚本 (Linux)
├── start_all_clean.sh     # 清洁启动 (Linux)
├── stop_all.sh            # 停止脚本 (Linux)
├── start_all.bat          # 启动脚本 (Windows)
└── stop_all.bat           # 停止脚本 (Windows)
```

## Features | 功能特性

- 📄 **PDF OCR Recognition** - Extract text from PDF documents using DeepSeek-OCR
- 🌐 **Document Translation** - Translate extracted text with real-time progress tracking
- 📝 **Smart Sentence Segmentation** - Intelligent text splitting that handles titles, cross-page sentences
- 🔄 **Real-time Progress** - Live translation progress with side-by-side source/target display
- 📚 **Translation Memory** - Correction system for consistent terminology
- 🔒 **User Management** - Secure authentication with encrypted API key storage
- 📊 **History Management** - Track and review all OCR and translation tasks
- ⚙️ **Flexible API Configuration** - Support for multiple AI API providers (Silicon Flow, OpenAI-compatible endpoints)

## Quick Start | 快速开始

### Prerequisites | 环境要求

- Python 3.9+
- Node.js 18+
- poppler-utils (for PDF processing)
  - **Linux**: `sudo apt-get install poppler-utils`
  - **macOS**: `brew install poppler`
  - **Windows**: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/)

### Installation | 安装步骤

1. **Clone the repository | 克隆仓库**
   ```bash
   git clone https://github.com/yourusername/ocrandtranslate.git
   cd ocrandtranslate
   ```

2. **Backend Setup | 后端设置**
   ```bash
   cd backend

   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment
   # Linux/macOS:
   source .venv/bin/activate
   # Windows:
   .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Configure environment variables
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Frontend Setup | 前端设置**
   ```bash
   cd frontend
   npm install
   ```

4. **Run Development Servers | 运行开发服务器**

   **Backend:**
   ```bash
   cd backend
   python run.py
   # API will be available at http://localhost:8000
   ```

   **Frontend:**
   ```bash
   cd frontend
   npm run dev
   # UI will be available at http://localhost:5173
   ```

### Production Deployment | 生产环境部署

**Linux/macOS:**
```bash
./start_all.sh
```

**Windows:**
```bash
start_all.bat
```

Check logs:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

Stop services:
```bash
./stop_all.sh  # Linux/macOS
stop_all.bat   # Windows
```

## Configuration | 配置说明

### API Configuration | API 配置

Configure your API keys in the web UI ("API配置" page) or via environment variables:

1. **OCR API** - For PDF text extraction
   - Recommended: Silicon Flow DeepSeek-OCR
   - API Base: `https://api.siliconflow.cn/v1`

2. **Translation API** - For text translation
   - Supported: OpenAI-compatible endpoints (Silicon Flow DeepSeek-V3, OpenAI, etc.)
   - API Base: `https://api.siliconflow.cn/v1` or `https://api.openai.com/v1`

3. **Embedding API** (Optional) - For translation memory similarity search
   - Used for correction suggestions

### Environment Variables | 环境变量

Edit `backend/.env`:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here  # Change this!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Database
DATABASE_URL=sqlite:///./ocr_translate.db

# CORS (for frontend)
CORS_ORIGINS=["http://localhost:5173","http://localhost:8080"]
```

Users will configure their own API keys through the web interface.

## Tech Stack | 技术栈

### Backend | 后端
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Lightweight database
- **pdf2image** - PDF to image conversion
- **httpx** - Async HTTP client
- **Pydantic** - Data validation
- **python-jose** - JWT authentication
- **passlib** - Password hashing

### Frontend | 前端
- **Vue 3** - Progressive JavaScript framework (Composition API)
- **Element Plus** - Vue 3 UI library
- **Pinia** - State management
- **Vue Router** - Official router
- **Axios** - HTTP client
- **Vite** - Build tool

## Project Structure | 项目结构

```
ocrandtranslate/
├── backend/                     # Backend (FastAPI)
│   ├── app/
│   │   ├── routers/            # API routes
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── ocr.py          # OCR endpoints
│   │   │   ├── translate.py    # Translation endpoints
│   │   │   ├── history.py      # History management
│   │   │   ├── correction.py   # Translation corrections
│   │   │   └── user.py         # User settings
│   │   ├── services/           # Business logic
│   │   │   ├── ocr_service.py
│   │   │   └── translation_service.py
│   │   ├── models/             # Database models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── utils/              # Utilities
│   │       ├── encryption.py   # API key encryption
│   │       └── sentence_splitter.py  # Text segmentation
│   ├── clean_ocr_tags.py       # OCR tag cleaning tool
│   ├── .env.example            # Environment template
│   ├── requirements.txt        # Python dependencies
│   └── run.py                  # Entry point
│
├── frontend/                    # Frontend (Vue 3)
│   ├── src/
│   │   ├── views/              # Page components
│   │   │   ├── Login.vue
│   │   │   ├── OCR.vue
│   │   │   ├── Translate.vue
│   │   │   ├── History.vue
│   │   │   ├── Corrections.vue
│   │   │   └── Settings.vue
│   │   ├── components/         # Reusable components
│   │   ├── api/                # API clients
│   │   ├── stores/             # Pinia stores
│   │   └── router/             # Route configuration
│   ├── vite.config.js
│   └── package.json
│
├── .gitignore
├── README.md
├── start_all.sh                # Linux/macOS startup script
├── start_all.bat               # Windows startup script
└── stop_all.sh                 # Service stop script
```

## How It Works | 工作原理

1. **OCR Process | OCR 流程**
   - Upload PDF document
   - Convert PDF pages to images
   - Send to DeepSeek-OCR API for text extraction
   - Clean and merge cross-page sentences
   - Store results in database

2. **Translation Process | 翻译流程**
   - Load OCR results or input text directly
   - Split text into sentences intelligently (handles titles, cross-page breaks)
   - Translate sentence by sentence in background
   - Apply translation corrections if available
   - Display real-time progress with side-by-side view
   - Save results for future reference

3. **Translation Memory | 翻译记忆**
   - Store common term corrections
   - Use vector similarity search for suggestions
   - Automatically apply corrections during translation

## Utilities | 工具

### Clean OCR Tags | 清理 OCR 标签

The system includes a utility to clean DeepSeek-OCR tags from historical records:

```bash
cd backend
python clean_ocr_tags.py --preview  # Preview changes
python clean_ocr_tags.py --execute  # Apply changes
```

Or use the web UI: Click "清理标签" button in History page.

## Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License | 许可证

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments | 致谢

- [DeepSeek](https://www.deepseek.com/) - For powerful OCR and language models
- [Silicon Flow](https://siliconflow.cn/) - For API infrastructure
- [FastAPI](https://fastapi.tiangolo.com/) - For the excellent web framework
- [Vue.js](https://vuejs.org/) - For the progressive framework
- [Element Plus](https://element-plus.org/) - For the beautiful UI components

## Screenshots | 截图

### OCR Recognition
![OCR Interface](docs/screenshots/ocr.png)

### Real-time Translation
![Translation Progress](docs/screenshots/translation.png)

### History Management
![History View](docs/screenshots/history.png)

---

**Note**: This is an open-source project. Please use responsibly and ensure you have the appropriate API keys and permissions for the services you integrate.
