# Developer guide

This section contains information for developers who want to contribute to Flee, understand the codebase, or extend the simulation.

---

## Pages in this section

- **[Contributing](contributing.md)** — how to report bugs, submit features, and contribute code
- **[Code architecture](architecture.md)** — how the Flee codebase is structured
- **[Writing and running tests](testing.md)** — how to run the test suite and add new tests
- **[Adding features](adding-features.md)** — guidelines for extending Flee
- **[Roadmap](roadmap.md)** — planned features and known limitations

---

## Quick start for developers

```sh
# Clone and install in editable mode
git clone https://github.com/djgroen/flee.git
cd flee
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/
```
