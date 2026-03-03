import google.generativeai as genai
from pathlib import Path


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
            )
        )

        return response.text.strip()

    def stream_response(self, question: str, history: str, context_str: str):
        """Stream response using LLM with context and history."""
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
            )
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

