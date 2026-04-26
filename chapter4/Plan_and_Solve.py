import os
import ast
from llm_client import HelloAgentsLLM
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables from the .env file, handle file-not-found gracefully
try:
    load_dotenv()
except FileNotFoundError:
    print("Warning: .env file not found; falling back to system environment variables.")
except Exception as e:
    print(f"Warning: error loading .env file: {e}")

# --- 1. LLM client definition ---
# Assume you already have llm_client.py that defines HelloAgentsLLM

# --- 2. Planner definition ---
PLANNER_PROMPT_TEMPLATE = """
You are a top-tier AI planning expert. Your task is to decompose a complex user problem into an action plan made up of multiple simple steps.
Ensure each step in the plan is an independent, executable subtask and strictly ordered logically.
Your output must be a Python list where each element is a string describing a subtask.
Return only one Python fenced code block containing a valid Python list of strings, and do not output any thinking, explanation, prose, or text before or after the code block.

Question: {question}

Please output your plan strictly in the following format, including the ```python fences:
```python
["step 1", "step 2", "step 3", ...]
```
"""


class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        print("--- Generating plan ---")
        response_text = self.llm_client.think(messages=messages) or ""
        print(f"✅ Plan generated:\n{response_text}")

        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            print(f"✅ Plan parsed successfully: {plan}")
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ Error parsing plan: {e}")
            print(f"Original response: {response_text}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error parsing plan: {e}")
            return []


# --- 3. Executor definition ---
EXECUTOR_PROMPT_TEMPLATE = """
You are a top-tier AI executor. Your task is to follow the provided plan precisely and solve the problem step by step.
You will receive the original question, the full plan, and the steps/results completed so far.
Focus on solving the "current step" and output only the final answer for that step; do not output any additional explanations or dialogue.
Once you think you have the answer for the current step, output it directly without any commentary.

# Original question:
{question}

# Full plan:
{plan}

# History of steps and results:
{history}

# Current step:
{current_step}

Please output only the answer for the "current step":
"""


class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        final_answer = ""

        print("\n--- Executing plan ---")
        for i, step in enumerate(plan, 1):
            print(f"\n-> Executing step {i}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history if history else "None", current_step=step
            )
            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(messages=messages) or ""

            history += f"Step {i}: {step}\nResult: {response_text}\n\n"
            final_answer = response_text
            print(f"✅ Step {i} completed, result: {final_answer}")

        return final_answer


# --- 4. Agent composition ---
class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        print(f"\n--- Starting to process the question ---\nQuestion: {question}")
        plan = self.planner.plan(question)
        if not plan:
            print("\n--- Task aborted --- \nFailed to generate a valid action plan.")
            return
        final_answer = self.executor.execute(question, plan)
        print(f"\n--- Task completed ---\nFinal answer: {final_answer}")


# --- 5. Main entry point ---
if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "A fruit store sold 15 apples on Monday. The number sold on Tuesday was twice Monday's amount. On Wednesday they sold 5 fewer apples than on Tuesday. How many apples were sold in total over the three days?"
        agent.run(question)
    except ValueError as e:
        print(e)