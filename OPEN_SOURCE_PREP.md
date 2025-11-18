# Open Source Preparation Summary

This document explains what has been excluded from the Git repository and why.

## Files Excluded via .gitignore

### Sensitive Data
- `backend/.env` - Contains API keys and secrets (652 bytes)
- `backend/.env.production` - Production configuration
- `backend/ocr_translate.db` - User data and history (652 KB)

### Build Artifacts & Dependencies
- `backend/.venv/` - Python virtual environment
- `frontend/node_modules/` - Node.js dependencies (large)
- `frontend/dist/` - Built frontend files
- `backend/static/` - Deployed frontend (copied from dist)

### User Data
- `backend/uploads/` - User uploaded PDF files
- `*.db`, `*.sqlite` - All database files

### Development Files
- `__pycache__/` - Python bytecode cache
- `.vscode/`, `.idea/` - IDE configurations
- `*.log` - Log files
- `.claude/` - Claude Code workspace

### Temporary/Deployment Files
- `deploy_*.zip` - Deployment archives
- `pack_for_deploy.ps1` - Deployment script
- `test_local.ps1` - Local testing script
- `setup_poppler.ps1` - Poppler setup script
- `poppler/` - Poppler binaries (should be installed separately)
- `nul` - Empty temp file

## Files Included in Repository

### Configuration Templates
- `backend/.env.example` - Template for environment variables
- `nginx.conf.example` - Nginx configuration example
- `ocr-backend.service.example` - Systemd service example

### Source Code
- `backend/app/` - All backend Python code
- `backend/clean_ocr_tags.py` - OCR tag cleaning utility
- `backend/requirements.txt` - Python dependencies list
- `backend/pyproject.toml` - Python project configuration
- `frontend/src/` - All frontend Vue.js code
- `frontend/package.json` - Node.js dependencies list

### Scripts
- `start_all.sh`, `start_all.bat` - Startup scripts
- `start_all_clean.sh` - Clean startup script
- `stop_all.sh`, `stop_all.bat` - Shutdown scripts

### Documentation
- `README.md` - Comprehensive project documentation
- `LICENSE` - MIT license

## Repository Size

After excluding the above files:
- Source code: ~200 KB
- Dependencies will be downloaded via pip/npm during installation
- Total repository size: < 1 MB

## Setup Instructions for New Users

1. Clone the repository
2. Copy `backend/.env.example` to `backend/.env`
3. Edit `.env` and add your own SECRET_KEY
4. Install dependencies: `pip install -r requirements.txt` and `npm install`
5. Configure API keys via the web interface
6. Run the application

## Security Notes

- All API keys are encrypted in the database using user-specific encryption
- SECRET_KEY in .env must be changed for production use
- Database contains user accounts and encrypted API keys - never commit it
- Upload directory may contain user PDF files - excluded from repository

## Git Commands to Initialize

```bash
# Initialize git if not already done
git init

# Add all files (respecting .gitignore)
git add .

# Check what will be committed
git status

# Create initial commit
git commit -m "Initial commit: OCR & Translation System"

# Add remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/ocrandtranslate.git

# Push to GitHub
git push -u origin main
```
