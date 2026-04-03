from assistant import hotel_assistant
from langchain_core.messages import HumanMessage
from utils import print_message

if __name__ == "__main__":
    user_message = HumanMessage(
        "I'm looking for a relaxing wellness retreat in Japan. Where are the best natural hot springs (onsen) located, "
        "and what is the weather like there now? Find me a good hotel close by."
    )
    print_message(user_message)

    result = hotel_assistant.invoke({"messages": [user_message]})

