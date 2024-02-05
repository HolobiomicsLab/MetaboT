from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.request import urlopen
from urllib.parse import quote
from langchain.chains.base import Chain
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains.llm import LLMChain
from langchain_core.prompts.base import BasePromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.pydantic_v1 import Field

from prompts import (
    NPC_CLASS_PROMPT,
)


class ChemicalResolver(Chain):
    input_key: str = "query"  #: :meta private:
    output_key: str = "result"  #: :meta private:
    qa_chain: LLMChain
    csv_data: Any
    retriever: Any

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
        qa_prompt: BasePromptTemplate = NPC_CLASS_PROMPT,
        **kwargs: Any,
    ) -> ChemicalResolver:
        """Initialize from LLM."""
        qa_chain = LLMChain(llm=llm, prompt=qa_prompt)

        return cls(
            qa_chain=qa_chain,
            **kwargs,
        )
        
    # def __init__(self, llm: BaseLanguageModel, qa_prompt: BasePromptTemplate = NPC_CLASS_PROMPT, **kwargs: Any):
    #     self.qa_chain = LLMChain(llm=llm, prompt=qa_prompt)
    #     self.csv_data = self.csv_loader()
    #     self.retriever = self.npc_retriever(self.csv_data)
    #     super().__init__(**kwargs)

    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        """
        Generate SPARQL query, use it to retrieve a response from the gdb and answer
        the question.
        """
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        prompt = inputs[self.input_key]
        
        res = self.CIRconvert(prompt)
        
        if res != 'Did not work':
            res = "InChIKey is " + res
            print(res)
            return {self.output_key: res}
        else:
            print("InChIKey not found, trying NPC Classifier")
            ## verify that csv_data is in the attributes of the class
            if self.csv_data is None:
                self.csv_data = self.csv_loader()
                self.retriever = self.npc_retriever(self.csv_data)
            uris = self.retriever.get_relevant_documents(prompt)
            res = self.qa_chain.run({"chemical_name": prompt, "results": uris})
            return {self.output_key: res}
            
            
    
    def csv_loader(self):
        
        loader = CSVLoader(file_path="../data/npc_all.csv", 
                    csv_args={
        'delimiter': ',',
        'fieldnames': ['NPCClass', 'NPCPathway', 'NPCSuperClass']
    }
                    )
        return loader.load()
        
    def npc_retriever(self, data):
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)
        embeddings = OpenAIEmbeddings()
        db = FAISS.from_documents(texts, embeddings)
        return db.as_retriever(
    # search_kwargs={"k": 10}
    )
    

    #Chemical name to Standard InChIKey
    def CIRconvert(self, ids):
        try:
            url = 'http://cactus.nci.nih.gov/chemical/structure/' + quote(ids) + '/stdinchikey'
            ans = urlopen(url).read().decode('utf8')
            return ": ".join([ids, ans])
        except:
            return 'Did not work'

