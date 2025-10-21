# Contributing to YouTube to Medium

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Error messages or logs

### Suggesting Features

Feature requests are welcome! Please include:
- Clear description of the feature
- Use case and benefits
- Examples of how it would work
- Any implementation ideas

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly**
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## Development Setup

```bash
git clone <your-fork>
cd yt2medium
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small
- Comment complex logic

## Testing

Before submitting:
```bash
python test_setup.py
python cli.py "https://www.youtube.com/watch?v=example" --stats-only
```

## Areas for Contribution

### High Priority
- [ ] Add support for more video platforms (Vimeo, Dailymotion)
- [ ] Direct Medium API integration for publishing
- [ ] Multi-language support
- [ ] Custom brand voice configuration
- [ ] SEO optimization features

### Medium Priority
- [ ] Batch processing improvements
- [ ] Better error handling and retry logic
- [ ] Progress bars for long operations
- [ ] Export to other formats (HTML, PDF)
- [ ] Analytics dashboard

### Nice to Have
- [ ] Browser extension
- [ ] Mobile app
- [ ] Scheduled generation
- [ ] Template system for different blog styles
- [ ] Integration with other blogging platforms

## Prompt Engineering

The `prompts.py` file is crucial for output quality. When modifying prompts:
- Test with multiple video types
- Check engagement scores
- Verify Medium formatting
- Ensure natural, readable output
- Maintain the storytelling focus

## Documentation

- Update README.md for new features
- Add examples for new functionality
- Update setup_guide.md if setup changes
- Document new configuration options

## Pull Request Guidelines

### Good PR:
- Focused on single feature/fix
- Includes tests
- Updates documentation
- Clear commit messages
- Follows code style

### PR Checklist:
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tested locally
- [ ] No breaking changes (or clearly noted)

## Community

- Be respectful and constructive
- Help others in issues and discussions
- Share your success stories
- Provide feedback on features

## Questions?

Open an issue with the "question" label or reach out to maintainers.

Thank you for contributing! 🙌
