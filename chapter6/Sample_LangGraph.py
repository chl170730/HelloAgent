from pathlib import Path
from typing import TypedDict, List

# 定义全局状态的数据结构
class AgentState(TypedDict):
    messages: List[str]      # 对话历史
    current_task: str        # 当前任务
    final_answer: str        # 最终答案
    # ... 任何其他需要追踪的状态


# 定义一个“规划者”节点函数
def planner_node(state: AgentState) -> AgentState:
    """根据当前任务制定计划，并更新状态。"""
    current_task = state["current_task"]
    # ... 调用LLM生成计划 ...
    plan = f"为任务 '{current_task}' 生成的计划..."

    # 将新消息追加到状态中
    state["messages"].append(plan)
    return state


# 定义一个“执行者”节点函数
def executor_node(state: AgentState) -> AgentState:
    """执行最新计划，并更新状态。"""
    latest_plan = state["messages"][-1]
    # ... 执行计划并获得结果 ...
    result = f"执行计划 '{latest_plan}' 的结果..."

    state["messages"].append(result)
    return state

def final_node(state: AgentState) -> AgentState:
    """整理最终答案，并更新状态。"""
    state["final_answer"] = state["messages"][-1]
    return state


def should_continue(state: AgentState) -> str:
    """条件函数：根据状态决定下一步路由。"""
    # 假设如果消息少于3条，则需要继续规划
    if len(state["messages"]) < 3:
        # 返回的字符串需要与添加条件边时定义的键匹配
        return "continue_to_planner"
    else:
        return "go_to_final"


from langgraph.graph import StateGraph, END

# 初始化一个状态图，并绑定我们定义的状态结构
workflow = StateGraph(AgentState)

# 将节点函数添加到图中
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("final", final_node)

# 设置图的入口点
workflow.set_entry_point("planner")

# 添加常规边，连接 planner 和 executor
workflow.add_edge("planner", "executor")

# 添加条件边，实现动态路由
workflow.add_conditional_edges(
    # 起始节点
    "executor",
    # 判断函数
    should_continue,
    # 路由映射：将判断函数的返回值映射到目标节点
    {
        "continue_to_planner": "planner",  # 如果返回"continue_to_planner"，则跳回planner节点
        "go_to_final": "final"              # 如果返回"go_to_final"，则进入最终整理节点
    }
)

# final 节点执行完后结束流程
workflow.add_edge("final", END)

# 编译图，生成可执行的应用
app = workflow.compile()

# 1. 输出 Mermaid 图代码：可以复制到 Mermaid Live Editor 或支持 Mermaid 的 Markdown 中查看
mermaid_code = app.get_graph().draw_mermaid()
print("\n===== Mermaid 图代码 =====")
print(mermaid_code)

# 2. 保存 Mermaid 源文件
current_dir = Path(__file__).resolve().parent
mermaid_path = current_dir / "langgraph_workflow.mmd"
mermaid_path.write_text(mermaid_code, encoding="utf-8")
print(f"\nMermaid 源文件已保存到: {mermaid_path}")

# 3. 保存 PNG 图片
# 注意：draw_mermaid_png() 默认可能访问 mermaid.ink；如果网络不稳定，这一步可能失败。
png_path = current_dir / "langgraph_workflow.png"
try:
    png_data = app.get_graph().draw_mermaid_png()
    png_path.write_bytes(png_data)
    print(f"PNG 图片已保存到: {png_path}")
except Exception as e:
    print(f"PNG 图片生成失败: {e}")
    print("你仍然可以打开 langgraph_workflow.mmd，复制其中内容到 Mermaid Live Editor 查看图。")

# 运行图
inputs = {
    "current_task": "分析最近的AI行业新闻",
    "messages": [],
    "final_answer": ""
}

print("\n===== LangGraph 执行过程 =====")
for event in app.stream(inputs):
    print(event)
