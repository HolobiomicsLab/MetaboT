# Contributing to MetaboT

Thank you for your interest in contributing to MetaboT! This guide will help you understand how to contribute effectively to the project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A GitHub account
- Basic understanding of metabolomics concepts
- Familiarity with:
  - Python programming
  - RDF and SPARQL
  - LangChain framework
  - Scientific Python libraries (numpy, pandas, etc.)

### Setting Up Development Environment

1. Fork the repository:
   ```bash
   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/MetaboT.git
   cd MetaboT
   
   # Add upstream remote
   git remote add upstream https://github.com/holobiomicslab/MetaboT.git
   ```

2. Create a virtual environment:
   ```bash
   # Using conda
   conda env create -f environment.yml
   
   # Or using venv
   python -m venv venv
   source venv/bin/activate  # Unix/macOS
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Development Workflow

### 1. Create a Branch

```bash
# Update your main
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clear, documented code
- Follow the project's coding style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run the test suite
python -m pytest app/core/tests/

# Run specific tests
python -m pytest app/core/tests/test_utils.py
```

### 4. Submit Changes

1. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: Add new feature X"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request on GitHub

## Code Style Guidelines

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write descriptive docstrings
- Keep functions focused and small

Example:
```python
from typing import Dict, Any

def process_feature(feature_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Process metabolomics feature data.
    
    Args:
        feature_data: Dictionary containing feature information
        
    Returns:
        Processed feature data with normalized values
        
    Raises:
        ValueError: If required fields are missing
    """
    if 'intensity' not in feature_data:
        raise ValueError("Missing required field: intensity")
    
    return {
        'normalized_intensity': feature_data['intensity'] / 100.0
    }
```

### Documentation Style

- Use Markdown for documentation
- Include code examples
- Provide clear explanations
- Update the changelog

## Adding New Features

### 1. Agents

When adding a new agent:

1. Create a new module in `app/core/agents/`
2. Implement the agent class
3. Add to the agent factory
4. Update documentation

Example:
```python
from app.core.agents.base import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self, model, graph):
        super().__init__(model, graph)
        self.tools = self._initialize_tools()
    
    def process(self, input_data):
        # Implementation
        pass
```

### 2. Tools

When adding new tools:

1. Create tool class in appropriate module
2. Implement required methods
3. Add tests
4. Update documentation

Example:
```python
class NewTool:
    def __init__(self):
        self.name = "new_tool"
        self.description = "Performs new analysis"
    
    def run(self, input_data):
        # Implementation
        pass
```

## Testing Guidelines

### 1. Unit Tests

- Write tests for new functionality
- Use pytest fixtures
- Mock external services
- Test edge cases

Example:
```python
import pytest
from app.core.utils import process_feature

def test_process_feature():
    # Arrange
    test_data = {'intensity': 100.0}
    
    # Act
    result = process_feature(test_data)
    
    # Assert
    assert result['normalized_intensity'] == 1.0
```

### 2. Integration Tests

- Test component interactions
- Verify workflow functionality
- Test with real data samples

## Documentation

### 1. Code Documentation

- Add docstrings to all functions/classes
- Include type hints
- Document exceptions
- Provide usage examples

### 2. User Documentation

- Update relevant .md files
- Add new features to examples
- Include configuration details
- Document breaking changes

## Pull Request Process

1. **Description**
   - Clearly describe the changes
   - Reference related issues
   - List breaking changes

2. **Review Process**
   - Address reviewer comments
   - Update tests as needed
   - Maintain clean commit history

3. **Merge Requirements**
   - Pass all tests
   - Receive approval from maintainers
   - Up-to-date documentation

## Community Guidelines

### Communication

- Be respectful and inclusive
- Use clear, technical language
- Provide context for questions
- Help others learn

### Issue Reporting

1. Search existing issues
2. Use issue templates
3. Provide reproducible examples
4. Include system information

## Getting Help

- Check the documentation
- Search existing issues
- Ask in discussions
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

Thank you for contributing to MetaboT! Your efforts help improve metabolomics research tools for everyone.