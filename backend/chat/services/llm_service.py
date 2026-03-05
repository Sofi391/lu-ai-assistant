import google.generativeai as genai
from pathlib import Path
from google.api_core.exceptions import DeadlineExceeded,ServiceUnavailable


BASE_DIR = Path(__file__).resolve().parent.parent


def load_prompt(file_path: str) -> str:
    """Load prompt from file."""
    path = BASE_DIR / "prompts" / file_path
    return path.read_text(encoding='utf-8')


class LLMService:
    def __init__(self):
        self.llm_model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def generate_response(self, question: str, history: str, context_str: str) -> str:
        """Generate response using LLM with context and history."""
        try:
            system_prompt = load_prompt("system_prompt.txt")
            rag_prompt = load_prompt("rag_prompt.txt")

            final_prompt = rag_prompt.format(
                system_prompt=system_prompt,
                history=history,
                context=context_str,
                question=question
            )

            response = self.llm_model.generate_content(
                final_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=1024,
                    temperature=0.1
                ),
                request_options={"timeout": 20}
            )
            if not response.text or not response.text.strip():
                return {
                    "error": True,
                    "code": "EMPTY_RESPONSE",
                    "message": "AI returned no text."
                    }

            return response.text.strip()
        except DeadlineExceeded:
            return {
                "error": True,
                "code": "TIMEOUT",
                "message": "Request timed out. Please try again."
            }
        except ServiceUnavailable:
            return {
                "error": True,
                "code": "SERVICE_UNAVAILABLE",
                "message": "AI service is currently unavailable. Please try again later."
            }
        except Exception as e:
            return {
                "error": True,
                "code": "UNKNOWN_ERROR",
                "message": f"An unexpected error occurred: {str(e)}"
            }

    def stream_response(self, question: str, history: str, context_str: str):
        """Stream response using LLM with context and history."""
        try:
            system_prompt = load_prompt("system_prompt.txt")
            rag_prompt = load_prompt("rag_prompt.txt")

            final_prompt = rag_prompt.format(
                system_prompt=system_prompt,
                history=history,
                context=context_str,
                question=question
            )

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
                yield "\n\nAI service temporarily unavailable. Please try again."
                return

            for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except DeadlineExceeded:
            yield "\n\nAI service temporarily unavailable. Please try again."
        except ServiceUnavailable:
            yield "\n\nAI service temporarily unavailable. Please try again."
        except Exception as e:
            yield "\n\nAI service temporarily unavailable. Please try again."



