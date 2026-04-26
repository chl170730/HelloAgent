from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

import os
from serpapi import SerpApiClient
from typing import Dict, Any, Optional, Callable


def search(query: str) -> str:
    """
    A practical web search tool based on SerpApi.
    It parses search results intelligently and prefers direct answers or knowledge-graph information.
    """
    print(f"🔍 Executing [SerpApi] web search: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Error: SERPAPI_API_KEY is not configured in the .env file."

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # country code
            "hl": "zh-cn",  # language code
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # Debug helpers (commented out):
        # import json
        # print("Top-level keys in results:", list(results.keys()))
        # print(json.dumps(results, ensure_ascii=False, indent=2))

        # Intelligent parsing: prefer the most direct answer
        if "error" in results:
            return f"SerpApi error: {results['error']}"
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # If there's no direct answer, return summaries of the top three organic results
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"Sorry, no information found for '{query}'."

    except Exception as e:
        return f"Error occurred during search: {e}"


class ToolExecutor:
    """
    A tool executor that manages and runs tools.
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: Callable[..., Any]):
        """
        Register a new tool in the toolbox.
        """
        if name in self.tools:
            print(f"Warning: tool '{name}' already exists and will be overwritten.")

        self.tools[name] = {"description": description, "func": func}
        print(f"Tool '{name}' registered.")

    def getTool(self, name: str) -> Optional[Callable[..., Any]]:
        """
        Get the execution function for a tool by name.
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        Get a formatted description string for all available tools.
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


# --- Tool initialization and usage example ---
if __name__ == '__main__':
    # 1. Initialize tool executor
    toolExecutor = ToolExecutor()

    # 2. Register our practical search tool
    search_description = "A web search engine. Use this tool when you need to answer questions about current events, facts, or information not present in your knowledge base."
    toolExecutor.registerTool("Search", search_description, search)

    # 3. Print available tools
    print("\n--- Available tools ---")
    print(toolExecutor.getAvailableTools())

    # 4. Example of an agent Action calling the tool for a real-time question
    print("\n--- Execute Action: Search['What is NVIDIA's latest GPU model?'] ---")
    tool_name = "Search"
    tool_input = "What is NVIDIA's latest GPU model?"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- Observation ---")
        print(observation)
    else:
        print(f"Error: Tool named '{tool_name}' not found.")
