from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import openai  # Using OpenAI for generating suggestions
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Predefined suggestion categories
SUGGESTIONS = {
    "document": ["Upload a document", "Analyze document content", "Extract key details"],
    "speech": ["Convert speech to text", "Analyze speech sentiment", "Summarize spoken content"],
    "tech_support": ["Troubleshoot an issue", "Report a bug", "Get system diagnostics"],
}

def generate_suggestions(user_message):
    """Generate AI suggestions based on user input."""
    # Simple keyword matching (can be replaced with LLM for better accuracy)
    if any(word in user_message.lower() for word in ["doc", "file", "upload"]):
        return SUGGESTIONS["document"]
    elif any(word in user_message.lower() for word in ["speech", "talk", "audio"]):
        return SUGGESTIONS["speech"]
    elif any(word in user_message.lower() for word in ["error", "bug", "issue"]):
        return SUGGESTIONS["tech_support"]
    
    # Generate AI-based suggestions using OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Suggest 3 actions based on this message: {user_message}"}],
            max_tokens=50,
        )
        suggestions = response['choices'][0]['message']['content'].split("\n")
        return suggestions[:3]  # Return only top 3 suggestions
    except:
        return ["Try again", "Ask another question", "See help options"]

@socketio.on("message")
def handle_message(data):
    user_message = data["message"]
    
    # Process the user's message
    response = f"AI Response: {user_message}"  # Placeholder AI response
    emit("response", {"message": response}, broadcast=True)

    # Generate AI suggestions
    suggestions = generate_suggestions(user_message)
    emit("suggestions", {"suggestions": suggestions}, broadcast=True)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, debug=True)
