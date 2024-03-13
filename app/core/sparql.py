
from __future__ import annotations

from typing import Any, Dict, List, Optional

from RdfGraphCustom import RdfGraph
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts.base import BasePromptTemplate
from langchain_core.pydantic_v1 import Field

from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.chains.base import Chain
from prompts import (
    SPARQL_GENERATION_SELECT_PROMPT,
)
from langchain.chains.llm import LLMChain
import re


class GraphSparqlQAChain(Chain):
    """Question-answering against an RDF or OWL graph by generating SPARQL statements."""

    graph: RdfGraph = Field(exclude=True)
    sparql_generation_select_chain: LLMChain
    input_key: str = "question"  #: :meta private:
    entities_key: str = "entities"  #: :meta private:
    output_key: str = "result"  #: :meta private:
    sparql_key: str = "sparql_query_used"  #: :meta private:

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        _output_keys = [self.output_key]
        return _output_keys

    @classmethod
    def from_llm(
        cls,
        llm: BaseLanguageModel,
        *,
        sparql_select_prompt: BasePromptTemplate = SPARQL_GENERATION_SELECT_PROMPT,
        **kwargs: Any,
    ) -> GraphSparqlQAChain:
        """
        Initializes a `GraphSparqlQAChain` object using a base language model (`BaseLanguageModel`) for SPARQL query generation.

        :param cls: Reference to the class itself, indicating the method belongs to the class.
        :param llm: An instance of `BaseLanguageModel`, utilized for generating natural language prompts for SPARQL query generation.
        :return: An instance of `GraphSparqlQAChain`.
        """
        sparql_generation_select_chain = LLMChain(
            llm=llm, prompt=sparql_select_prompt)

        return cls(
            sparql_generation_select_chain=sparql_generation_select_chain,
            **kwargs,
        )

    @staticmethod
    def remove_markdown_quotes(query_with_markdown):
        """
        The `remove_markdown_quotes` function removes markdown quotes from a given query.
        """
        txt = re.sub(r"```sparql", "", query_with_markdown)
        cleaned_query = re.sub(r"```", "", txt)

        return cleaned_query

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        """
        Generate SPARQL query, use it to retrieve a response from the gdb and answer the question.
        """
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        prompt = inputs[self.input_key]
        entities = inputs[self.entities_key]

        generated_sparql = self.sparql_generation_select_chain.run(
            {
                "question": prompt,
                "entities": entities,
                "schema": self.graph.get_schema
            },
            callbacks=callbacks,
        )

        # TODO [Franck]: why do we need this? The prompt explicitely says to NOT return any markdown, still there might be some?
        generated_sparql = self.remove_markdown_quotes(generated_sparql)

        _run_manager.on_text("Generated SPARQL:",
                             end="\n", verbose=self.verbose)
        _run_manager.on_text(
            generated_sparql, color="green", end="\n", verbose=self.verbose
        )

        result = self.graph.query(generated_sparql)

        contextualized_result = {'query': generated_sparql, 'result': result}
        return {self.output_key: contextualized_result}
