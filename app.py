from flask import Flask, render_template, request, redirect, session, send_file
from reportlab.pdfgen import canvas
import sqlite3
from google import genai
from secret import API_KEY

app = Flask(__name__)
app.secret_key = "studyassistant"

# Gemini Client
client = genai.Client(api_key=API_KEY)
#print("API KEY:", API_KEY)

# Progress Data
# Progress Data
progress = {
    "Python": 80,
    "Java": 70,
    "HTML": 90
}

latest_question = ""
latest_answer = ""

# Quiz Data
quiz_data = {
    "python": [
        {
            "question": "Who created Python?",
            "answer": "Guido van Rossum"
        },
        {
            "question": "Python is a ______ language.",
            "answer": "Programming"
        }
    ],

    "java": [
        {
            "question": "Java is an ______ language.",
            "answer": "Object Oriented"
        }
    ]
}


# Save Chat
def save_chat(username, question, answer):

    connection = sqlite3.connect("study.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO chats(username, question, answer) VALUES (?, ?, ?)",
        (username, question, answer)
    )

    connection.commit()
    connection.close()


@app.route('/')
def login_page():
    return render_template("login.html")


@app.route('/register')
def register_page():
    return render_template("register.html")


@app.route('/register', methods=['POST'])
def register():

    username = request.form['username']
    password = request.form['password']

    connection = sqlite3.connect("study.db")
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, password)
        )

        connection.commit()

    except:
        return "User already exists"

    connection.close()

    return redirect('/')


@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    connection = sqlite3.connect("study.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()

    connection.close()

    if user:
        session['user'] = username
        return redirect('/home')

    return "Invalid Login"


@app.route('/home')
def home():

    if 'user' not in session:
        return redirect('/')

    connection = sqlite3.connect("study.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT question, answer FROM chats WHERE username=?",
        (session['user'],)
    )

    history = cursor.fetchall()

    connection.close()

    return render_template(
        "index.html",
        user=session['user'],
        history=history,
        progress=progress
    )


@app.route('/ask', methods=['POST'])
def ask():

    global latest_question
    global latest_answer

    question = request.form['question']

    prompt = f"""
You are an AI Study Assistant.

Give simple and short answers.
Maximum 150 words.
Use bullet points if needed.

Question:
{question}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text

    except Exception as e:

        answer = f"Error: {e}"

    latest_question = question
    latest_answer = answer

    save_chat(
        session['user'],
        question,
        answer
    )

    return redirect('/home')

@app.route('/history')
def history():

    connection = sqlite3.connect("study.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT question, answer FROM chats WHERE username=?",
        (session['user'],)
    )

    records = cursor.fetchall()

    connection.close()

    return render_template(
        "history.html",
        records=records
    )


@app.route('/quiz/<subject>')
def quiz(subject):

    questions = quiz_data.get(subject.lower(), [])

    return render_template(
        "quiz.html",
        subject=subject,
        questions=questions
    )


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

@app.route("/download")
def download():

    c = canvas.Canvas("notes.pdf")

    c.drawString(50, 800, "AI Study Assistant Notes")

    c.drawString(50, 760, "Question:")

    c.drawString(50, 740, latest_question)

    c.drawString(50, 700, "Answer:")

    y = 680

    for line in latest_answer.split("\n"):
        c.drawString(50, y, line[:90])
        y -= 20

    c.save()

    return send_file(
        "notes.pdf",
        as_attachment=True
    )
@app.route('/aiquiz', methods=['POST'])
def aiquiz():

    topic = request.form['topic']

    prompt = f"""
Generate 10 unique multiple-choice quiz questions about {topic}.

Rules:
- Questions must be different.
- Include four options.
- Mention the correct answer.
- Suitable for college students.

Format:

1. Question
A)
B)
C)
D)
Answer:
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        quiz = response.text

    except Exception as e:

        quiz = f"Error: {e}"

    return render_template(
        "aiquiz.html",
        topic=topic,
        quiz=quiz
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)