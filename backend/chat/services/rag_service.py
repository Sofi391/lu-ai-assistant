import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from ..models import KnowledgeBase
from pgvector.django import L2Distance
from .llm_service import LLMService
from google.api_core.exceptions import DeadlineExceeded
from django.db import OperationalError



FOLLOW_UP_PHRASES = {
    "tell me more",
    "why",
    "how",
    "explain",
    "explain that",
    "and",
    "continue",
    "elaborate",
    "summary",
    "thank you",
    "what",
    "could you",
    "do you",
    "does it",
    "does that",
    "is it",
    "is that",
    "can you",
    "please",
    "will"
}


def is_follow_up(question: str) -> bool:
    q = question.strip().lower()
    if len(q.split()) <= 4:
        return True
    if q in FOLLOW_UP_PHRASES:
        return True
    return False


# Configure Gemini
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found! Check your .env file.")
genai.configure(api_key=GEMINI_API_KEY)


class RAGService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=60,
            length_function=len
        )
        self.embedding_model = "models/gemini-embedding-001"
        self.llm_service = LLMService()

    def ingest_text(self, text: str, metadata: dict = None):
        chunks = self.text_splitter.split_text(text)

        embeddings_result = genai.embed_content(
            model=self.embedding_model,
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )

        embeddings = embeddings_result["embedding"]

        knowledge_objects = [
            KnowledgeBase(
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            for content, embedding in zip(chunks, embeddings)
        ]

        KnowledgeBase.objects.bulk_create(knowledge_objects)

    def retrieve_context(self, embedding, top_k=3):
        docs = KnowledgeBase.objects.order_by(
            L2Distance("embedding", embedding)
        )[:top_k]

        return [doc.content for doc in docs]

    def get_response(self, question: str, history: str) -> str:
        try:
            query_embedding_result = genai.embed_content(
                model=self.embedding_model,
                content=question,
                task_type="RETRIEVAL_QUERY",
                request_options={"timeout": 10}
            )

            query_embedding = query_embedding_result["embedding"]
            if not query_embedding:
                return {"error": True,"message": "Failed to generate embedding for the question."}

            context = self.retrieve_context(query_embedding)

            if not context and is_follow_up(question) and history:

                recent_history = history.split("\n")[-4:]
                enhanced_query = " ".join(recent_history) + " " + question

                enhanced_embedding = genai.embed_content(
                    model=self.embedding_model,
                    content=enhanced_query,
                    task_type="RETRIEVAL_QUERY",
                    reequest_options={"timeout": 10}
                )["embedding"]

                context = self.retrieve_context(enhanced_embedding)

            if not context:
                return "I currently do not have sufficient information to answer that."

            context_str = "\n\n".join(context)

            return self.llm_service.generate_response(question, history, context_str)

        except (DeadlineExceeded, OperationalError) as e:
            print(f"Error during RAG processing: {e}")
            return {"error": True,"message": "Service temporarily unavailable. Please try again later."}

    def get_response_stream(self,question: str, history: str) -> str:
        """Attempt to stream"""
        try:
            query_embedding_result = genai.embed_content(
                model=self.embedding_model,
                content=question,
                task_type="RETRIEVAL_QUERY",
                request_options={"timeout": 10}
            )

            query_embedding = query_embedding_result["embedding"]
            if not query_embedding:
                yield "Failed to generate embedding for the question."
                return

            context = self.retrieve_context(query_embedding)

            if not context and is_follow_up(question) and history:
                recent_history = history.split("\n")[-4:]
                enhanced_query = " ".join(recent_history) + " " + question

                enhanced_embedding = genai.embed_content(
                    model=self.embedding_model,
                    content=enhanced_query,
                    task_type="RETRIEVAL_QUERY",
                    request_options={"timeout": 10}
                )["embedding"]

                context = self.retrieve_context(enhanced_embedding)

            if not context:
                yield "I currently do not have sufficient information to answer that."
                return

            context_str = "\n\n".join(context)

            yield from self.llm_service.stream_response(question, history, context_str)

        except (DeadlineExceeded, OperationalError) as e:
            print(f"Error during RAG streaming: {e}")
            yield "Service temporarily unavailable. Please try again later."

