from typing import List, Dict, Any
# Assume llm_client.py exists and provides HelloAgentsLLM
from llm_client import HelloAgentsLLM


# --- Module 1: Memory ---

class Memory:
    """
    A simple short-term memory module for storing execution and reflection trajectories.
    """

    def __init__(self):
        # Initialize an empty list to store all records
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        Add a new record into memory.

        Args:
        - record_type (str): 'execution' or 'reflection'.
        - content (str): The specific content of the record (e.g., generated code or reflection feedback).
        """
        self.records.append({"type": record_type, "content": content})
        print(f"📝 Memory updated: added a '{record_type}' record.")

    def get_trajectory(self) -> str:
        """
        Format all memory records into a coherent string for prompt building.
        """
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- Previous attempt (code) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- Reviewer feedback ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """
        Get the most recent execution result (e.g., the latest generated code).
        """
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None


# --- Module 2: Reflection Agent ---

# 1. Initial Execution Prompt
INITIAL_PROMPT_TEMPLATE = """
You are a senior Python programmer. Write a Python function according to the requirement below.
Your code must include a full function signature, docstring, and follow PEP 8.

Requirement: {task}

Output code only, with no extra explanation.
"""

# 2. Reflection Prompt
REFLECT_PROMPT_TEMPLATE = """
You are an extremely strict code reviewer and senior algorithm engineer, with the highest standards for code performance.
Your task is to review the following Python code, focusing on identifying the main bottlenecks in **algorithm efficiency**.

# Original Task:
{task}

# Code to Review:
```python
{code}
```

Analyze the time complexity of this code, and consider if there exists a **algorithmically superior** solution that could significantly enhance performance.
If such a solution exists, clearly point out the current algorithm's shortcomings and propose specific, feasible algorithmic improvements (e.g., using the sieve method instead of trial division).
Only respond with "No improvement needed" if the code is already optimal at the algorithm level.

Provide your feedback directly, without any additional explanation.
"""

# 3. Optimization Prompt
REFINE_PROMPT_TEMPLATE = """
You are a senior Python programmer. You are optimizing your code based on feedback from a code reviewer.

# Original Task:
{task}

# Your Last Code Attempt:
{last_code_attempt}

# Reviewer's Feedback:
{feedback}

Based on the reviewer's feedback, generate an optimized new version of the code.
Your code must include a full function signature, docstring, and follow PEP 8.
Output the optimized code only, with no extra explanation.
"""


class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task: str):
        print(f"\n--- Starting Task ---\nTask: {task}")

        # --- 1. Initial Execution ---
        print("\n--- Performing Initial Attempt ---")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # --- 2. Iterative Loop: Reflection and Optimization ---
        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i + 1}/{self.max_iterations} ---")

            # a. Reflection
            print("\n-> Reflecting...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # b. Check if we should stop
            if "No improvement needed" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ Reflection indicates no further improvement is needed. Task complete.")
                break

            # c. Optimization
            print("\n-> Optimizing...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)

        final_code = self.memory.get_last_execution()
        print(f"\n--- Task Complete ---\nFinal Generated Code:\n{final_code}")
        return final_code

    def _get_llm_response(self, prompt: str) -> str:
        """A helper method to call the LLM and get the complete streaming response."""
        messages = [{"role": "user", "content": prompt}]
        # Ensure it can handle the case where the generator might return None
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text


if __name__ == '__main__':
    # 1. Initialize LLM Client (Ensure your .env and llm_client.py are correctly configured)
    try:
        llm_client = HelloAgentsLLM()
    except Exception as e:
        print(f"Error initializing LLM client: {e}")
        exit()

    # 2. Initialize Reflection Agent, set to a maximum of 2 iterations
    agent = ReflectionAgent(llm_client, max_iterations=2)

    # 3. Define task and run agent
    task = "Write a Python function to find all prime numbers between 1 and n."
    agent.run(task)
