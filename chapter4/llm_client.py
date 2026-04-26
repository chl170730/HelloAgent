import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any, cast
import json

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
                stream=True  # Enable streaming responses
            )

            print("✅ LLM responded successfully:")
            # for chunk in response:
            #     print("JSON start:\n",json.dumps(chunk.model_dump(), indent=2))
            #     print("JSON end\n")
            collected_content = []

            # check whether the chunk has the "choices" attribute and that it's not empty
            for chunk in response:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
            # check whether the first choice has the "delta" attribute
                delta = getattr(chunk.choices[0], "delta", None)
                if delta is None:
                    continue
            # check whether the delta has the "content" attribute and that it's not empty and not None and make sure to convert it to a string
                content = str(getattr(delta, "content", "") or "")
                if not content:
                    continue

            # directly print the content to the console without adding a new line, and flush the output buffer immediately to ensure real-time display
                print(content, end="", flush=True)
                collected_content.append(content)

            print()
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