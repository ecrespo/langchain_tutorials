# from assistant import TravelAssistant
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from assistant import TravelAssistant


def print_conversation(messages):
    """Print the conversation with proper formatting for each message type."""
    for msg in messages:
        if isinstance(msg, SystemMessage):
            continue  # Skip system messages for cleaner output
        elif isinstance(msg, AIMessage):
            # For AI messages, use text() method to get clean content
            print(f"\n🤖 Assistant: {msg.text}")
            if msg.tool_calls:
                print(
                    f"   [Calling tools: {', '.join([tc['name'] for tc in msg.tool_calls])}]"
                )
        else:
            # For other message types, use pretty_print()
            msg.pretty_print()


# Create our complete assistant
assistant = TravelAssistant()

# Test conversation demonstrating all tools
assistant.chat("I'm planning a trip to Tokyo for the next week. Find me a nice hotel.")
assistant.chat(
    "Nice. How much will the cheapest hotel be for the whole week and tell me what the weather will be like?"
)
assistant.chat("Great, please book it for me")
assistant.chat(
    "I'm in Dubai right now. What time will it be in Tokyo when I arrive if I leave at 10am?"
)

# Display the complete conversation
print("=== Complete Travel Planning Conversation ===")
print_conversation(assistant.messages)

