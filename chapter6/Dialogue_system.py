"""
Intelligent Search Assistant - Real search system based on LangGraph + Tavily API
1. Understand user intent
2. Use Tavily API to perform real web search
3. Generate answers based on search results
"""
from pathlib import Path
import asyncio
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()


# Define state schema
class SearchState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str  # User query
    search_query: str  # Optimized search query
    search_results: str  # Tavily search results
    final_answer: str  # Final answer
    step: str  # Current step


# Initialize model and Tavily client
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID", "gpt-4o-mini"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    temperature=0.7
)
# Tavily API key should be configured in the .env file as TAVILY_API_KEY=...
# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))



def _ensure_str(content) -> str:
    """Convert various response content types to a string safely."""
    if isinstance(content, str):
        return content
    try:
        return str(content)
    except Exception:
        return ""


def understand_query_node(state: SearchState) -> SearchState:
    """Step 1: Understand user query and generate search keywords"""

    # Get the latest human message from the state
    user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break

    understand_prompt = f"""Analyze the user's query: "{user_message}"\n\n
Please complete two tasks:
1. Briefly summarize what the user wants to know
2. Generate the best search keywords (English preferred, concise and precise)\n\n
Format:
Understanding: [summary of user intent]
Search terms: [best search keywords]"""

    if not user_message.strip():
        raise ValueError("Could not read user query from state['messages']. Please ensure initial_state['messages'] contains a HumanMessage.")

    response = llm.invoke([
        SystemMessage(content="You are a search query rewriting assistant. Understand the user question and generate search-engine-friendly keywords."),
        HumanMessage(content=understand_prompt)
    ])

    # Extract search keywords safely
    response_text = _ensure_str(response.content)
    search_query = user_message  # Default to the original query

    if "Search terms:" in response_text:
        search_query = response_text.split("Search terms:", 1)[1].strip()
    elif "Search keywords:" in response_text:
        search_query = response_text.split("Search keywords:", 1)[1].strip()

    return {
        "user_query": user_message,
        "search_query": search_query,
        "step": "understood",
        "messages": [AIMessage(content=f"I understand your request: {_ensure_str(response.content)}")]
    }


def tavily_search_node(state: SearchState) -> SearchState:
    """Step 2: Use Tavily API for real search"""

    search_query = state.get("search_query", "")

    try:
        print(f"🔍 Searching: {search_query}")

        # Call Tavily search API
        response = tavily_client.search(
            query=search_query,
            search_depth="basic",
            include_answer=True,
            include_raw_content=False,
            max_results=5
        )

        # Process search results
        search_results = ""

        # Prefer Tavily's summary answer first
        if response.get("answer"):
            search_results = f"Summary answer:\n{response['answer']}\n\n"

        # Add individual results
        if response.get("results"):
            search_results += "Related information:\n"
            for i, result in enumerate(response["results"][:3], 1):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                search_results += f"{i}. {title}\n{content}\nSource: {url}\n\n"

        if not search_results:
            search_results = "Sorry, no relevant information was found."

        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [AIMessage(content="✅ Search completed! I found relevant information and am organizing the answer...")]
        }

    except Exception as e:
        error_msg = f"An error occurred during search: {str(e)}"
        print(f"❌ {error_msg}")

        return {
            "search_results": f"Search failed: {error_msg}",
            "step": "search_failed",
            "messages": [AIMessage(content="❌ Search encountered a problem. I will answer based on existing knowledge.")]
        }


def generate_answer_node(state: SearchState) -> SearchState:
    """Step 3: Generate final answer based on search results"""

    # If search failed, answer based on the LLM's internal knowledge
    if state.get("step") == "search_failed":
        fallback_prompt = f"""The search API is temporarily unavailable. Please answer based on your existing knowledge:\n\nUser question: {state.get('user_query', '')}\n\nPlease provide a helpful answer and clearly state that it is based on existing knowledge."""

        response = llm.invoke([
            SystemMessage(content="You are a QA assistant. If the search API is unavailable, do not provide claims that exceed timeliness or verifiability."),
            HumanMessage(content=fallback_prompt)
        ])

        return {
            "final_answer": _ensure_str(response.content),
            "step": "completed",
            "messages": [AIMessage(content=_ensure_str(response.content))]
        }

    # Otherwise synthesize an answer from search results
    answer_prompt = f"""Provide a complete and accurate answer based on the following search results:\n\nUser question: {state.get('user_query', '')}\n\nSearch results:\n{state.get('search_results', '')}\n\nRequirements:\n1. Synthesize the search results into an accurate and useful answer\n2. If it is a technical question, provide concrete solutions or code\n3. Cite sources for key information\n4. Keep the answer well-structured and easy to understand\n5. If results are incomplete, explain that and provide follow-up suggestions"""

    response = llm.invoke([
        SystemMessage(content="You are a rigorous search-result summarization assistant. You must answer based on the user's question and search results."),
        HumanMessage(content=answer_prompt)
    ])

    return {
        "final_answer": _ensure_str(response.content),
        "step": "completed",
        "messages": [AIMessage(content=_ensure_str(response.content))]
    }


# Build search workflow
def create_search_assistant():
    workflow = StateGraph(SearchState)

    # Add three nodes
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    # Linear flow
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    # Compile graph
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)
    current_dir = Path(__file__).resolve().parent
    png_path = current_dir / "langgraph_workflow.png"
    try:
        png_data = app.get_graph().draw_mermaid_png()
        png_path.write_bytes(png_data)
        print(f"PNG image saved to: {png_path}")
    except Exception as e:
        print(f"PNG generation failed: {e}")
        print("You can still open langgraph_workflow.mmd and paste the content into Mermaid Live Editor to view the graph.")

    return app


async def main():
    """Main function: run the intelligent search assistant"""

    # Check API key
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ Error: Please configure TAVILY_API_KEY in the .env file")
        return

    app = create_search_assistant()

    print("🔍 Intelligent Search Assistant started!")
    print("I will use Tavily API to find up-to-date and accurate information")
    print("Supports all kinds of questions: news, technology, knowledge QA, etc.")
    print("(Type 'quit' to exit)\n")

    session_count = 0

    while True:
        user_input = input("🤔 What would you like to know: ").strip()

        if user_input.lower() in ['quit', 'q', 'exit']:
            print("Thanks for using this assistant. Goodbye! 👋")
            break

        if not user_input:
            continue

        session_count += 1
        config = {"configurable": {"thread_id": f"search-session-{session_count}"}}

        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": "",
            "search_query": "",
            "search_results": "",
            "final_answer": "",
            "step": "start"
        }

        try:
            print("\n" + "=" * 60)

            # Execute workflow
            async for output in app.astream(initial_state, config=config):
                for node_name, node_output in output.items():
                    if "messages" in node_output and node_output["messages"]:
                        latest_message = node_output["messages"][-1]
                        if isinstance(latest_message, AIMessage):
                            if node_name == "understand":
                                print(f"🧠 Understanding stage: {latest_message.content}")
                            elif node_name == "search":
                                print(f"🔍 Search stage: {latest_message.content}")
                            elif node_name == "answer":
                                print(f"\n💡 Final answer:\n{latest_message.content}")

            print("\n" + "=" * 60 + "\n")

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            print("Please try asking your question again.\n")


if __name__ == "__main__":
    asyncio.run(main())