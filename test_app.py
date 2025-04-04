from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from crewai import Crew, Agent, Task
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")

# Define AI Agents
class ChatBot:
    def __init__(self):
        self.general_agent = Agent(
            role="General Assistant",
            goal="Answer general inquiries and provide helpful responses.",
            backstory="A friendly AI assistant trained to help users with various topics.",
            verbose=True,
            allow_delegation=True
        )

        self.tech_support_agent = Agent(
            role="Tech Support",
            goal="Provide troubleshooting steps and technical assistance.",
            backstory="An AI expert specializing in diagnosing tech issues.",
            verbose=True,
            allow_delegation=True
        )

        # File Analysis Crew
        self.document_parser_agent = Agent(
            role="Document Parser",
            goal="Extracts text and structures data from files.",
            backstory="An AI trained to process documents and extract meaningful content.",
            verbose=True
        )

        self.content_verifier_agent = Agent(
            role="Content Verifier",
            goal="Checks for inconsistencies, missing data, or errors.",
            backstory="An AI that ensures extracted document data is accurate and complete.",
            verbose=True
        )

        self.content_validator_agent = Agent(
            role="Content Validator",
            goal="Ensures content integrity and compliance with rules.",
            backstory="A specialist AI that validates data for correctness and security compliance.",
            verbose=True
        )

        # File Analysis Crew (Works Together)
        self.file_analysis_crew = Crew(
            agents=[
                self.document_parser_agent,
                self.content_verifier_agent,
                self.content_validator_agent
            ],
            verbose=True
        )

        # Main AI Crew (Includes Tech Support)
        self.crewai_crew = Crew(
            agents=[
                self.general_agent,
                self.tech_support_agent,
                self.document_parser_agent,
                self.content_verifier_agent,
                self.content_validator_agent
            ],
            verbose=True
        )

    def process_message(self, user_message):
        """Triggers different agents based on the conversation"""
        if any(word in user_message.lower() for word in ["error", "bug", "fix", "troubleshoot"]):
            task = Task(
                description="Help the user troubleshoot their issue. If a file is uploaded, collaborate with the File Analysis Crew.",
                agent=self.tech_support_agent
            )
        else:
            task = Task("Respond to the user’s general inquiries.", agent=self.general_agent)

        response = self.crewai_crew.kickoff(tasks=[task])
        return response

    def process_file(self, file_path):
        """Triggers the File Analysis Crew before passing results to Tech Support"""
        parse_task = Task(
            description=f"Extract text and structure data from the file at {file_path}.",
            agent=self.document_parser_agent
        )

        verify_task = Task(
            description="Check the extracted data for inconsistencies or missing elements.",
            agent=self.content_verifier_agent,
            dependencies=[parse_task]  # Verifier waits for Parser to finish
        )

        validate_task = Task(
            description="Ensure the document meets integrity and compliance standards.",
            agent=self.content_validator_agent,
            dependencies=[verify_task]  # Validator waits for Verifier
        )

        # Once validation is done, Tech Support receives the final result
        tech_support_task = Task(
            description="Use the final file analysis report to assist the user with troubleshooting.",
            agent=self.tech_support_agent,
            dependencies=[validate_task]  # Tech Support waits for Validation
        )

        # Run the multi-agent workflow
        response = self.crewai_crew.kickoff(tasks=[tech_support_task])
        return response

chat_bot = ChatBot()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("message")
def handle_message(data):
    user_message = data["message"]
    response = chat_bot.process_message(user_message)
    emit("response", {"message": response}, broadcast=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Process file with collaborative workflow
    response = chat_bot.process_file(file_path)
    return jsonify({"message": response})

if __name__ == "__main__":
    socketio.run(app, debug=True)
