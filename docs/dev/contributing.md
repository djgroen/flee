# Contributing to Flee

Contributions are welcome, and they are greatly appreciated. Every contribution helps, and credit is always given.

---

## Ways to contribute

### Report bugs

File a bug report at [https://github.com/djgroen/flee/issues](https://github.com/djgroen/flee/issues).

When reporting a bug, please include:
- Your operating system name and version
- Python version and relevant package versions
- Detailed steps to reproduce the issue

### Fix bugs

Browse the GitHub issues. Anything tagged `bug` and `help wanted` is open for contribution.

### Implement features

Browse the GitHub issues. Anything tagged `enhancement` and `help wanted` is available to work on.

### Improve documentation

Flee always benefits from better documentation — whether in the official docs, in code docstrings, or in blog posts and tutorials. To contribute to the docs, edit files in `flee/docs/` and submit a pull request.

### Submit feedback

File an issue at [https://github.com/djgroen/flee/issues](https://github.com/djgroen/flee/issues).

When proposing a new feature:
- Explain in detail how it would work
- Keep the scope narrow to make it easier to implement
- Note that this is a volunteer-driven project

---

## Pull request workflow

1. Fork the Flee repository on GitHub
2. Clone your fork:
   ```sh
   git clone https://github.com/<your-username>/flee.git
   ```
3. Create a feature branch:
   ```sh
   git checkout -b my-feature
   ```
4. Make your changes and write tests (see [Writing and running tests](testing.md))
5. Ensure all tests pass:
   ```sh
   pytest tests/
   ```
6. Commit with a clear message:
   ```sh
   git commit -m "Add: brief description of change"
   ```
7. Push and open a pull request on GitHub

---

## Code style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Keep functions focused on a single responsibility
- Add docstrings to public functions and classes

---

## See also

- [Code architecture](architecture.md) — understanding the codebase before contributing
- [Adding features](adding-features.md) — where to add new functionality
