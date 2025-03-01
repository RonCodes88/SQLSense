from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec, PodSpec  
from langchain_pinecone import PineconeVectorStore
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
import time
import bs4
from dotenv import load_dotenv

load_dotenv()

class RAG:
    def __init__(self, web_urls):
        
        self.loader = WebBaseLoader(
            web_paths=web_urls,
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("contentcontainer", "belowtopnavcontainer")
                )
            ),
        )

        self.embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small"
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
        self.vectorstore = PineconeVectorStore(
            index_name=self.vectorstore_index_name,
            embedding=self.embeddings,
            pinecone_api_key=os.getenv("PINECONE_API_KEY")
        )

        # add langsmith and nemo guardrails later

    def create_pinecone_index(self, vectorstore_index_name):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        spec = ServerlessSpec(cloud='aws', region='us-west-2')
        if vectorstore_index_name in pc.list_indexes().name():
            pc.delete_index(vectorstore_index_name)
        pc.create_index(
            name=vectorstore_index_name,
            dimension=1536,
            metric='cosine',
            spec=spec
        )
        while not pc.describe_index(vectorstore_index_name).status['ready']:
            time.sleep(1)
    
    def load_docs_into_vectorstore_chain(self):
        docs = self.loader.load()
        split_docs = self.text_splitter.split_documents(docs)
        self.vectorstore.add_documents(split_docs)

    def create_retrieval_chain(self):
        self.load_docs_into_vectorstore_chain()
        self.retriever = self.vectorstore.as_retriever()
        self.rag_chain = (
            {
                "context": self.retriever | self.format_docs, "question": RunnablePassthrough()
            }
            | self.rag_prompt
            | self.groq_llm
            | StrOutputParser()
        )
        # add guardrails check here

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def query_answer(self, query, vectorstorecreated):
        if not vectorstorecreated:
            self.create_retrieval_chain()
        return self.rag_chain.invoke(query), True
