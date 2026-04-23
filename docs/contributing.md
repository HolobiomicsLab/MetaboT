# Contributing

Thank you for helping improve MetaboT. Contributions are welcome across code, prompts, evaluation, examples, and documentation.

## Development Workflow

1. Fork the repository.
2. Clone your fork locally.
3. Create a feature branch from `main`.
4. Make and test your changes.
5. Open a pull request back to `main`.

Example:

```bash
git clone https://github.com/<your-username>/MetaboT.git
cd MetaboT
git checkout -b my-feature
```

## What We Appreciate Most

- bug fixes and reliability improvements
- clearer prompts and better agent coordination
- documentation improvements
- new examples and benchmarks
- portability improvements for new knowledge graphs

## Code Style

- Follow standard Python style and keep changes readable.
- Add comments where they clarify non-obvious logic.
- Prefer small, focused pull requests over large mixed changes.
- Update docs when behavior, configuration, or setup changes.

## Tests and Validation

Relevant code and tests live under:

- `app/core/`
- `app/tests/`
- `docs/`

Before opening a pull request, run the checks that make sense for your change. At minimum, a lightweight smoke test is helpful:

```bash
python -m app.core.main -q 1
```

If you change prompts, routing, or SPARQL behavior, include a short note in the pull request explaining what you validated.

## Documentation Changes

Documentation is part of the product. If you change:

- setup steps
- environment variables
- CLI behavior
- agent roles
- endpoint assumptions

please update the corresponding pages in `docs/` and, when relevant, `README.md`.

## Pull Requests

When you open a pull request:

- explain the user-facing motivation
- summarize the main changes
- mention how you tested them
- link related issues or discussions when available

Clear PR descriptions make review much faster.

## Community

Please be respectful, generous, and constructive in discussion and review. MetaboT sits at the intersection of AI, knowledge graphs, and metabolomics, so clear collaboration matters a lot.

## Useful References

- [Documentation Home](index.md)
- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [Examples](examples/basic-usage.md)
