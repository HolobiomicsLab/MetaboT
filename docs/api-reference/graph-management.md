# Graph Management API Reference

This document details the graph management system in MetaboT, focusing on the RDF graph implementation and related utilities.

## RDF Graph Custom

The `RdfGraphCustom` module (`app.core.graph_management.RdfGraphCustom`) provides the core functionality for interacting with RDF-based knowledge graphs.

### Class: RdfGraph

```python
class RdfGraph:
    """
    Custom RDF graph implementation for metabolomics data management.
    Provides methods for graph operations and SPARQL query execution.
    """
    
    def __init__(self, query_endpoint: str, standard: str = "rdf"):
        """
        Initialize RDF graph connection.
        
        Args:
            query_endpoint (str): SPARQL endpoint URL
            standard (str): RDF standard to use (default: "rdf")
        """
```

#### Key Methods

##### Query Execution

```python
def execute_query(self, query: str) -> Dict[str, Any]:
    """
    Execute a SPARQL query against the graph.
    
    Args:
        query (str): SPARQL query string
    
    Returns:
        Dict[str, Any]: Query results
    
    Raises:
        QueryExecutionError: If query execution fails
    """
```

##### Schema Management

```python
@property
def get_schema(self) -> Dict[str, Any]:
    """
    Retrieve the current graph schema.
    
    Returns:
        Dict[str, Any]: Graph schema information
    """
```

##### Graph Operations

```python
def save(self, path: str = None) -> None:
    """
    Save the current graph state.
    
    Args:
        path (str, optional): Path to save the graph
    """

def load(self, path: str) -> None:
    """
    Load a graph from file.
    
    Args:
        path (str): Path to the graph file
    """
```

## Query Templates

The system includes predefined SPARQL query templates for common operations.

### Basic Queries

```sparql
# Class Information Query
SELECT DISTINCT ?cls ?com ?label
WHERE {
    ?cls a rdfs:Class .
    OPTIONAL { ?cls rdfs:comment ?com }
    OPTIONAL { ?cls rdfs:label ?label }
}
GROUP BY ?cls ?com ?label

# Class Relationships Query
SELECT ?property (SAMPLE(COALESCE(?type, STR(DATATYPE(?value)), "Untyped")) AS ?valueType)
WHERE {
    {
        SELECT ?instance WHERE {
            ?instance a <{class_uri}> .
        } LIMIT 1000
    }
    ?instance ?property ?value .
    OPTIONAL {
        ?value a ?type .
    }
}
GROUP BY ?property ?type
LIMIT 300
```

## Graph Utilities

### URI Management

```python
class URIManager:
    """
    Manages URI handling and validation.
    """
    
    @staticmethod
    def validate_uri(uri: str) -> bool:
        """
        Validate a URI string.
        
        Args:
            uri (str): URI to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
```

### Query Building

```python
class QueryBuilder:
    """
    Helps construct SPARQL queries programmatically.
    """
    
    def __init__(self):
        self.prefixes = {}
        self.where_clauses = []
        self.limit = None
    
    def add_prefix(self, prefix: str, uri: str) -> None:
        """
        Add a prefix to the query.
        
        Args:
            prefix (str): Prefix label
            uri (str): URI for the prefix
        """
    
    def build(self) -> str:
        """
        Build the complete SPARQL query.
        
        Returns:
            str: Formatted SPARQL query
        """
```

## Usage Examples

### Basic Graph Operations

```python
from app.core.graph_management.RdfGraphCustom import RdfGraph

# Initialize graph
graph = RdfGraph(
    query_endpoint="https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
)

# Execute a simple query
results = graph.execute_query("""
    SELECT ?s ?p ?o
    WHERE {
        ?s ?p ?o
    }
    LIMIT 10
""")

# Save graph state
graph.save("graph_backup.pkl")
```

### Complex Query Example

```python
# Query for chemical structures with specific properties
query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX chemical: <http://example.org/chemical/>

SELECT ?compound ?mass ?structure
WHERE {
    ?compound rdf:type chemical:Compound ;
             chemical:mass ?mass ;
             chemical:structure ?structure .
    FILTER(?mass > 300.0)
}
ORDER BY ?mass
LIMIT 100
"""

results = graph.execute_query(query)
```

### Using Query Builder

```python
builder = QueryBuilder()
builder.add_prefix("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
builder.add_prefix("chemical", "http://example.org/chemical/")

builder.add_where_clause("?compound rdf:type chemical:Compound")
builder.add_where_clause("?compound chemical:mass ?mass")
builder.set_limit(100)

query = builder.build()
results = graph.execute_query(query)
```

## Error Handling

```python
class GraphError(Exception):
    """Base class for graph-related errors."""
    pass

class ConnectionError(GraphError):
    """Raised when unable to connect to the SPARQL endpoint."""
    pass

class QueryError(GraphError):
    """Raised when a SPARQL query fails."""
    pass
```

### Error Handling Example

```python
try:
    results = graph.execute_query(query)
except QueryError as e:
    logger.error(f"Query execution failed: {e}")
    # Handle error appropriately
except ConnectionError as e:
    logger.error(f"Graph connection failed: {e}")
    # Handle connection error
```

## Performance Considerations

1. **Query Optimization**
   - Use appropriate LIMIT clauses
   - Include specific graph patterns
   - Consider query complexity

2. **Connection Management**
   - Maintain persistent connections
   - Handle timeouts appropriately
   - Implement connection pooling for high-load scenarios

3. **Data Volume**
   - Consider pagination for large result sets
   - Use streaming for large data transfers
   - Implement caching where appropriate

For more detailed information about specific graph operations or advanced usage, refer to the respective module documentation.