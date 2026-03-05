import os
import logging
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from ..models import KnowledgeBase
from pgvector.django import L2Distance
from .llm_service import LLMService
from google.api_core.exceptions import DeadlineExceeded
from django.db import OperationalError


logger = logging.getLogger("chat")



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
        logger.info("Initializing RAG service")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=60,
            length_function=len
        )
        self.embedding_model = "models/gemini-embedding-001"
        self.llm_service = LLMService()
        logger.info("RAG service initialized successfully")

    def ingest_text(self, text: str, metadata: dict = None):
        start_time = time.time()
        logger.info(f"Starting text ingestion - Text length: {len(text)}")
        
        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Text split into {len(chunks)} chunks")

            embeddings_result = genai.embed_content(
                model=self.embedding_model,
                content=chunks,
                task_type="RETRIEVAL_DOCUMENT"
            )

            embeddings = embeddings_result["embedding"]
            logger.info(f"Generated {len(embeddings)} embeddings")

            knowledge_objects = [
                KnowledgeBase(
                    content=content,
                    embedding=embedding,
                    metadata=metadata
                )
                for content, embedding in zip(chunks, embeddings)
            ]

            KnowledgeBase.objects.bulk_create(knowledge_objects)
            elapsed = time.time() - start_time
            logger.info(f"Text ingestion completed - {len(knowledge_objects)} objects created in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Text ingestion failed: {str(e)} - Time: {elapsed:.2f}s")
            raise

    def retrieve_context(self, embedding, top_k=3):
        start_time = time.time()
        logger.info(f"Retrieving context - top_k: {top_k}")
        
        try:
            docs = KnowledgeBase.objects.order_by(
                L2Distance("embedding", embedding)
            )[:top_k]
            
            result = [doc.content for doc in docs]
            elapsed = time.time() - start_time
            logger.info(f"Context retrieved - {len(result)} documents found in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Context retrieval failed: {str(e)} - Time: {elapsed:.2f}s")
            return []

    def get_response(self, question: str, history: str) -> str:
        start_time = time.time()
        logger.info(f"Getting response - Question length: {len(question)}, History length: {len(history)}")
        
        try:
            logger.info("Generating query embedding")
            query_embedding_result = genai.embed_content(
                model=self.embedding_model,
                content=question,
                task_type="RETRIEVAL_QUERY",
                request_options={"timeout": 10}
            )

            query_embedding = query_embedding_result["embedding"]
            if not query_embedding:
                logger.error("Failed to generate embedding for question")
                return {"error": True,"message": "Failed to generate embedding for the question."}
            
            logger.info("Query embedding generated successfully")
            context = self.retrieve_context(query_embedding)

            if not context and is_follow_up(question) and history:
                logger.info("No context found, attempting follow-up enhancement")
                recent_history = history.split("\n")[-4:]
                enhanced_query = " ".join(recent_history) + " " + question
                logger.info(f"Enhanced query created - length: {len(enhanced_query)}")

                enhanced_embedding = genai.embed_content(
                    model=self.embedding_model,
                    content=enhanced_query,
                    task_type="RETRIEVAL_QUERY",
                    request_options={"timeout": 10}
                )["embedding"]

                context = self.retrieve_context(enhanced_embedding)
                logger.info(f"Follow-up context retrieved - {len(context)} items")

            if not context:
                elapsed = time.time() - start_time
                logger.warning(f"No context found for question - Time: {elapsed:.2f}s")
                return "I currently do not have sufficient information to answer that."

            context_str = "\n\n".join(context)
            logger.info(f"Generating LLM response with {len(context)} context items")

            response = self.llm_service.generate_response(question, history, context_str)
            elapsed = time.time() - start_time
            logger.info(f"Response generated successfully - Total time: {elapsed:.2f}s")
            return response

        except DeadlineExceeded as e:
            elapsed = time.time() - start_time
            logger.error(f"Deadline exceeded during RAG processing: {str(e)} - Time: {elapsed:.2f}s")
            return {"error": True,"message": "Service temporarily unavailable. Please try again later."}
        except OperationalError as e:
            elapsed = time.time() - start_time
            logger.error(f"Database error during RAG processing: {str(e)} - Time: {elapsed:.2f}s")
            return {"error": True,"message": "Service temporarily unavailable. Please try again later."}
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Unexpected error during RAG processing: {str(e)} - Time: {elapsed:.2f}s")
            return {"error": True,"message": "Service temporarily unavailable. Please try again later."}

    def get_response_stream(self,question: str, history: str) -> str:
        """Attempt to stream"""
        start_time = time.time()
        logger.info(f"Starting stream response - Question length: {len(question)}, History length: {len(history)}")
        
        try:
            logger.info("Generating query embedding for stream")
            query_embedding_result = genai.embed_content(
                model=self.embedding_model,
                content=question,
                task_type="RETRIEVAL_QUERY",
                request_options={"timeout": 10}
            )

            query_embedding = query_embedding_result["embedding"]
            if not query_embedding:
                elapsed = time.time() - start_time
                logger.error(f"Failed to generate embedding for stream - Time: {elapsed:.2f}s")
                yield "\n\nI'm having trouble understanding your question right now. Please try rephrasing it."
                return
            
            logger.info("Query embedding generated for stream")
            context = self.retrieve_context(query_embedding)

            if not context and is_follow_up(question) and history:
                logger.info("No context for stream, attempting follow-up enhancement")
                recent_history = history.split("\n")[-4:]
                enhanced_query = " ".join(recent_history) + " " + question
                logger.info(f"Enhanced query for stream - length: {len(enhanced_query)}")

                enhanced_embedding = genai.embed_content(
                    model=self.embedding_model,
                    content=enhanced_query,
                    task_type="RETRIEVAL_QUERY",
                    request_options={"timeout": 10}
                )["embedding"]

                context = self.retrieve_context(enhanced_embedding)
                logger.info(f"Follow-up context for stream - {len(context)} items")

            if not context:
                elapsed = time.time() - start_time
                logger.warning(f"No context found for stream - Time: {elapsed:.2f}s")
                yield "\n\nI don't have enough information to answer that question. Try asking about Python or Django topics I've been trained on."
                return

            context_str = "\n\n".join(context)
            logger.info(f"Starting LLM stream with {len(context)} context items")

            chunk_count = 0
            for chunk in self.llm_service.stream_response(question, history, context_str):
                chunk_count += 1
                yield chunk
            
            elapsed = time.time() - start_time
            logger.info(f"Stream completed - {chunk_count} chunks sent in {elapsed:.2f}s")

        except DeadlineExceeded as e:
            elapsed = time.time() - start_time
            logger.error(f"Deadline exceeded during stream: {str(e)} - Time: {elapsed:.2f}s")
            yield "\n\nThe request is taking longer than expected. Please try again."
        except OperationalError as e:
            elapsed = time.time() - start_time
            logger.error(f"Database error during stream: {str(e)} - Time: {elapsed:.2f}s")
            yield "\n\nI'm experiencing database connectivity issues. Please try again in a moment."
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Unexpected error during stream: {str(e)} - Time: {elapsed:.2f}s")
            yield "\n\nSomething unexpected happened. Please try asking your question again."

