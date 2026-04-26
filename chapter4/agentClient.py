import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any, cast

# Load environment variables from the .env file
load_dotenv()


class HelloAgentsLLM:
    """
    An LLM client customized for the book "Hello Agents".
    It calls any service compatible with the OpenAI interface and uses streaming responses by default.
    """

    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        Initialize the client. Prefer parameters passed in; otherwise load from environment variables.
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))

        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("Model ID, API key, and base URL must be provided or defined in the .env file.")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> Optional[str]:
        """
        Call the large language model and return its response.
        """
        print(f"🧠 Calling model {self.model}...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=cast(Any, messages),
                temperature=temperature,
                stream=True,
            )

            # Handle the streaming response
            print("✅ LLM responded successfully:")
            collected_content = []
            for chunk in response:
                content = str(getattr(chunk.choices[0].delta, "content", "") or "")
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # newline after streaming output
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ Error calling LLM API: {e}")
            return None


# --- Client usage example ---
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()

        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "Write a quicksort algorithm"}
        ]

        print("--- Calling LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- Full model response ---")
            print(responseText)

    except ValueError as e:
        print(e)

# Example output (for illustration):
#
# --- Calling LLM ---
# 🧠 Calling model xxxxxx...
# ✅ LLM responded successfully:
# Quicksort is a very efficient sorting algorithm...
#
