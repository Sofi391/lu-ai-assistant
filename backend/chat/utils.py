import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from .models import KnowledgeBase
from pgvector.django import L2Distance

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found! Check your .env file.")
genai.configure(api_key=GEMINI_API_KEY)

class RAGService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=80,
            length_function=len
        )
        self.embedding_model = "models/gemini-embedding-001"
        self.llm_model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def ingest_text(self, text: str, metadata: dict = None):
        chunks = self.text_splitter.split_text(text)
        embeddings_result = genai.embed_content(
            model=self.embedding_model,
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )
        embeddings = embeddings_result['embedding']
        
        # Create KnowledgeBase objects using Django ORM
        knowledge_objects = []
        for content, embedding in zip(chunks, embeddings):
            knowledge_objects.append(KnowledgeBase(
                content=content,
                embedding=embedding,
                metadata=metadata
            ))
        
        # Bulk create for better performance
        KnowledgeBase.objects.bulk_create(knowledge_objects)

    def get_response(self, question: str) -> str:
        # 1. Get embedding for the query
        query_embedding_result = genai.embed_content(
            model=self.embedding_model,
            content=question,
            task_type="RETRIEVAL_QUERY"
        )
        query_embedding = query_embedding_result['embedding']

        # 2. Retrieve Top 3 using Django ORM with pgvector
        similar_docs = KnowledgeBase.objects.order_by(
            L2Distance('embedding', query_embedding)
        )[:3]
        
        context = [doc.content for doc in similar_docs]

        if not context:
            return "No relevant information found."

        # 3. Generate Answer
        context_str = "\n".join([f"- {c}" for c in context])
        prompt = f"""
        You are "LU", a helpful chatbot.
        Answer the question based ONLY on the context. 
        CONTEXT: {context_str}
        QUESTION: {question}
        """
        response = self.llm_model.generate_content(prompt)
        return response.text
