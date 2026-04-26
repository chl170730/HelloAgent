import re
from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search
from datetime import datetime
current_time = datetime.now().strftime("%Y%m%d-%H%M%S")

# REACT prompt template (translated to English)
REACT_PROMPT_TEMPLATE = """
Please note: you are an intelligent assistant capable of calling external tools. You are not allowed to generate Thought and Action more than 1 time per step. You should obey the current time.

Available tools:
{tools}

Please strictly follow the format below:

Thought: briefly explain the next step.
Action: the action you decide to take; it must be one of the following formats:
- `{{tool_name}}[{{tool_input}}]`: call an available tool.
- `Finish[final answer]`: when you believe you have the final answer, directly output the final answer without any redundant explanation and characters.

Important rules for Action:
- If you call `Search`, the content inside `Search[...]` must be a plain text search query only.
- For `Search[...]`, do NOT output JSON, dictionaries, key-value pairs, labels such as `query=`, or quoted whole-query strings.
- Correct example: `Search[Apple latest phone model 2026]`
- Incorrect examples:
  - `Search[{{"query": "Apple latest phone model 2026", "top_n": 10}}]`
  - `Search[query=Apple latest phone model 2026]`
  - `Search["Apple latest phone model 2026"]`
- When you have collected enough information to answer the user's final question, you must use `Finish[final answer]` in the `Action:` field to output the final answer.

Additional information:
Current step: {current_step}
Current_time: {current_time}

Now, begin solving the following problem:
Question: {question}
History: {history}

"""


class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- Step {current_step} ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(tools=tools_desc, question=question, history=history_str, current_step=current_step, current_time=current_time)

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("Error: LLM did not return a valid response.")
                break

            thought, action = self._parse_output(response_text)
            if thought:
                print(f"🤔 Thought: {thought}")
            if not action:
                print("Warning: failed to parse a valid Action; stopping.")
                break

            if action.startswith("Finish"):
                # If it's a Finish instruction, extract the final answer and stop
                final_answer = self._parse_action_input(action)
                print(f"🎉 Final answer: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                self.history.append("Observation: Invalid Action format, please check.")
                continue

            if not self._is_valid_tool_input(tool_name, tool_input):
                print("Warning: invalid tool input rejected.")
                self.history.append(
                    "Observation: Invalid tool input format. For Search, use plain text query only. "
                    "Do not use JSON, query=, or quoted whole-query strings."
                )
                continue


            print(f"🎬 Action: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = tool_function(tool_input) if tool_function else f"Error: Tool named '{tool_name}' not found."

            print(f"👀 Observation: {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("Reached maximum steps; stopping the process.")
        return None

    def _parse_output(self, text: str):
        # Thought: match until Action: or end of text
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: match until end of text
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        match = re.match(r"\w+\[(.*)]", action_text, re.DOTALL)
        return match.group(1) if match else ""

    def _is_valid_tool_input(self, tool_name: str, tool_input: str) -> bool:
        if not tool_name or not tool_input:
            return False

        if tool_name == "Search":
            stripped = tool_input.strip()
            if not stripped:
                return False

            forbidden_substrings = [
                '{', '}', '"query"', "'query'", 'query=',
                'top_n', 'recency_days', 'source=', 'source:'
            ]
            lowered = stripped.lower()
            if any(token.lower() in lowered for token in forbidden_substrings):
                return False

            if stripped.startswith('"') and stripped.endswith('"'):
                return False
            if stripped.startswith("'") and stripped.endswith("'"):
                return False

        return True


if __name__ == '__main__':
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "A web search engine. Use this tool when you need to answer questions about current events, facts, or information that is not present in your knowledge base."
    tool_executor.registerTool("Search", search_desc, search)
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "What is APPLE's latest phone model? What are its main selling points?"
    agent.run(question)