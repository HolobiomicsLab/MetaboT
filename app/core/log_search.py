from typing import Dict, List
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.base import Chain
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain import hub
from langchain.chains import RetrievalQA


class QueryInput(BaseModel):
    query: str

class DocumentWrapper:
    def __init__(self, content):
        self.page_content = content

class LogMemoryAccessTool():
    def __init__(self):
        super().__init__()
        self.log_file_path = "kgbot.log"
        self.db = None


    def chroma_vector_store(self):
        # Load raw log content
        raw_log = TextLoader(self.log_file_path).load()
        
        # Use a text splitter similar to ChemicalResolver but with RecursiveCharacterTextSplitter
        text_splitter = CharacterTextSplitter(separator=" ", chunk_size=800, chunk_overlap=50)
        log_splits = text_splitter.split_documents(raw_log)

        # Now, use these wrapped documents with Chroma
        self.db = Chroma.from_documents(documents=log_splits, embedding=OpenAIEmbeddings())
    

    def generate_answer(self, query_input: QueryInput) -> str:

        self.chroma_vector_store()
        self.retriever = self.db.as_retriever(search_type="similarity", search_kwargs={"k":3})

        self.specialized_prompt = hub.pull("rlm/rag-prompt")
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0.0)

        def format_docs(docs):
            # Adapt format_docs to work with the structure of DocumentWrapper instances
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.specialized_prompt
            | self.llm
            | StrOutputParser()
        )

        #self.qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.retriever)

        response = self.rag_chain.invoke(query_input.query)

        #response  = self.qa({"query": query_input.query})

        return response
    
    def _call(self, input):
        query_input = QueryInput(query=input['query'])
        return self.generate_answer(query_input)

    def input_keys(self) -> List[str]:
        return ["query"]

    def output_keys(self) -> List[str]:
        return ["answer"]