# Graph Management API Reference 📡

This document details the graph management system in 🧪 MetaboT 🍵, focusing on the RDF graph implementation and related utilities.

---
## RDF Graph Custom 🔄

The [`RdfGraphCustom`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/graph_management/RdfGraphCustom.py) module provides core functionality for interacting with RDF-based knowledge graphs, with a focus on managing and querying RDF schema information. It is primarily used by the SPARQL query generation chain to execute queries against the configured endpoint.

### Class: RdfGraph

The `RdfGraph` class handles RDF graph representation, focusing on schema management and SPARQL query execution. The class primarily works with rdfs:Class nodes and their relationships.

#### Constructor

```python
def __init__(
    self,
    query_endpoint: Optional[str],
    standard: Optional[str] = "rdf",
    schema_file: Optional[str] = None,
    auth: Optional[Tuple[str, str]] = None
) -> None
```

**Parameters:**

- `query_endpoint` (Optional[str]): SPARQL endpoint URL for queries (read access)
- `standard` (Optional[str]): RDF standard to use - one of "rdf", "rdfs", or "owl" (default: "rdf")
- `schema_file` (Optional[str]): Path to file containing RDF graph schema in turtle format
- `auth` (Optional[Tuple[str, str]]): Optional authentication credentials as (username, password) tuple. If not provided, the connection will be attempted without authentication. This is useful when users need to connect to a local SPARQL endpoint that requires authentication.

**Environment Variables:**

- `SPARQL_USERNAME`: Username for endpoint authentication (optional)
- `SPARQL_PASSWORD`: Password for endpoint authentication (optional)
- `KG_ENDPOINT_URL`: URL of the SPARQL endpoint (defaults to "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG")

**Raises:**

- `ValueError`: If standard is not one of rdf, rdfs, or owl
- `ValueError`: If no query endpoint is provided

#### Core Methods

##### Query Execution 🚀

```python
def query(self, query: str) -> List[csv.DictReader]:
    """
    Execute a SPARQL query against the graph.
    
    Args:
        query (str): SPARQL query string to execute
    
    Returns:
        List[csv.DictReader]: Query results as list of dictionaries
    
    Raises:
        ValueError: If query is invalid or execution fails
    """
```

##### Schema Management 🏗️

```python
def load_schema(self) -> None:
    """
    Loads graph schema information based on the specified standard (rdf, rdfs, owl).
    The schema is either loaded from a file (if schema_file was provided) or 
    extracted from the endpoint.
    """

@property
def get_schema(self) -> str:
    """
    Retrieve the current graph schema.
    
    Returns:
        str: Complete graph schema information including namespaces and node types
    """
```

##### Property and Value Types 🔍

```python
def get_prop_and_val_types(self, class_uri: str) -> List[Tuple[str, str]]:
    """
    Retrieves and filters properties and their value types for a specified class URI.
    
    Args:
        class_uri (str): The URI of the class to analyze
        
    Returns:
        List[Tuple[str, str]]: List of (property_uri, value_type) pairs
    """
```

##### Graph Generation 🌐

```python
def get_graph_from_classes(self, classes: List[Dict]) -> rdflib.graph.Graph:
    """
    Generates an RDF graph from class definitions.
    
    Example triple:
        ns1:InChIkey ns1:has_npc_pathway ns1:ChemicalTaxonomy .
    
    Args:
        classes (List[Dict]): List of class definitions
        
    Returns:
        rdflib.graph.Graph: Generated RDF graph
    """
```

##### Namespace Management 🏷️

```python
def get_namespaces(self) -> List[Tuple[str, str]]:
    """
    Retrieve namespace definitions.
    
    Returns:
        List[Tuple[str, str]]: List of (prefix, uri) pairs
        
    Raises:
        ValueError: If no namespaces are found
    """
```

---
## Usage Examples 💡

### Basic Graph Operations

```python
from app.core.graph_management.RdfGraphCustom import RdfGraph

# Initialize graph without authentication (public endpoint)
graph = RdfGraph(
    query_endpoint="https://example.org/sparql"
)

# Initialize graph with authentication (local/private endpoint)
graph = RdfGraph(
    query_endpoint="http://localhost:3030/sparql",
    auth=("username", "password")  # For endpoints requiring authentication
)

# Execute a simple query
results = graph.query("""
    SELECT ?s ?p ?o
    WHERE {
        ?s ?p ?o
    }
    LIMIT 10
""")

# Get schema information
schema = graph.get_schema
```

### Working with Class Properties

```python
# Get properties for a specific class
class_uri = "http://example.org/onto#Compound"
props = graph.get_prop_and_val_types(class_uri)

# Display properties and their value types
for prop_uri, value_type in props:
    print(f"Property: {prop_uri}")
    print(f"Value type: {value_type}")
```

---
## Implementation Details 🔧

This module is designed to work as part of the larger MetaboT system. It performs the following functions:

1. **Configuration**

    -  Automatically connects to the specified SPARQL endpoint
    - Handles authentication if credentials are provided
    - Uses environment variables for flexible configuration


2. **Query Processing**

    - Works with the SPARQL query generation chain
    - Executes generated queries against the endpoint
    - Returns results in a standardized format


3. **Schema Management**

    - Can load schema from file or extract from endpoint
    - Manages namespace definitions
    - Filters system-specific properties

4. **Error Handling**

    - Validates endpoint configuration
    - Handles connection issues gracefully
    - Provides clear error messages


For more detailed information about using this module within the MetaboT system, refer to the inline code documentation in [RdfGraphCustom.py](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/graph_management/RdfGraphCustom.py).