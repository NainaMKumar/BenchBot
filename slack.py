from flask import Flask
from slackeventsapi import SlackEventAdapter
import openai
import re
import requests
import os
from flask_ngrok import run_with_ngrok  # Import the run_with_ngrok function
import json

SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
ORGANIZATION_ID = os.getenv('ORGANIZATION_ID')

# Create a Flask app instance
app = Flask(__name__, static_folder=None)
run_with_ngrok(app)  # Connect the Flask app to ngrok

@app.route('/')
def text():
    return "Running on Flask"

# Initialize the SlackEventAdapter with the Flask app
slack_event_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, '/slack/events', app
)

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY
openai.organization = ORGANIZATION_ID

# Function to get a response from GPT using OpenAI API
def get_gpt_response(text, file_path):
    with open(file_path, 'r') as file:
        engineer_data = json.load(file)
    
    prompt = f"Engineer data: {engineer_data}\n\nUser prompt: {text}\n\nResponse:"

    response = openai.Completion.create(
        model= "text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        temperature = 0.7
    )
    return response.choices[0].text.strip()

@slack_event_adapter.on("app_mention")

def handle_app_mention(event_data):
    print("listening")
    event = event_data["event"]
    channel_id = event["channel"]
    text = event.get("text")

    #Remove the mention of the bot from the text
    bot_mention = f"<@{event.get('bot_id')}>"
    text_without_mention = re.sub(bot_mention, "", text).strip()

    # Get response from GPT
    response = get_gpt_response(text, "data.json")
    print(response)

    # Post the response back to the Slack channel
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {SLACK_APP_TOKEN}'
    }
    payload = {
        'channel': channel_id,
        'text': response
    }

    return requests.post('https://slack.com/api/chat.postMessage', json=payload, headers=headers)

app.route('/')

def message(): 
    return "Hi Slackbot"

# Start the server on port 3000
if __name__ == "__main__":
    app.run()

