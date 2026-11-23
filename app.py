import os

from database.db import db
from database.models import User, ActivityHistory
from functools import wraps


import webbrowser
from flask import Flask, render_template, request, session, redirect
from utils.content_generator import generate_content
from utils.prompt_engine import generate_prompt_response
from utils.sentiment import analyze_sentiment
from utils.information_extractor import extract_information
from utils.code_generator import generate_code
from utils.chatbot import get_chatbot_response
import tempfile
from utils.image_analyzer import analyze_image
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# Configure database
os.makedirs(app.instance_path, exist_ok=True)

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///promptcraft.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with Flask
db.init_app(app)

with app.app_context():
    db.create_all()

# Function to save user activity history
def save_history(feature_name, input_text, output_text):

    try:
        history = ActivityHistory(
            user_id=session["user_id"],
            feature_name=feature_name,
            input_text=str(input_text),
            output_text=str(output_text)
        )

        db.session.add(history)
        db.session.commit()

        return True

    except Exception as e:
        db.session.rollback()
        print("History Database Error:", e)
        return False

def login_required(route_function):

    @wraps(route_function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        return route_function(*args, **kwargs)

    return decorated_function


@app.before_request
def require_login():

    allowed_routes = ["login", "register", "logout", "static"]

    if request.endpoint in allowed_routes:
        return None

    if "user_id" not in session:
        return redirect("/login")

# User Activity History
@app.route("/history")
def history():

    user_history = ActivityHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        ActivityHistory.created_at.desc()
    ).all()

    return render_template(
        "history.html",
        history=user_history
    )


@app.route("/delete-history/<int:history_id>", methods=["POST"])
def delete_history(history_id):
    history_item = ActivityHistory.query.filter_by(
        id=history_id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(history_item)
    db.session.commit()

    return redirect("/history")


@app.route("/clear-history", methods=["POST"])
def clear_history():
    ActivityHistory.query.filter_by(
        user_id=session["user_id"]
    ).delete()

    db.session.commit()

    return redirect("/history")


@app.route("/analytics")
def analytics():
    user_history = ActivityHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        ActivityHistory.created_at.desc()
    ).all()

    feature_names = [
        "Content Generator",
        "Prompt Engineering Lab",
        "Sentiment Analysis",
        "Information Extraction",
        "AI Code Generator",
        "AI Chatbot",
        "Image-to-Text Analysis"
    ]

    feature_counts = {}

    for feature in feature_names:
        feature_counts[feature] = sum(
            1 for item in user_history
            if item.feature_name == feature
        )

    total_activities = len(user_history)

    recent_activities = user_history[:5]

    return render_template(
        "analytics.html",
        total_activities=total_activities,
        feature_counts=feature_counts,
        recent_activities=recent_activities
    )


# Home page
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")


# Content Generator page
@app.route("/generator", methods=["GET", "POST"])
def generator():

    generated_prompt = None
    generated_content = None
    error = None

    if request.method == "POST":

        topic = request.form.get("topic", "").strip()
        content_type = request.form.get("content_type")
        tone = request.form.get("tone")
        length = request.form.get("length")

        if not topic:
            error = "Please enter a topic."

        else:
            generated_prompt = f"""
            Create a {length} {content_type}
            about {topic}.
            Use a {tone} tone.
            """

            try:
                generated_content = generate_content(
                    topic,
                    content_type,
                    tone,
                    length
                )

            except Exception as e:
                print("Gemini API Error:", e)
                error = "Content generation failed. Please try again."

            else:
                save_history(
                    feature_name="Content Generator",
                    input_text=f"Topic: {topic}, Type: {content_type}, Tone: {tone}, Length: {length}",
                    output_text=generated_content
                )

    return render_template(
        "generator.html",
        generated_prompt=generated_prompt,
        generated_content=generated_content,
        error=error
    )


# Prompt Engineering Lab page

@app.route("/prompt-lab", methods=["GET", "POST"])
def prompt_lab():

    generated_prompt = None
    generated_response = None
    error = None

    if request.method == "POST":

        technique = request.form.get("technique", "")
        task = request.form.get("task", "").strip()
        example = request.form.get("example", "").strip()

        if not task:
            error = "Please enter a task."

        elif technique not in [
            "Zero-Shot",
            "One-Shot",
            "Few-Shot",
            "Role-Based",
            "Structured"
        ]:
            error = "Please select a valid prompting technique."

        elif technique in ["One-Shot", "Few-Shot"] and not example:
            error = "Please provide an example for this technique."

        else:
            try:
                generated_prompt, generated_response = generate_prompt_response(
                technique, task, example
                )

            except Exception as e:
                print("Prompt Lab Gemini Error:", e)
                error = "Unable to generate a response. Please try again."

            else:
                save_history(
                    feature_name="Prompt Engineering Lab",
                    input_text=f"Technique: {technique}, Task: {task}, Example: {example}",
                    output_text=f"Generated Prompt:\n{generated_prompt}\n\nAI Response:\n{generated_response}"
                )
    return render_template(
        "prompt_lab.html",
        generated_prompt=generated_prompt,
        generated_response=generated_response,
        error=error
    )

#sentiment analysis page
@app.route("/sentiment", methods=["GET", "POST"])
def sentiment():

    result = None
    error = None
    input_text = ""

    if request.method == "POST":

        input_text = request.form.get("text", "").strip()

        if not input_text:
            error = "Please enter some text to analyze."

        else:
            try:
                result = analyze_sentiment(input_text)

            except Exception as e:
                print("Sentiment Analysis Error:", e)
                error = "Unable to analyze sentiment. Please try again."

            else:
                save_history(
                    feature_name="Sentiment Analysis",
                    input_text=input_text,
                    output_text=str(result)
                )

    return render_template(
        "sentiment.html",
        result=result,
        error=error,
        input_text=input_text
    )


@app.route("/information-extraction", methods=["GET", "POST"])
def information_extraction():
    extracted_information = None
    error = None
    input_text = ""

    if request.method == "POST":
        input_text = request.form.get("text", "").strip()

        if not input_text:
            error = "Please enter some text to analyze."
        else:
            try:
                extracted_information = extract_information(input_text)

            except Exception as e:
                print("Information Extraction Error:", e)
                error = "Unable to extract information. Please try again."

            else:
                save_history(
                    feature_name="Information Extraction",
                    input_text=input_text,
                    output_text=str(extracted_information)
                )
    return render_template(
        "information_extraction.html",
        extracted_information=extracted_information,
        error=error,
        input_text=input_text
    )


@app.route("/code-generator", methods=["GET", "POST"])
def code_generator():
    generated_code = None
    error = None
    task = ""
    language = ""
    difficulty = ""

    if request.method == "POST":
        task = request.form.get("task", "").strip()
        language = request.form.get("language", "")
        difficulty = request.form.get("difficulty", "")

        if not task:
            error = "Please enter a programming task."
        else:
            try:
                generated_code = generate_code(
                task, language, difficulty
            )

            except Exception as e:
                print("Code Generator Error:", e)
                error = "Unable to generate code. Please try again."

            else:
                save_history(
                    feature_name="AI Code Generator",
                    input_text=f"Task: {task}, Language: {language}, Difficulty: {difficulty}",
                    output_text=str(generated_code)
                )

    return render_template(
        "code_generator.html",
        generated_code=generated_code,
        error=error,
        task=task,
        language=language,
        difficulty=difficulty
    )


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    error = None

    if "conversation_history" not in session:
        session["conversation_history"] = []

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if not message:
            error = "Please enter a message."
        else:
            try:
                reply, history = get_chatbot_response(
                message,
                session["conversation_history"]
            )

            except Exception as e:
                print("Chatbot Error:", e)
                error = "Unable to generate a response. Please try again."

            else:
                session["conversation_history"] = history
                session.modified = True

            save_history(
                feature_name="AI Chatbot",
                input_text=message,
                output_text=reply
            )

    return render_template(
        "chatbot.html",
        conversation_history=session["conversation_history"],
        error=error
    )


@app.route("/clear-chat", methods=["POST"])
def clear_chat():
    session.pop("conversation_history", None)
    return redirect("/chatbot")


# Image-to-Text Analysis
@app.route("/image-to-text", methods=["GET", "POST"])
def image_to_text():
    result = None
    error = None
    question = "Describe this image in detail."

    if request.method == "POST":
        image_file = request.files.get("image")
        question = request.form.get("question", "").strip() or question

        if not image_file or not image_file.filename:
            error = "Please upload an image."

        else:
            extension = os.path.splitext(image_file.filename)[1].lower()

            if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
                error = "Please upload a JPG, JPEG, PNG, or WEBP image."

            else:
                temp_path = None

                try:
                    with tempfile.NamedTemporaryFile(
                        suffix=extension, delete=False
                    ) as temp_file:
                        temp_path = temp_file.name

                    image_file.save(temp_path)

                    if os.path.getsize(temp_path) > 5 * 1024 * 1024:
                        raise ValueError("Image size must be less than 5 MB.")

                    result = analyze_image(temp_path, question)

                    save_history(
                        feature_name="Image-to-Text Analysis",
                        input_text=question,
                        output_text=result
                    )

                except Exception as e:
                    print("Image Analysis Error:", e)
                    error = str(e) if isinstance(e, ValueError) else (
                        "Unable to analyze the image. Please try again."
                    )

                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

    return render_template(
        "image_to_text.html",
        result=result,
        error=error,
        question=question
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    error = None
    success = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            error = "All fields are required."

        elif len(password) < 8:
            error = "Password must contain at least 8 characters."

        else:
            existing_user = User.query.filter_by(email=email).first()

            if existing_user:
                error = "An account with this email already exists."

            else:
                new_user = User(
                    username=username,
                    email=email
                )

                new_user.set_password(password)

                db.session.add(new_user)
                db.session.commit()

                success = "Registration successful! You can now log in."

    return render_template(
        "register.html",
        error=error,
        success=success
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect("/")

        else:
            error = "Invalid email address or password."

    return render_template(
        "login.html",
        error=error
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000/logout")
    app.run(debug=True)
