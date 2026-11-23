
from utils.content_generator import client


def get_chatbot_response(message, conversation_history=None):

    if conversation_history is None:
        conversation_history = []

    conversation_history.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=conversation_history,
        config={
            "system_instruction": (
                "You are PromptCraft AI Assistant, a helpful and "
                "friendly AI chatbot. Answer questions clearly, "
                "accurately and in a beginner-friendly manner. "
                "Provide examples whenever useful."
            )
        }
    )

    chatbot_reply = response.text

    conversation_history.append({
        "role": "model",
        "parts": [{"text": chatbot_reply}]
    })

    return chatbot_reply, conversation_history
