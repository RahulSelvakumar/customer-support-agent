from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, SystemMessage
from src.core.config import get_llm
from tools import fetch_customer_profile, read_refund_policy, execute_refund, escalate_to_human

# 1. Define the System State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    logs: list[str]

# 2. Gather and bind tools to the Open-Source LLM
tools_list = [fetch_customer_profile, read_refund_policy, execute_refund, escalate_to_human]
llm = get_llm().bind_tools(tools_list)

# 3. Define the Core Agent Execution Node

def sanitize_messages(messages):
    """Ensure no message sent to Gemini has empty content."""
    sanitized = []
    for msg in messages:
        is_empty_content = msg.content is None or (
            isinstance(msg.content, (str, list)) and len(msg.content) == 0
        )
        if is_empty_content:
            sanitized.append(msg.model_copy(update={"content": " "}))
            continue
        sanitized.append(msg)
    return sanitized

def call_model(state: AgentState):
    # 1. Define the strict autonomous behavior
    system_instruction = SystemMessage(content="""You are an autonomous customer support agent for an e-commerce company. 
    Your primary job is to independently evaluate refund requests. 
    CRITICAL INSTRUCTION: DO NOT ask the user for permission to look up their account or read the policy. 
    If a user asks about a refund, you must immediately and autonomously call the `fetch_customer_profile` tool and the `read_refund_policy` tool. 
    Evaluate the data strictly. If they meet the criteria, approve it. If they violate the rules, politely but firmly deny it. Hold the line.""")
    
    # 2. Prepend the system instruction to the sanitized history
    messages = [system_instruction] + sanitize_messages(state["messages"])
    logs = state.get("logs", [])
    
    logs.append("Invoking Gemini 2.5 Flash Engine to evaluate next action...")
    response = llm.invoke(messages)
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            logs.append(f"🤖 Agent decided to invoke tool: '{tool_call['name']}' with arguments {tool_call['args']}")
            
    return {"messages": [response], "logs": logs}

# 4. Define the Tool Execution Node wrapper to capture logs
tool_node = ToolNode(tools_list)

def call_tools(state: AgentState):
    logs = state.get("logs", [])
    logs.append("Executing system tool backend...")
    
    # Run the prebuilt tool execution node
    result = tool_node.invoke(state)
    result["logs"] = logs
    return result

# 5. Construct the Deterministic State Machine Graph
workflow = StateGraph(AgentState)

# Add our processing units
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)

# Establish execution boundaries
workflow.set_entry_point("agent")

# Conditional path: check if LLM requested tools or wants to talk back to user
workflow.add_conditional_edges(
    "agent",
    tools_condition,  # Built-in check that routes to "tools" if tool_calls exists, else END
)

# After tools run, loop back to the agent to analyze the tool outcomes
workflow.add_edge("tools", "agent")

# Compile into an executable application
agent_app = workflow.compile()