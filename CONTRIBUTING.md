# Contributing to OCR & Translation System

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, Node.js version)
- Screenshots if applicable

### Suggesting Features

Feature requests are welcome! Please open an issue with:
- A clear description of the feature
- Use cases and benefits
- Any implementation ideas you have

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/ocrandtranslate.git
   cd ocrandtranslate
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   - Ensure backend tests pass
   - Test frontend functionality manually
   - Check for console errors

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Commit message format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Provide a clear description of your changes
   - Reference any related issues
   - Wait for code review

## Development Setup

### Backend Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Code Style

**Python (Backend)**
- Follow PEP 8 style guide
- Use type hints where possible
- Keep functions focused and small
- Add docstrings for public functions

**JavaScript/Vue (Frontend)**
- Use Vue 3 Composition API
- Follow Vue.js style guide
- Use meaningful variable names
- Keep components focused

## Project Structure

```
backend/app/
├── routers/        # API endpoints (add new routes here)
├── services/       # Business logic (OCR, translation, etc.)
├── models/         # Database models
├── schemas/        # Request/response schemas
└── utils/          # Helper functions

frontend/src/
├── views/          # Page components
├── components/     # Reusable components
├── api/            # API client functions
├── stores/         # State management
└── router/         # Route configuration
```

## Adding New Features

### Adding a New API Endpoint

1. Create route in `backend/app/routers/`
2. Add business logic in `backend/app/services/`
3. Define schemas in `backend/app/schemas/`
4. Add API client in `frontend/src/api/`
5. Update UI in `frontend/src/views/`

### Adding a New Page

1. Create Vue component in `frontend/src/views/`
2. Add route in `frontend/src/router/index.js`
3. Add navigation item in layout component

## Testing

### Backend Testing
```bash
cd backend
pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm run test
```

### Manual Testing Checklist
- [ ] User registration and login
- [ ] OCR processing with PDF upload
- [ ] Translation with progress tracking
- [ ] History viewing and management
- [ ] Correction system
- [ ] API configuration

## Code Review Process

1. All pull requests require review before merging
2. Reviewers will check:
   - Code quality and style
   - Functionality and correctness
   - Test coverage
   - Documentation updates

3. Address review comments
4. Once approved, your PR will be merged

## Questions?

If you have questions about contributing, feel free to:
- Open an issue on GitHub
- Check existing issues for similar questions
- Review the README for setup instructions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
