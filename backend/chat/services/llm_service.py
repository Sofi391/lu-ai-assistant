import logging
import time
import google.generativeai as genai
from pathlib import Path
from google.api_core.exceptions import DeadlineExceeded,ServiceUnavailable


logger = logging.getLogger("chat")


BASE_DIR = Path(__file__).resolve().parent.parent


def load_prompt(file_path: str) -> str:
    """Load prompt from file."""
    try:
        logger.info(f"Loading prompt file: {file_path}")
        path = BASE_DIR / "prompts" / file_path
        content = path.read_text(encoding='utf-8')
        logger.info(f"Prompt file loaded successfully: {file_path} - Length: {len(content)}")
        return content
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt file {file_path}: {str(e)}")
        raise


class LLMService:
    def __init__(self):
        logger.info("Initializing LLM service")
        self.llm_model = genai.GenerativeModel("gemini-2.5-flash-lite")
        logger.info("LLM service initialized with model: gemini-2.5-flash-lite")

    def generate_response(self, question: str, history: str, context_str: str) -> str:
        """Generate response using LLM with context and history."""
        start_time = time.time()
        logger.info(f"Generating LLM response - Question length: {len(question)}, Context length: {len(context_str)}")
        
        try:
            system_prompt = load_prompt("system_prompt.txt")
            rag_prompt = load_prompt("rag_prompt.txt")

            final_prompt = rag_prompt.format(
                system_prompt=system_prompt,
                history=history,
                context=context_str,
                question=question
            )
            logger.info(f"Final prompt created - Length: {len(final_prompt)}")

            logger.info("Sending request to LLM API")
            response = self.llm_model.generate_content(
                final_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=1024,
                    temperature=0.1
                ),
                request_options={"timeout": 20}
            )
            
            if not response.text or not response.text.strip():
                elapsed = time.time() - start_time
                logger.warning(f"LLM returned empty response - Time: {elapsed:.2f}s")
                return {
                    "error": True,
                    "code": "EMPTY_RESPONSE",
                    "message": "AI returned no text."
                    }

            elapsed = time.time() - start_time
            logger.info(f"LLM response generated successfully - Response length: {len(response.text)}, Time: {elapsed:.2f}s")
            return response.text.strip()
            
        except DeadlineExceeded as e:
            elapsed = time.time() - start_time
            logger.error(f"LLM request timeout: {str(e)} - Time: {elapsed:.2f}s")
            return {
                "error": True,
                "code": "TIMEOUT",
                "message": "Request timed out. Please try again."
            }
        except ServiceUnavailable as e:
            elapsed = time.time() - start_time
            logger.error(f"LLM service unavailable: {str(e)} - Time: {elapsed:.2f}s")
            return {
                "error": True,
                "code": "SERVICE_UNAVAILABLE",
                "message": "AI service is currently unavailable. Please try again later."
            }
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Unexpected LLM error: {str(e)} - Time: {elapsed:.2f}s")
            return {
                "error": True,
                "code": "UNKNOWN_ERROR",
                "message": f"An unexpected error occurred: {str(e)}"
            }

    def stream_response(self, question: str, history: str, context_str: str):
        """Stream response using LLM with context and history."""
        start_time = time.time()
        logger.info(f"Starting LLM stream - Question length: {len(question)}, Context length: {len(context_str)}")
        
        try:
            system_prompt = load_prompt("system_prompt.txt")
            rag_prompt = load_prompt("rag_prompt.txt")

            final_prompt = rag_prompt.format(
                system_prompt=system_prompt,
                history=history,
                context=context_str,
                question=question
            )
            logger.info(f"Final prompt for stream created - Length: {len(final_prompt)}")

            logger.info("Sending stream request to LLM API")
            stream = self.llm_model.generate_content(
                final_prompt,
                stream=True,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=1024,
                    temperature=0.1
                ),
                request_options={"timeout": 20}
            )

            if not stream:
                elapsed = time.time() - start_time
                logger.error(f"LLM stream is None - Time: {elapsed:.2f}s")
                yield "\n\nI'm having trouble connecting to the AI service right now. Please try again in a moment."
                return

            chunk_count = 0
            total_chars = 0
            for chunk in stream:
                if chunk.text:
                    chunk_count += 1
                    total_chars += len(chunk.text)
                    yield chunk.text
            
            elapsed = time.time() - start_time
            logger.info(f"LLM stream completed - Chunks: {chunk_count}, Total chars: {total_chars}, Time: {elapsed:.2f}s")
            
        except DeadlineExceeded as e:
            elapsed = time.time() - start_time
            logger.error(f"LLM stream timeout: {str(e)} - Time: {elapsed:.2f}s")
            yield "\n\nThe request is taking longer than expected. Please try asking your question again."
        except ServiceUnavailable as e:
            elapsed = time.time() - start_time
            logger.error(f"LLM stream service unavailable: {str(e)} - Time: {elapsed:.2f}s")
            yield "\n\nI'm currently experiencing high demand. Please try again in a few moments."
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Unexpected LLM stream error: {str(e)} - Time: {elapsed:.2f}s")
            yield "\n\nSomething went wrong while processing your request. Please try again."



