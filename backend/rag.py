from langchain_community.document_loaders import WebBaseLoader
# from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_text_splitters import CharacterTextSplitter
# from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from pinecone import Pinecone, ServerlessSpec, PodSpec  
from langchain_pinecone import PineconeVectorStore
from langchain import hub
from langchain.chains import RetrievalQA
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
import time
import bs4
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = 'sqlsense'

class RAG:
    def __init__(self, web_urls):
        
        self.vectorstore_index_name = "sqlsense-rag-index"
        self.loader = WebBaseLoader(
            web_paths=web_urls,
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("contentcontainer", "belowtopnavcontainer", "belowtopnav")
                )
            ),
        )     

        self.groq_llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"), 
            model="llama3-70b-8192", 
            temperature=0
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, 
            chunk_overlap=100
        )

        self.create_pinecone_index(self.vectorstore_index_name)

        self.rag_prompt = hub.pull(
            "rlm/rag-prompt", 
            api_key=os.getenv("LANGSMITH_API_KEY")
        )
        # add langsmith and nemo guardrails later

    def create_pinecone_index(self, vectorstore_index_name):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))  
        spec = ServerlessSpec(cloud='aws', region='us-east-1')  
        if vectorstore_index_name not in pc.list_indexes().names():  
            print(f"Creating new index {vectorstore_index_name}")
            pc.create_index(  
                vectorstore_index_name,  
                dimension=1536,
                metric='cosine',  
                spec=spec  
            )
            while not pc.describe_index(vectorstore_index_name).status['ready']:  
                    time.sleep(1)
        else:
            print(f"Index {vectorstore_index_name} already exists.")
    
    def load_docs_into_vectorstore_chain(self):
        docs = self.loader.load()
        print(f"Loaded {len(docs)} documents")
        split_docs = self.text_splitter.split_documents(docs)
        self.embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small"
        )
        print(self.embeddings)
        self.vectorstore = PineconeVectorStore(
            index_name=self.vectorstore_index_name,
            embedding=self.embeddings,
            pinecone_api_key=os.getenv("PINECONE_API_KEY")
        )
        self.vectorstore.add_documents(split_docs)
        print(self.vectorstore)
        print(f"Added {len(split_docs)} documents to vectorstore")

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    def create_chain(self):
        self.load_docs_into_vectorstore_chain()
        self.retriever = self.vectorstore.as_retriever()
        print("Retriever is:", self.retriever)
        self.rag_chain = (
            {"context": self.retriever | self.format_docs, "question": RunnablePassthrough(),}
            | self.rag_prompt
            | self.groq_llm
            | StrOutputParser()
        )
        # add guardrails check here

    # def create_chain(self):
    #     self.load_docs_into_vectorstore_chain()
    #     self.qa_chain = RetrievalQA.from_llm(
    #         self.groq_llm, retriever=self.vectorstore.as_retriever(), prompt=self.rag_prompt
    #     )

    def query_answer(self, query, vectorstorecreated):
        if not vectorstorecreated:
            self.create_chain()
            vectorstorecreated = True
        
        return self.rag_chain.invoke(query), vectorstorecreated
        # return self.qa_chain(query), vectorstorecreated
