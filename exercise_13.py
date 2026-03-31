def stream_diet_response():
    """Stream a response chunk by chunk"""
    response = "I'll help you create a healthy meal plan for your goals."

    # Stream response in small chunks
    for word in response.split():
        yield word + " "


# Using the generator
print("LLM streaming response:\n")
for i, chunk in enumerate(stream_diet_response()):
    print(f"Chunk {i + 1}: {chunk.strip()}")