from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from crewai import Crew, Agent, Task
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Define CrewAI Agents
class ChatBot:
    def __init__(self):
        self.general_agent = Agent(
            role="General Assistant",
            goal="Answer general inquiries and provide helpful responses.",
            verbose=True
        )

        self.tech_support_agent = Agent(
            role="Tech Support",
            goal="Help users troubleshoot and fix technical issues.",
            verbose=True
        )

        self.document_analysis_agent = Agent(
            role="Document Analyst",
            goal="Extract and analyze text from uploaded documents.",
            verbose=True
        )

        # Crew Workflow
        self.crewai_crew = Crew(
            agents=[self.general_agent, self.tech_support_agent, self.document_analysis_agent],
            verbose=True
        )

    def process_message(self, user_message):
        """Triggers specific agents based on the user message"""

        if any(word in user_message.lower() for word in ["error", "issue", "troubleshoot"]):
            task = Task("Assist with troubleshooting the reported issue.", agent=self.tech_support_agent)
            response = self.crewai_crew.kickoff(tasks=[task])
            socketio.emit("agent_response", {"agent": "Tech Support", "message": response})

        elif any(word in user_message.lower() for word in ["document", "analyze", "file"]):
            task = Task("Analyze the uploaded document and extract key information.", agent=self.document_analysis_agent)
            response = self.crewai_crew.kickoff(tasks=[task])
            socketio.emit("agent_response", {"agent": "Document Analyst", "message": response})

        else:
            task = Task("Provide general assistance.", agent=self.general_agent)
            response = self.crewai_crew.kickoff(tasks=[task])
            socketio.emit("agent_response", {"agent": "General Assistant", "message": response})

        return response

chat_bot = ChatBot()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("message")
def handle_message(data):
    user_message = data["message"]
    chat_bot.process_message(user_message)

if __name__ == "__main__":
    socketio.run(app, debug=True)
