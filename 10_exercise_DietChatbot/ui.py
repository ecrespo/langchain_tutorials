import gradio as gr


class ChatBotUI:
    def __init__(self, diet_chatbot):
        self.diet_chatbot = diet_chatbot

    def send_message_handler(self, user_message: str, history: list) -> tuple:
        """Send message to chatbot and get response."""
        # Trim the user message from whitespace
        user_message = user_message.strip()

        # If the user message is not empty, get the response from the chatbot
        if len(user_message):
            # Get response
            ai_response = self.diet_chatbot.get_response(user_message)

            # Add user message and AI response to chatbot history
            history.append(gr.ChatMessage(content=user_message, role="user"))
            history.append(gr.ChatMessage(content=ai_response, role="assistant"))

        # Return the user message as empty string and the updated chatbot history
        return "", history

    def create_ui(self) -> gr.Blocks:
        """Create the Gradio user interface."""
        with gr.Blocks(
            theme=gr.themes.Soft(), title="Diet Planning Chatbot"
        ) as interface:
            gr.Markdown("# Diet Planning Assistant")
            gr.Markdown(
                "I can help you create balanced meal plans based on your goals and preferences."
            )

            chatbot = gr.Chatbot(height=600)

            with gr.Row():
                with gr.Column(scale=4):
                    msg = gr.Textbox(
                        placeholder="Tell me about your dietary goals...",
                        show_label=False,
                    )

                with gr.Column(scale=1):
                    submit = gr.Button("💬 Send", variant="primary")

            # Event handlers for clicking the send button and pressing enter
            submit.click(self.send_message_handler, [msg, chatbot], [msg, chatbot])
            msg.submit(self.send_message_handler, [msg, chatbot], [msg, chatbot])

        return interface

