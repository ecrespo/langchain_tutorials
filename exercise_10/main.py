# from logic import DietChatBot
# from ui import ChatBotUI
from logic import DietChatBot
from ui import ChatBotUI


# Initialize the chatbot
diet_chatbot = DietChatBot()

# Create and launch the UI
chatbot_ui = ChatBotUI(diet_chatbot)
interface = chatbot_ui.create_ui()

interface.launch()

