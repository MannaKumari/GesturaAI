from flask import Flask, render_template, request, jsonify, Response
import time
import queue

app = Flask(__name__)

current_task = None
current_option = None

chat_history = []
last_emotion = None

event_queue = queue.Queue()


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/perform")
def perform():
    return render_template("perform.html")


@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html", chat_history=chat_history)


@app.route("/emotion")
def emotion():
    return render_template("emotion.html", last=last_emotion)


@app.route("/set_task", methods=["POST"])
def set_task():
    global current_task, current_option

    data = request.get_json()
    current_task = data.get("task")
    current_option = data.get("option")

    print("Task set:", current_task, current_option)

    return jsonify({"status": "ok"})


@app.route("/get_task")
def get_task():
    return jsonify({
        "task": current_task,
        "option": current_option
    })


@app.route("/gesture_detected", methods=["POST"])
def gesture_detected():
    global current_task, chat_history, last_emotion

    data = request.get_json()
    detected_text = data.get("data", "")

    print("Detector sent:", detected_text)

    if current_task == "chatbot":
        gesture = detected_text

        meaning_map = {
        "Palm": ("Hello", "Hello! Do you need any help?"),
        "Thumb Up": ("All's good", "Good to hear it's right!"),
        "Thumb Down": ("Not good", "Ohh, sorry to hear that."),
        "Two Fingers": ("I am happy", "Ooo nice to hear you are happy!"),
        "Fist": ("I am ready", "Great, I am ready to come with you!")
    }

        user_msg, bot_reply = meaning_map.get(gesture, ("Unknown", "I didn't understand the gesture."))

        chat_history.append((user_msg, bot_reply))

        event_queue.put("chat")
        return jsonify({"reply": bot_reply})

    elif current_task == "emotion":
        last_emotion = detected_text
        event_queue.put("emotion")
        return jsonify({"emotion": detected_text})



@app.route("/stream")
def stream():
    def event_stream():
        while True:
            msg = event_queue.get()
            yield f"data: {msg}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
