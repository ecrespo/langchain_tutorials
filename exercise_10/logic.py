from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEFAULT_MODEL = "gpt-4o-mini"


SYSTEM_MESSAGE = (
    "You are a diet planning assistant. Help users create balanced meal plans "
    "based on their goals, dietary needs, and preferences. Ask about one topic "
    "at a time to avoid overwhelming the user."
)


class DietChatBot:
    def __init__(self):
        """Initialize the Diet Chatbot."""
        self.model = init_chat_model(model=DEFAULT_MODEL, temperature=0)
        self.system_msg = SystemMessage(content=SYSTEM_MESSAGE)
        self.messages = [self.system_msg]

    def get_response(self, user_message: str) -> str:
        """Process user message and get AI response."""
        # Add user message to messages
        self.messages.append(HumanMessage(content=user_message))

        # Get response
        response = self.model.invoke(self.messages)

        # Add AI response to messages
        self.messages.append(AIMessage(content=response.text))

        return response.text

