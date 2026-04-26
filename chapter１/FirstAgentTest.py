AGENT_SYSTEM_PROMPT = """
You are an intelligent travel assistant. Your task is to analyze the user's request and solve it step by step using available tools.

# Available tools:
- `get_weather(city: str)`: Get real-time weather for a city.
- `get_attraction(city: str, weather: str)`: Recommend attractions based on city and weather.

# Output format requirements:
Each response must strictly contain one Thought and one Action:

Thought: [your reasoning and next-step plan]
Action: [the concrete action to execute]

Action must be one of:
1. Tool call: function_name(arg_name="arg_value")
2. Finish task: Finish[final answer]

# Important:
- Output only one Thought-Action pair each turn
- Action must stay on the same line
- When enough information is collected, end with Action: Finish[final answer]

Let's begin!
"""

import requests
import os
from tavily import TavilyClient


def get_weather(city: str) -> str:
    """
    Query real weather information via wttr.in API.
    """
    # API endpoint, request JSON format
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # Perform HTTP request
        response = requests.get(url, timeout=10)
        # Raise for non-200 status
        response.raise_for_status()
        # Parse returned JSON
        data = response.json()

        # Extract current condition
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition.get('temp_C', '')

        # Format a human-friendly string
        return f"{city} current weather: {weather_desc}, temperature {temp_c}°C"

    except requests.exceptions.RequestException as e:
        # Network-related error
        return f"Error: network issue when fetching weather - {e}"
    except (KeyError, IndexError) as e:
        # Data parsing error
        return f"Error: failed to parse weather data, city may be invalid - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    Use Tavily Search API to search for and return optimized attraction recommendations based on city and weather.
    """

    # Obtain API key from environment variables
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not configured in environment."

    # Initialize Tavily client
    tavily = TavilyClient(api_key=api_key)

    # Build a precise query
    query = f"Recommended attractions in '{city}' given weather '{weather}', with reasons"

    try:
        # Call API; include_answer=True requests a synthesized answer when available
        response = tavily.search(query=query, search_depth="basic", include_answer=True)

        # If Tavily provides a summary answer, use it
        if response.get("answer"):
            return response["answer"]

        # Otherwise format individual results
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result.get('title','')}: {result.get('content','')}")

        if not formatted_results:
            return "Sorry, no attraction recommendations were found."

        return "Based on search, found the following information:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"Error: an issue occurred while executing Tavily search - {e}"


# Collect available tools for easy lookup
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


from openai import OpenAI


class OpenAICompatibleClient:
    """
    A simple wrapper for calling any OpenAI-compatible LLM service.
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """Call the LLM API to generate a response."""
        print("Calling LLM service...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("LLM responded successfully.")
            return answer
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return "Error: failed to call language model service."


import re

# --- 1. Configure LLM client ---
# Use environment variables instead of hardcoding credentials
API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
MODEL_ID = os.environ.get("LLM_MODEL_ID", "gpt-4o-mini")

if not API_KEY:
    print("Warning: no LLM API key found in environment; LLM calls will fail until configured.")

llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)

# --- 2. Initialize ---
user_prompt = "Hello, please help me check today's weather in Tokyo and recommend a suitable attraction based on the weather."
prompt_history = [f"User request: {user_prompt}"]

print(f"User input: {user_prompt}\n" + "=" * 40)

# --- 3. Run main loop ---
for i in range(5):  # max loop count
    print(f"--- Iteration {i + 1} ---\n")

    # 3.1. Build prompt
    full_prompt = "\n".join(prompt_history)

    # 3.2. Call the LLM to think
    llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
    # The model may output extra Thought-Action pairs; truncate to the first pair
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output = truncated
            print("Truncated extra Thought-Action pairs.")
    print(f"Model output:\n{llm_output}\n")
    prompt_history.append(llm_output)

    # 3.3. Parse and execute the action
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        observation = "Error: failed to parse Action field. Ensure the reply strictly follows 'Thought: ... Action: ...' format."
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)
        continue
    action_str = action_match.group(1).strip()

    if action_str.startswith("Finish"):
        final_match = re.match(r"Finish\[(.*)\]", action_str)
        final_answer = final_match.group(1) if final_match else ""
        print(f"Task complete, final answer: {final_answer}")
        break

    tool_name_search = re.search(r"(\w+)\(", action_str)
    args_search = re.search(r"\((.*)\)", action_str)
    if not tool_name_search or not args_search:
        observation = "Error: invalid Action format or missing arguments."
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)
        continue

    tool_name = tool_name_search.group(1)
    args_str = args_search.group(1)
    kwargs = dict(re.findall(r'(\w+)="([^\"]*)"', args_str))

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"Error: undefined tool '{tool_name}'"

    # 3.4. Record observation
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "=" * 40)
    prompt_history.append(observation_str)

