

class RunSparql:
    def __init__(self, endpoint: str, tool_name: str, tool_desc: str):
        self.endpoint = endpoint
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(600)  # You can adjust the timeout as needed

    @staticmethod
    def _format(results):
        """Simplify results from SPARQL query."""
        return [
            {key: result[key]['value'] for key in result}
            for result in results['results']['bindings']
        ]

    def run_query(self, query: str):
        """Run a SPARQL query and handle potential errors."""
        self.sparql.setQuery(query)

        try:
            results = self.sparql.query().convert()
            if not results['results']['bindings']:
                return "No results were found. Please try a different query."

            formatted_results = self._format(results)

            token_count = count_tokens(str(formatted_results))

            if token_count > 3500:
                return (f"Results from query are too long ({token_count} tokens). "
                        "Consider running this query manually.")
            return formatted_results
        except Exception as e:
            # For production code, consider logging the error message as well.
            return f"An error occurred: {e}"

    def make_tool(self):
        """Create a tool with the defined specifications."""
        self.tool = Tool(
            name=self.tool_name,
            description=self.tool_desc,
            func=self.run_query,
        )
        
        
        

### SPARQL TEMPLATE TOOL ##############################

class QueryTool():
    def __init__(
        self,
        prompt: str,
        tool_name: str,
        tool_desc: str,
        endpoint: str,
        parser: Optional[Callable] = None
    ):
        # Initialize the QueryTool object with the given prompt, tool description, tool name, format function, and SPARQL endpoint
        self.endpoint = endpoint
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(600)
        self.prompt = prompt
        self.tool_desc = tool_desc
        self.tool_name = tool_name
        # Using 'or' for default assignment
        self.parser = parser or (lambda x: x)
        self.matches = self.parse_inputs()

    def parse_inputs(self):
        """Parse the prompt to find the input variables using regex and store the matches."""
        pattern = r'(?<!{){([^{}]+)}(?!})'
        return re.findall(pattern, self.prompt)

    def run_query(self, query: str):
        """
        Execute the SPARQL query after replacing placeholders with actual values.
        query: str, the input string
        """
        try:  # Robust error handling is crucial, especially for code interacting with external systems or user inputs.
            kwargs = dict(zip(self.matches, query.split(',')))

            if not all(kwargs.values()):  # empty string '', 0, None, etc. are considered false
                return "Please provide all the required inputs."

            # Format the query string where each '{K}' is replaced by V in kwargs
            query = self.prompt.format(**kwargs)
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()  # Execute the SPARQL query

            if results:
                return self.parser(results['results']['bindings'])
            return None

        # Catching all exceptions can hide unexpected errors. Specify particular ones if possible.
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def make_tool(self):
        # Create a Tool object with the specified name, description, and function
        return Tool(
            name=self.tool_name,
            description=self.tool_desc,
            func=self.execute_query,
        )
