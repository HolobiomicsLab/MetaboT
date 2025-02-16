# Contributing to 🧪 MetaboT 🍵 📝

We appreciate your interest in contributing to 🧪 MetaboT 🍵! Below are the guidelines to help you get started.

---

## How to Contribute 🤝

### Fork the Repository

Fork the [MetaboT repository](https://github.com/holobiomicslab/MetaboT) to your GitHub account.

Clone your forked repository to your local machine:

- Fork the repository on GitHub.
- Clone your fork and check out a new branch from the [`dev` branch](https://github.com/holobiomicslab/MetaboT/tree/dev).

```bash
git clone https://github.com/<your-username>/MetaboT.git
cd MetaboT
git checkout -b dev
```

### Create a Branch

Create a new branch for your feature or bugfix. For example, if you're working on a new feature, you might create a branch off the [`dev` branch](https://github.com/holobiomicslab/MetaboT/tree/dev).

#### Development Process

**Making Changes**

- Make your changes ensuring all references to files (e.g., configuration files like [app/config/params.ini](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/params.ini)) are updated as needed.
- Commit your changes with clear, meaningful commit messages.
- Push your feature branch and open a pull request against the [`dev` branch](https://github.com/holobiomicslab/MetaboT/tree/dev).


### Code Guidelines

- Follow the existing code style (Google DocString).
- Write clear and concise commit messages.
- Include comments and docstrings where necessary.

---

#### Code Standards 

- Follow **PEP8** for Python code. See the [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/).
- Include detailed documentation and inline comments where applicable.

---

#### Tests 

You can find our test suite in the [app/core/tests/](https://github.com/holobiomicslab/MetaboT/tree/main/app/core/tests) directory.

#### Documentation

Update the documentation to reflect your changes. This includes:

- Docstrings in the code.
- Relevant Markdown files in the [docs/ directory](https://github.com/holobiomicslab/MetaboT/tree/main/docs), including:
  - [API Reference](https://github.com/holobiomicslab/MetaboT/tree/main/docs/api-reference)
  - [User Guide](https://github.com/holobiomicslab/MetaboT/tree/main/docs/user-guide)
  - [Examples](https://github.com/holobiomicslab/MetaboT/tree/main/docs/examples)
  - [Getting Started](https://github.com/holobiomicslab/MetaboT/tree/main/docs/getting-started)

---

## Submitting Your Changes 📤

### Commit Your Changes

Commit your changes with a descriptive message:

```bash
git add .
git commit -m "Add new feature X"
```

### Push to Your Fork

Push your changes to your forked repository:

```bash
git push origin my-feature-branch
```

### Open a Pull Request

Open a pull request from your branch to the [`dev` branch](https://github.com/holobiomicslab/MetaboT/tree/dev) of the original repository. Provide a clear description of your changes and any relevant information.

---

### Code Review

Your pull request to the [`dev` branch](https://github.com/holobiomicslab/MetaboT/tree/dev) will be reviewed by an AI-agent and then by the maintainers. They may request changes or provide feedback. Please be responsive and address any comments or suggestions.

---

## Community 👥

- You are welcome to use, reuse, and enrich 🧪 MetaboT 🍵.
- Be respectful and considerate in your interactions.
- Help others and share your knowledge.
- Check our [examples](https://github.com/holobiomicslab/MetaboT/tree/main/docs/examples) for guidance.

---

## Additional Resource 📚

- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)

---

Thank you for contributing to 🧪 MetaboT 🍵! Your efforts help make this project better for everyone.