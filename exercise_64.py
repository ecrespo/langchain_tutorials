import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from devtools import pprint

load_dotenv()


import pandas as pd
from langchain_core.tools import tool
from typing import List, Dict
from datetime import datetime, timedelta


def load_csv_data():
    """Load CSV data files"""
    users_df = pd.read_csv("data/agentic-systems/agentic-workflows/users.csv")
    bookings_df = pd.read_csv("data/agentic-systems/agentic-workflows/bookings.csv")
    availability_df = pd.read_csv(
        "data/agentic-systems/agentic-workflows/availability.csv"
    )
    return users_df, bookings_df, availability_df


@tool
def get_user_context(user_id: str) -> dict:
    """
    Get user context including profile and active bookings.

    Args:
        user_id: The user ID to look up
    """
    users_df, bookings_df, _ = load_csv_data()

    # Get user info
    user_row = users_df[users_df["user_id"] == user_id]
    if user_row.empty:
        return {"error": f"User {user_id} not found"}

    user_info = user_row.iloc[0].to_dict()

    # Get user's active bookings
    user_bookings = bookings_df[bookings_df["user_id"] == user_id]
    active_bookings = []

    for _, booking in user_bookings.iterrows():
        active_bookings.append(
            {
                "booking_id": booking["booking_id"],
                "hotel_id": booking["hotel_id"],
                "hotel": booking["hotel"],
                "check_in": booking["check_in"],
                "check_out": booking["check_out"],
                "room_type": booking["room_type"],
                "amount_paid_per_night": booking["amount_paid_per_night"],
                "total_amount": booking["total_amount"],
            }
        )

    return {
        "user_id": user_info["user_id"],
        "tier": user_info["tier"],
        "total_spent": user_info["total_spent"],
        "previous_bookings": user_info["previous_bookings"],
        "active_bookings": active_bookings,
    }


@tool
def query_rooms(
    hotel_id: str,
    room_type: str,
    check_in: str,
    check_out: str,
) -> List[Dict]:
    """
    Query room availability for specific hotel and parameters.

    Args:
        hotel_id: Hotel identifier
        room_type: Type of room
        check_in: Check-in date (YYYY-MM-DD format)
        check_out: Check-out date (YYYY-MM-DD format)
    """
    _, _, availability_df = load_csv_data()

    # Parse dates and create date range
    start_date = datetime.strptime(check_in, "%Y-%m-%d")
    end_date = datetime.strptime(check_out, "%Y-%m-%d")

    results = []
    current_date = start_date

    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        # Query availability for this specific date
        availability_row = availability_df[
            (availability_df["hotel_id"] == hotel_id)
            & (availability_df["room_type"] == room_type)
            & (availability_df["date"] == date_str)
        ]

        if not availability_row.empty:
            row = availability_row.iloc[0]
            results.append(
                {
                    "date": date_str,
                    "available": row["available"],
                    "rate_per_night": row["rate_per_night"],
                }
            )
        else:
            # Default to not available if no data
            results.append({"date": date_str, "available": False, "rate_per_night": 0})

        current_date += timedelta(days=1)

    return results


@tool
def modify_reservation(
    booking_id: str,
    modifications: List[Dict[str, str]],
    reason: str = "Customer request",
) -> str:
    """
    Modify an existing hotel reservation.

    Args:
        booking_id: The booking ID to modify
        modifications: List of changes to make
        reason: Reason for the modification
    """
    change_summary = []
    for mod in modifications:
        field = mod["field"]
        new_value = mod["new_value"]
        change_summary.append(f"{field} changed to {new_value}")

    return f"""RESERVATION MODIFICATION SUCCESSFUL
Booking ID: {booking_id}
Changes: {", ".join(change_summary)}
Reason: {reason}
Status: Confirmed"""


@tool
def cancel_reservation(booking_id: str, reason: str = "Customer request") -> str:
    """
    Cancel an existing hotel reservation.

    Args:
        booking_id: The booking ID to cancel
        reason: Reason for cancellation
    """
    return f"""RESERVATION CANCELLATION PROCESSED
Booking ID: {booking_id}
Reason: {reason}
Status: Cancelled
Refund: Processing according to policy"""


llm = init_chat_model("gpt-4o-mini")


def format_conversation_history(messages: list) -> str:
    if not messages:
        return "No conversation history yet."
    formatted = "=== CONVERSATION HISTORY ===\n"
    for msg in messages:
        if isinstance(msg, HumanMessage):
            formatted += f"USER: {msg.text}\n"
        elif isinstance(msg, AIMessage):
            formatted += f"ASSISTANT: {msg.text}\n"
    return formatted


IDENTIFY_DETAILS_PROMPT = """
You are a Detail Identification specialist for hotel booking management.
Your job is to analyze the user context and identify which booking the user
wants to modify and what exactly they want to change.

INSTRUCTIONS:

Review the provided user context, then:

(a) Identify Target Booking: Review customer's active reservations from
user context. Match booking against conversation details (dates, hotel
names, room types). Identify the booking_id, hotel_id and room_type of the
target booking for modification or cancellation.

If Unable to Identify: Set details_identified to False and provide a clear
question asking the user to specify which booking they want to modify.
Include a list of their active reservations with dates and hotels.

(b) Extract Request Details: Determine if this is a modification or
cancellation request. If cancellation, set content to "Cancellation
request - no further details needed". If modification, extract specific
changes requested: desired new dates, new room type, etc. Note flexibility
indicators
(date ranges, alternative options).

If Unable to Identify: Set details_identified to False and provide a clear
question asking the user to clarify specific changes needed. Include
examples of common modifications.

OUTPUT REQUIREMENTS:

You must return a structured output with the following fields:

- details_identified (boolean): True if booking and changes are clearly
  identified, False if more information needed
- request_type: "modification" or "cancellation" if identified, None
  otherwise
- user_context (dict): The complete user context provided below
- content (string): Either the request details if identified, or the
  clarifying question if not

INPUTS:

Today's Date: {today} User ID: {user_id} Conversation History:
{conversation_history} User Context: {user_context}
"""

AVAILABILITY_ANALYSIS_PROMPT = """
You are an Availability Analyst for hotel booking management. Check room
availability for the requested booking changes.

INSTRUCTIONS:

Use `query_rooms` tool with extracted parameters. Search exact requested
dates and room types first. If limited availability, try alternative
dates (±3 days) and room categories.

Note: This analysis applies to both modifications and cancellations to
understand impact.

Output Format: Return analysis with Available Options and Alternatives.

INPUTS:

Request Details: {request_details}"""

FX_POLICY_ANALYSIS_PROMPT = """You are a Financial Policy Analyst for hotel
booking management. Analyze the financial implications of the booking
change request.

INSTRUCTIONS:

For Modifications:

- rate_difference = (new_rate_per_night - amount_paid_per_night) ×
  nights_count
- Change fees by notice: >48h=$0, 24-48h=$25, <24h=$50
- total_cost_of_request = rate_difference + change_fee

For Cancellations:

- Hotel penalties by notice: >48h=0%, 24-48h=50%, <24h=100% of booking
- Processing cost: $25 all cancellations
- total_cost_of_request = (original_booking × penalty_%) + $25

Examples:

- 36h Modification: Original=$200/night, new=$250/night, 3 nights,
  rate_diff=$150, change_fee=$25, total=$175
- <24h Cancellation: Original=$450, penalty=100%=$450,
  processing=$25, total=$475

Output Format:

Financial Analysis:

- total_cost_of_request: [amount]
- cost breakdown: [itemized components]

INPUTS:

Today's Date: {today} User Context: {user_context} Request Details:
{request_details} Availability Analysis: {availability_analysis}
"""

CX_POLICY_ANALYSIS_PROMPT = """
You are a Customer Experience Policy Analyst for hotel booking management.
Analyze the customer experience implications of the booking change request.

INSTRUCTIONS:

Analysis Inputs: tier, previous_bookings, total_spent, request_type,
request_urgency

Processing Rules:

(a) Customer Value Classification: Determine from total_spent -
High >$2000, Medium $500-$2000, Low <$500

(b) Booking Frequency Classification: Determine from previous_bookings -
High >6 bookings, Medium 2-6 bookings, Low <2 bookings

(c) Relationship Risk Assessment: Determine likelihood of customer
relationship damage if request rejected based on request nature, customer
communication tone, and complexity

(d) Service Priority Determination: Combine tier + customer_value +
relationship_risk to classify as Low/Medium/High

Output Format:

Customer Experience Analysis:

- loyalty_tier: [Bronze/Silver/Gold]
- customer_value: [High/Medium/Low]
- relationship_risk: [High/Medium/Low]
- service_priority: [Low/Medium/High]

INPUTS:

User Context: {user_context} Request Details: {request_details}
Availability Analysis: {availability_analysis}
"""

DETERMINE_ACTION_PROMPT = """
You are an Action Determination specialist for hotel booking management.
Decide whether to approve or reject the booking change request based on
policy analysis.

INSTRUCTIONS:

Cost Absorption Tolerance by Tier: Bronze=$0, Silver=$25, Gold=$100

Decision Framework: total_cost_of_request vs tier_tolerance +
service_priority override

Accept Conditions: total_cost_of_request <= tier_tolerance OR
service_priority=High AND total_cost_of_request <= $50

Reject Conditions: total_cost_of_request > tier_tolerance AND
service_priority != High

Examples:

- Bronze customer, $30 cost, Low priority → Reject (exceeds $0 tolerance)
- Silver customer, $20 cost, Medium priority → Accept (within $25
  tolerance)
- Gold customer, $150 cost, Low priority → Reject (exceeds $100 tolerance)
- Any tier, $40 cost, High priority → Accept (high priority override)

Action Format:

- For approved modifications: use modify_reservation tool
- For approved cancellations: use cancel_reservation tool
- For rejections: provide clear reasoning without using tools

INPUTS:

Today's Date: {today} 
User Context: {user_context} 
Request Details: {request_details} 
Availability Analysis: {availability_analysis} 
Financial Analysis: {fx_policy_analysis} 
Customer Experience Analysis: {cx_policy_analysis}
"""

COMMUNICATE_OUTCOME_PROMPT = """
You are a Communication specialist for hotel booking management. Generate
the final customer response based on the outcome of their booking request.

INSTRUCTIONS:

Communication Guidelines:

(a) Style: Conversational chat message, helpful and direct, no signature

(b) Acceptance Confirmations: Confirm details with dates/room, highlight
upgrades, next steps, appreciate flexibility

(c) Rejection Explanations: Empathetic explanation, alternative options,
policy reasoning, contact info

(d) Information Requests: Specific questions, explain need, provide
examples, set expectations

Output Format: Single conversational message appropriate for chat interface

INPUTS:

Request Details: {request_details} Communication Type: {communication_type}
Communication Context: {communication_context}
"""


class State(TypedDict):
    # Input fields
    today: str
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str
    # Request Details
    user_context: dict
    request_type: Literal["modification", "cancellation"] | None
    request_details: str | None
    info_request: str | None
    # Availabilty Analysis
    availability_messages: Annotated[list[AnyMessage], add_messages]
    availability_analysis: str
    # Policy Analysis
    fx_policy_analysis: str
    cx_policy_analysis: str
    # Decision Fields
    action_spec: AIMessage | None
    action_result: str
    rejection_reason: str | None


from pydantic import BaseModel, Field
from typing import Literal


class DetailIdentificationResult(BaseModel):
    """Structured output for Detail Identification node."""

    details_identified: bool = Field(
        description="True if booking and requested changes are clearly identified, False if more information needed"
    )
    request_type: Literal["modification", "cancellation"] | None = Field(
        description="Type of request - 'modification' for date/room changes, 'cancellation' for cancellations, None if unable to identify"
    )
    user_context: dict = Field(
        description="Complete user context as obtained from the get_user_context tool"
    )
    content: str = Field(
        description="If details_identified=True: the request details. If False: the specific clarifying question to ask user"
    )


def identify_details_node(state: State):
    # First, get user context directly (no LLM involvement)
    user_context = get_user_context.invoke({"user_id": state["user_id"]})

    # Format conversation for context
    conversation_context = format_conversation_history(state["messages"])

    # Now call LLM with structured output
    system_prompt = IDENTIFY_DETAILS_PROMPT.format(
        conversation_history=conversation_context,
        user_id=state["user_id"],
        today=state["today"],
        user_context=user_context,
    )

    # Get structured output directly
    detail_llm = llm.with_structured_output(
        DetailIdentificationResult, method="function_calling"
    )
    response = detail_llm.invoke([SystemMessage(content=system_prompt)])

    if response.details_identified:
        return {
            "user_context": user_context,
            "request_type": response.request_type,
            "request_details": response.content,
        }
    else:
        return {"user_context": user_context, "info_request": response.content}


def identify_details_condition(
    state: State,
) -> Literal["communicate", "continue_workflow"]:
    # Check if we need info from user
    if state.get("info_request"):
        return "communicate"

    # Otherwise continue workflow
    return "continue_workflow"


def analyze_availability_node(state: State):
    availability_llm = llm.bind_tools([query_rooms])
    system_prompt = AVAILABILITY_ANALYSIS_PROMPT.format(
        request_details=state["request_details"],
    )
    prompt_messages = [SystemMessage(content=system_prompt)] + state.get(
        "availability_messages", []
    )
    response = availability_llm.invoke(prompt_messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"availability_messages": [response]}
    else:
        return {
            "availability_messages": [response],
            "availability_analysis": response.content,
        }


def availability_tool_node(state: State):
    availability_messages = state["availability_messages"]
    last_message = availability_messages[-1]
    if not last_message.tool_calls:
        return {}
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool = {"query_rooms": query_rooms}[tool_call["name"]]
        tool_message = tool.invoke(tool_call)
        tool_messages.append(tool_message)
    return {"availability_messages": tool_messages}


def availability_condition(state: State) -> Literal["tools", "continue"]:
    availability_messages = state.get("availability_messages", [])
    if (
        availability_messages
        and hasattr(availability_messages[-1], "tool_calls")
        and availability_messages[-1].tool_calls
    ):
        return "tools"
    return "continue"


def analyze_fx_policy_node(state: State):
    system_prompt = FX_POLICY_ANALYSIS_PROMPT.format(
        today=state["today"],
        user_context=state["user_context"],
        request_details=state["request_details"],
        availability_analysis=state.get("availability_analysis", ""),
    )
    response = llm.invoke([SystemMessage(content=system_prompt)])
    return {"fx_policy_analysis": response.content}


def analyze_cx_policy_node(state: State):
    system_prompt = CX_POLICY_ANALYSIS_PROMPT.format(
        user_context=state["user_context"],
        request_details=state["request_details"],
        availability_analysis=state.get("availability_analysis", ""),
    )
    response = llm.invoke([SystemMessage(content=system_prompt)])
    return {"cx_policy_analysis": response.content}


def determine_action_node(state: State):
    # Bind both modification and cancellation tools
    action_llm = llm.bind_tools([modify_reservation, cancel_reservation])
    system_prompt = DETERMINE_ACTION_PROMPT.format(
        today=state["today"],
        user_context=state["user_context"],
        request_details=state["request_details"],
        availability_analysis=state.get("availability_analysis", ""),
        fx_policy_analysis=state["fx_policy_analysis"],
        cx_policy_analysis=state["cx_policy_analysis"],
    )
    response = action_llm.invoke([SystemMessage(content=system_prompt)])

    if response.tool_calls:
        return {"action_spec": response}
    else:
        return {"rejection_reason": response.content}


def execute_action_node(state: State):
    """Execute the tool calls from the action determination node."""
    action_spec = state.get("action_spec")
    if not action_spec or not action_spec.tool_calls:
        return {}

    tool_results = []
    for tool_call in action_spec.tool_calls:
        # Determine which tool to use based on the tool call name
        if tool_call["name"] == "modify_reservation":
            tool_message = modify_reservation.invoke(tool_call)
        elif tool_call["name"] == "cancel_reservation":
            tool_message = cancel_reservation.invoke(tool_call)
        else:
            continue
        tool_results.append(tool_message.text)

    combined_result = "\n".join(tool_results)
    return {"action_result": combined_result}


def action_condition(state: State) -> Literal["execute", "communicate"]:
    """Route based on whether action was approved (has tool calls) or rejected."""
    if state.get("action_spec"):
        return "execute"
    else:
        return "communicate"


def communicate_outcome_node(state: State):
    if state.get("info_request"):
        communication_type = "request_info"
        communication_context = state["info_request"]
    elif state.get("rejection_reason"):
        communication_type = "reject_request"
        communication_context = state["rejection_reason"]
    else:
        communication_type = "accept_request"
        communication_context = state.get(
            "action_result", "Request processed successfully."
        )

    system_prompt = COMMUNICATE_OUTCOME_PROMPT.format(
        request_details=state.get("request_details", "No details available"),
        communication_type=communication_type,
        communication_context=communication_context,
    )
    response = llm.invoke([SystemMessage(content=system_prompt)])
    return {"messages": [AIMessage(content=response.content)]}


# -----NEW CODE-----#


# Workaround node for parallel execution (needed for policy dispatcher)
def policy_dispatcher(state: State):
    """Dispatcher node that enables parallel policy analysis."""
    return {}


# Define Graph
workflow = StateGraph(State)

# Define Nodes
workflow.add_node("identify_details", identify_details_node)
workflow.add_node("analyze_availability", analyze_availability_node)
workflow.add_node("availability_tools", availability_tool_node)
workflow.add_node("policy_dispatcher", policy_dispatcher)
workflow.add_node("analyze_fx_policy", analyze_fx_policy_node)
workflow.add_node("analyze_cx_policy", analyze_cx_policy_node)
workflow.add_node("determine_action", determine_action_node)
workflow.add_node("execute_action", execute_action_node)
workflow.add_node("communicate_outcome", communicate_outcome_node)

# Define Edges

# Identify details
workflow.add_edge(START, "identify_details")
workflow.add_conditional_edges(
    "identify_details",
    identify_details_condition,
    {"communicate": "communicate_outcome", "continue_workflow": "analyze_availability"},
)

# Availability analysis with tool reflection
workflow.add_conditional_edges(
    "analyze_availability",
    availability_condition,
    {"tools": "availability_tools", "continue": "policy_dispatcher"},
)
workflow.add_edge("availability_tools", "analyze_availability")

# Parallel policy analysis
workflow.add_edge("policy_dispatcher", "analyze_fx_policy")
workflow.add_edge("policy_dispatcher", "analyze_cx_policy")
workflow.add_edge("analyze_fx_policy", "determine_action")
workflow.add_edge("analyze_cx_policy", "determine_action")

# Action determination and execution
workflow.add_conditional_edges(
    "determine_action",
    action_condition,
    {"execute": "execute_action", "communicate": "communicate_outcome"},
)
workflow.add_edge("execute_action", "communicate_outcome")

# Final communication
workflow.add_edge("communicate_outcome", END)

# Compile
booking_agent = workflow.compile()

# Test 1: Clear
print("Clear test case...")
booking_agent = workflow.compile()
test_state = {
    "today": "2024-06-01",
    "user_id": "user_001",
    "messages": [
        HumanMessage(
            content="I need to change my July reservation from July 1-5 to July 10-14"
        )
    ],
}
final_state = {}
for mode, chunk in booking_agent.stream(test_state, stream_mode=["updates", "values"]):
    if mode == "updates":
        # Node just finished executing
        node_name = list(chunk.keys())[0]
        print(f"  ✓ Completed: {node_name}")
    elif mode == "values":
        # Keep updating final_state but don't print it yet
        final_state = chunk

# Print the final state once at the end
pprint(f"User Context: {final_state.get('user_context', 'None')}")
pprint(f"Details identified: {final_state.get('request_details', 'None')}")
pprint(f"Info request: {final_state.get('info_request', 'None')}")
pprint(f"Availability Analysis: {final_state.get('availability_analysis', 'None')}")
if "messages" in final_state and final_state["messages"]:
    pprint(f"Final response: {final_state['messages'][-1].text}\n")

# Test 2: Unclear
print("Unclear case...")
test_state_unclear = {
    "today": "2024-08-01",
    "user_id": "user_002",
    "messages": [HumanMessage(content="I need to change my reservation")],
}
final_state_unclear = {}
for mode, chunk in booking_agent.stream(
    test_state_unclear, stream_mode=["updates", "values"]
):
    if mode == "updates":
        # Node just finished executing
        node_name = list(chunk.keys())[0]
        print(f"  ✓ Completed: {node_name}")
    elif mode == "values":
        # Keep updating final_state_unclear but don't print it yet
        final_state_unclear = chunk

# Now print the final state once at the end
pprint(f"User Context: {final_state_unclear.get('user_context', 'None')}")
pprint(f"Details identified: {final_state_unclear.get('request_details', 'None')}")
pprint(f"Info request: {final_state_unclear.get('info_request', 'None')}")
pprint(f"Availability Analysis: {final_state.get('availability_analysis', 'None')}")
if "messages" in final_state_unclear and final_state_unclear["messages"]:
    pprint(f"Final response: {final_state_unclear['messages'][-1].text}")

