# Basic Usage Examples 🚀

This guide provides practical examples of using 🧪 MetaboT 🍵 for common metabolomics analysis tasks.

---
## Standard Queries 🔬

### Feature Analysis

Count features with matching annotations:

```bash
python -m app.core.main -c "How many features have the same SIRIUS/CSI:FingerID and ISDB annotation?"
```

### Chemical Class Analysis

Query specific chemical classes:

```bash
python -m app.core.main -c "Which extracts have features annotated as aspidosperma-type alkaloids by CANOPUS with a probability score above 0.5?"
```

### Structure Identification

Get structural annotations for a specific plant:

```bash
python -m app.core.main -c "What are the SIRIUS structural annotations for Tabernaemontana coffeoides?"
```

---
## Advanced Queries ⚡️

### Cross-Mode Feature Matching

Match features across ionization modes:

```bash
python -m app.core.main -c "Filter the pos ionization mode features of Melochia umbellata annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds)"
```

### Bioassay Integration

Query bioassay results:

```bash
python -m app.core.main -c "List the bioassay results at 10µg/mL against T.cruzi for lab extracts of Tabernaemontana coffeoides"
```

### Complex Analysis

Combine multiple analysis aspects:

```bash
python -m app.core.main -c "Which lab extracts from Melochia umbellata yield compounds that have a retention time of less than 2 minutes and demonstrate an inhibition percentage greater than 70% in bioassay results?"
```

---
## Programmatic Usage 🖥️

### Basic Setup

```python
# Initialize components
from app.core.main import llm_creation
from app.core.workflow.langraph_workflow import create_workflow
# Initialize components
endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
models = llm_creation()  # [llm_creation](https://github.com/nothiasl/MetaboT/blob/main/app/core/main.py)
# Create workflow
workflow = create_workflow(
    models=models,
    endpoint_url=endpoint_url,
    evaluation=False,

)
```

### Custom Query Processing

```python
from app.core.workflow.langraph_workflow import process_workflow

# Process a custom query
query = "What are the chemical structure ISDB annotations for Lovoa trichilioides?"
process_workflow(workflow, query)  # [process_workflow](https://github.com/nothiasl/MetaboT/blob/main/app/core/workflow/langraph_workflow.py)
```

### Batch Processing

```python
# Process multiple queries
queries = [
    "Count the number of LCMS features in negative ionization mode",
    "What are the mass spectrometry features detected for Rumex nepalensis?",
    "What is the highest inhibition percentage for compounds from Rauvolfia vomitoria?"
]

for query in queries:
    process_workflow(workflow, query)
    # Process results as needed
```

---

## Best Practices 👍

1. **Query Optimization**

    - Be specific in your queries
    - Include relevant constraints
    - Consider data volume

2. **Resource Management**

    - Close connections when done
    - Monitor memory usage
    - Handle large result sets appropriately

3. **Error Handling**
   ```python
   try:
        process_workflow(workflow, query)
   except Exception as e:
       print(f"Error processing query: {e}")
       # Handle error appropriately
   ```

---
## Common Patterns 🔁

### Feature Filtering

```python
# Filter features by retention time
query = "List LC-MS features with chemical class annotation by CANOPUS and retention time between 5-7 minutes"
```

### Annotation Comparison

```python
# Compare annotations across methods
query = "Which compounds have annotations from both ISDB and SIRIUS, and what are their molecular masses?"
```

### Multi-criteria Analysis

```python
# Combine multiple criteria
query = "Which plant has extracts containing compounds that demonstrated inhibition rates above 50% and are above 800 Da in mass?"
```
