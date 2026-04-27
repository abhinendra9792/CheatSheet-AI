# Contributing to CheatSheet AI

Thank you for your interest in contributing! This document provides guidelines and instructions.

## 🎯 Code of Conduct

- Be respectful and inclusive
- Welcome diverse perspectives
- Provide constructive feedback
- Focus on the code, not the person

## 🚀 Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/CheatSheet-AI.git
cd CheatSheet-AI
git remote add upstream https://github.com/abhinendra9792/CheatSheet-AI.git
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-name
git checkout -b docs/improvement-name
```

### 3. Branch Naming Convention
```
feature/add-new-model       # New feature
fix/api-timeout-issue       # Bug fix
docs/update-readme          # Documentation
test/improve-coverage       # Tests
perf/optimize-pipeline      # Performance
refactor/clean-code         # Code refactoring
```

## 📝 Commit Messages

Use clear, descriptive commit messages:

```bash
git commit -m "feat: add support for Gemini 2.5 Pro model

- Implement fallback chain for new model
- Update settings with model configuration
- Add tests for model selection logic"
```

### Commit Message Format
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Test additions
- `perf`: Performance improvements
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

## ✅ Before Submitting PR

1. **Update main branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**
   ```bash
   cd backend
   pytest tests/ -v --tb=short
   ```

3. **Check code quality**
   ```bash
   # Run linting (if configured)
   flake8 src/
   black src/
   ```

4. **Update documentation**
   - Update README if needed
   - Add docstrings to functions
   - Include examples for new features

5. **Verify no conflicts**
   ```bash
   git status  # Should be clean
   ```

## 🔄 Creating a Pull Request

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**
   - Use descriptive title
   - Reference related issues
   - Provide detailed description

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Related Issues
   Closes #123

   ## Testing
   How to test the changes

   ## Checklist
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No breaking changes
   ```

## 📋 Review Process

1. **Address feedback**
   - Respond to review comments
   - Make requested changes
   - Push updates (don't force push)

2. **Keep PR focused**
   - One feature per PR
   - Avoid scope creep
   - Link to related issues

3. **Merge strategy**
   - Rebase and merge preferred
   - Squash for small fixes
   - Merge commit for features

## 🎓 Development Setup

### Backend Development
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
pip install -e .  # For development
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_pipeline.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## 📚 Areas for Contribution

### High Priority
- 🐛 Bug fixes
- 🚀 Performance improvements
- 📚 Documentation improvements
- 🧪 Test coverage

### Medium Priority
- ✨ New features
- 🎨 UI/UX improvements
- ♻️ Code refactoring
- 🔍 Code quality

### Low Priority
- 💬 Comments/docstring improvements
- 🎯 Minor optimizations

## 🔍 Review Criteria

PRs are evaluated on:

1. **Code Quality**
   - Follows project conventions
   - Well-structured and readable
   - Proper error handling
   - Type hints (where applicable)

2. **Testing**
   - Unit tests included
   - Test coverage maintained
   - Integration tests if needed

3. **Documentation**
   - Code comments
   - Docstrings
   - README updates
   - Examples provided

4. **Performance**
   - No performance regression
   - Optimized algorithms
   - Efficient resource usage

5. **Security**
   - No hardcoded secrets
   - Input validation
   - Safe API usage

## 🚫 Common Issues

### Issue: "Your branch is behind by X commits"
```bash
git fetch upstream
git rebase upstream/main
git push origin feature-name --force-with-lease
```

### Issue: "Merge conflicts"
```bash
git fetch upstream
git rebase upstream/main
# Resolve conflicts in editor
git add .
git rebase --continue
git push origin feature-name --force-with-lease
```

### Issue: "Tests failing"
```bash
# Run tests locally first
pytest tests/ -v
# Check logs for errors
cat logs/*.log
```

## 📞 Need Help?

- Check existing issues & discussions
- Review documentation
- Ask in PR comments
- Reach out to maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to CheatSheet AI! 🎉
