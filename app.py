from flask import Flask, request, jsonify, send_from_directory
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Debug check
print("Loaded API Key:", os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/check', methods=['POST'])
def check_compliance():
    data = request.get_json()
    contract_text = data.get('contract', '')

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a legal compliance assistant. Analyze contracts for regulatory risks."},
            {"role": "user", "content": f"Analyze this contract for compliance issues:\n{contract_text}"}
        ]
    )

    return jsonify({"analysis": response.choices[0].message.content})

if __name__ == '__main__':
    app.run(debug=True)
