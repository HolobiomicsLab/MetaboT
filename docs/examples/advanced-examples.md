# Advanced Usage Examples

This guide demonstrates advanced usage patterns and complex workflows in MetaboT.

## Complex Query Patterns

### 1. Multi-Criteria Analysis

Combine multiple analysis criteria in a single query:

```python
from app.core.workflow.langraph_workflow import process_workflow

# Complex query combining multiple criteria
query = """
Which lab extracts from Melochia umbellata:
1. Have compounds in positive ionization mode
2. With retention time < 2 minutes
3. Show inhibition percentage > 70% in bioassay
4. Are annotated as alkaloids by CANOPUS
Provide lab extracts, retention times, and inhibition percentage.
"""

results = process_workflow(workflow, query)
```

### 2. Cross-Reference Analysis

Compare data across different annotation methods:

```python
# Query comparing SIRIUS and ISDB annotations
query = """
For features from the Melochia umbellata taxon in pos ionization mode:
1. Get features with SIRIUS annotations
2. Find matching features in neg ionization mode
3. Compare retention times (±3 seconds)
4. Verify matching SIRIUS annotations by InCHIKey 2D
Return features, retention times, and InChIKey2D
"""

results = process_workflow(workflow, query)
```

## Custom Workflows

### 1. Batch Processing with Custom Logic

```python
from app.core.main import link_kg_database, llm_creation
from app.core.workflow.langraph_workflow import create_workflow, process_workflow
from app.core.agents.agents_factory import create_all_agents
import pandas as pd

def batch_process_samples(sample_list, workflow):
    """
    Process multiple samples with custom analysis logic.
    
    Args:
        sample_list: List of sample identifiers
        workflow: Initialized workflow instance
    
    Returns:
        DataFrame with processed results
    """
    results = []
    
    for sample in sample_list:
        # Query basic sample information
        basic_query = f"What are the chemical structure ISDB annotations for {sample}?"
        basic_results = process_workflow(workflow, basic_query)
        
        # Query bioassay results
        bioassay_query = f"List the bioassay results at 10µg/mL against T.cruzi for {sample}"
        bioassay_results = process_workflow(workflow, bioassay_query)
        
        # Combine and process results
        combined_results = {
            'sample': sample,
            'annotations': len(basic_results),
            'active_compounds': sum(1 for r in bioassay_results if r['inhibition'] > 50)
        }
        results.append(combined_results)
    
    return pd.DataFrame(results)

# Usage example
samples = ['Lovoa trichilioides', 'Tabernaemontana coffeoides', 'Melochia umbellata']
results_df = batch_process_samples(samples, workflow)
```

### 2. Custom Analysis Pipeline

```python
from typing import Dict, List, Any
import numpy as np

class MetabolomicsAnalysisPipeline:
    def __init__(self, workflow):
        self.workflow = workflow
        self.results_cache = {}
    
    def analyze_sample(self, sample_name: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a sample.
        
        Args:
            sample_name: Name of the sample to analyze
        
        Returns:
            Dictionary containing analysis results
        """
        # Get basic features
        features_query = f"What are the mass spectrometry features detected for {sample_name}?"
        features = process_workflow(self.workflow, features_query)
        
        # Get structural annotations
        structure_query = f"What are the SIRIUS structural annotations for {sample_name}?"
        structures = process_workflow(self.workflow, structure_query)
        
        # Get bioassay results
        bioassay_query = f"List all bioassay results for {sample_name}"
        bioassays = process_workflow(self.workflow, bioassay_query)
        
        # Process and combine results
        return {
            'sample_name': sample_name,
            'feature_count': len(features),
            'structure_annotations': len(structures),
            'active_compounds': self._process_bioassays(bioassays),
            'molecular_properties': self._calculate_properties(features)
        }
    
    def _process_bioassays(self, bioassays: List[Dict]) -> Dict[str, float]:
        """Process bioassay results."""
        if not bioassays:
            return {}
            
        return {
            'max_inhibition': max(b['inhibition'] for b in bioassays),
            'mean_inhibition': np.mean([b['inhibition'] for b in bioassays]),
            'active_count': sum(1 for b in bioassays if b['inhibition'] > 50)
        }
    
    def _calculate_properties(self, features: List[Dict]) -> Dict[str, float]:
        """Calculate molecular properties from features."""
        masses = [f['mass'] for f in features if 'mass' in f]
        return {
            'average_mass': np.mean(masses) if masses else 0,
            'mass_range': max(masses) - min(masses) if masses else 0
        }

# Usage example
pipeline = MetabolomicsAnalysisPipeline(workflow)
results = pipeline.analyze_sample('Tabernaemontana coffeoides')
```

## Advanced Data Integration

### 1. Combining Multiple Data Sources

```python
def integrate_metabolomics_data(workflow, sample_name: str):
    """
    Integrate data from multiple sources for comprehensive analysis.
    """
    # Get MS features
    ms_query = f"""
    What are the retention times and molecular masses of compounds 
    identified in negative ionization mode LCMS analysis from {sample_name} extracts, 
    and what are the CANOPUS chemical class annotations for those features?
    """
    ms_data = process_workflow(workflow, ms_query)
    
    # Get bioassay data
    bioassay_query = f"""
    List the bioassay results at multiple concentrations against 
    T.cruzi for lab extracts of {sample_name}
    """
    bioassay_data = process_workflow(workflow, bioassay_query)
    
    # Get structural annotations
    structure_query = f"""
    What are the SIRIUS structural annotations associated with 
    the MS2 spectra from the lab extracts of {sample_name}?
    """
    structure_data = process_workflow(workflow, structure_query)
    
    # Integrate results
    integrated_data = []
    for feature in ms_data:
        feature_info = {
            'retention_time': feature['rt'],
            'mass': feature['mass'],
            'canopus_class': feature['class']
        }
        
        # Match with structural data
        matching_structures = [
            s for s in structure_data 
            if abs(s['mass'] - feature['mass']) < 0.01
        ]
        if matching_structures:
            feature_info['structure'] = matching_structures[0]
        
        # Match with bioassay data
        matching_bioassays = [
            b for b in bioassay_data 
            if b['feature_id'] == feature['id']
        ]
        if matching_bioassays:
            feature_info['bioassay'] = matching_bioassays[0]
            
        integrated_data.append(feature_info)
    
    return integrated_data
```

### 2. Custom Visualization Pipeline

```python
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_metabolomics_results(integrated_data: List[Dict]):
    """
    Create comprehensive visualizations of metabolomics results.
    """
    # Prepare data
    masses = [d['mass'] for d in integrated_data]
    rts = [d['retention_time'] for d in integrated_data]
    
    # Create figure with multiple subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Mass distribution
    sns.histplot(masses, ax=ax1)
    ax1.set_title('Mass Distribution')
    ax1.set_xlabel('Mass (Da)')
    
    # RT vs Mass scatter plot
    sns.scatterplot(x=rts, y=masses, ax=ax2)
    ax2.set_title('Retention Time vs Mass')
    ax2.set_xlabel('Retention Time (min)')
    ax2.set_ylabel('Mass (Da)')
    
    plt.tight_layout()
    return fig

# Usage example
data = integrate_metabolomics_data(workflow, 'Tabernaemontana coffeoides')
fig = visualize_metabolomics_results(data)
plt.show()
```

## Performance Optimization

### 1. Caching Results

```python
from functools import lru_cache
import hashlib
import json

class CachedWorkflow:
    def __init__(self, workflow):
        self.workflow = workflow
        self.cache = {}
    
    @lru_cache(maxsize=1000)
    def process_query(self, query: str):
        """
        Process query with caching for improved performance.
        """
        # Generate cache key
        key = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache
        if key in self.cache:
            return self.cache[key]
        
        # Process query
        result = process_workflow(self.workflow, query)
        
        # Cache result
        self.cache[key] = result
        return result

# Usage
cached_workflow = CachedWorkflow(workflow)
result = cached_workflow.process_query("Your complex query here")
```

For more information about specific components or advanced features, refer to the [API Reference](../api-reference/core.md).