from flask import Flask, request, jsonify, render_template, Response
import requests
import json
import os

app = Flask(__name__)

# Get API key safely
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
print("KEY EXISTS:", bool(GROQ_API_KEY)) 

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    question = data.get("question", "")

    print("QUESTION RECEIVED:", question)

    def generate():

        # Check API key
        if not GROQ_API_KEY:
            yield "ERROR: GROQ_API_KEY is missing in Hugging Face Secrets."
            return

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "user", "content": question}
                    ],
                    "stream": True
                },
                stream=True
            )

            print("STATUS CODE:", response.status_code)

            # If API fails
            if response.status_code != 200:
                yield f"API ERROR: {response.text}"
                return

            # Stream response
            for line in response.iter_lines():

                if line:

                    line = line.decode("utf-8")

                    if line.startswith("data: "):

                        data_str = line[6:]

                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)

                            word = chunk["choices"][0]["delta"].get("content", "")

                            if word:
                                yield word

                        except Exception as e:
                            print("JSON ERROR:", e)

        except Exception as e:
            print("REQUEST ERROR:", e)
            yield f"SERVER ERROR: {str(e)}"

    return Response(generate(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)