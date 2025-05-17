import datetime
import os
from flask import Flask, request, redirect, url_for, render_template_string
from dotenv import load_dotenv
from supabase import create_client, Client
from twilio.twiml.messaging_response import MessagingResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

# Supabase setup
url = os.environ.get("SUPABASE_API")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Google API scope and redirect URI
SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly"
]

REDIRECT_URI = "https://d5d0-103-172-72-14.ngrok-free.app/callback"

def refresh_token_if_expired(token_json, phone_number):
    try:
        creds = Credentials.from_authorized_user_info(eval(token_json), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save new token
            supabase.table('user_info').update({"token": creds.to_json()}).eq("phone_number", phone_number).execute()
        return creds
    except Exception as e:
        print("Error refreshing token:", e)
        return None

@app.route('/hi', methods=['POST'])
def whatsapp_handler():
    incoming_msg = request.form.get('Body')
    response = MessagingResponse()
    msg = response.message()

    if not incoming_msg:
        msg.body("empty")
        return str(response)

    
    phone = request.form.get('From')
    number = phone.split('+')[-1]
    print(f"Received message from: {number}")

        # Check if user exists in Supabase
    user_data = supabase.table('user_info').select('*').eq('phone_number', number).execute()

    if len(user_data.data)==0:
        auth_url = generate_google_auth_url(number)
        print(auth_url)
        msg.body(f"🔐 Please authenticate using this link:\n{auth_url}")
        return str(response)    
    print(user_data.data)
    token_json = user_data.data[0]['token']
    credentials = refresh_token_if_expired(token_json, number)
    if not credentials:
        msg.body("❌ Failed to authenticate. Please try again.")
        return str(response)
    
    if incoming_msg.lower() == "hi":
        msg.body("You're authenticated. You can type:\n- `add task`\n- `list tasks`")
    elif incoming_msg.lower() == "add task":
        msg.body("Please send task details in the format:\n`Title | Description | DD-MM-YYYY HH:MM`")
    elif "|" in incoming_msg:
        parts = incoming_msg.split("|")
        if len(parts) == 3:
            title = parts[0].strip()
            description = parts[1].strip()
            due_str = parts[2].strip()

            result = add_task(credentials, title, description, due_str)
            msg.body(result)
        else:
            msg.body("Invalid format. Please use:\nTitle | Description | DD-MM-YYYY HH:MM")
    elif incoming_msg.lower() == "list tasks":
        result = list_upcoming_tasks(credentials)
        msg.body(result)
    else:
        msg.body("Unknown command. Please type `add task` or `list tasks`.")

    return str(response)


def add_task(creds, title, description, due_str):
    try:
        # Build the service
        service = build("tasks", "v1", credentials=creds)
        tasklist_id = '@default'

        # Convert the input due date string into a datetime object (without considering time zones)
        due_date = datetime.datetime.strptime(due_str, "%d-%m-%Y").date()

        # Store the due date as a string in "yyyy-mm-dd" format
        due_datetime_iso = due_date.strftime("%Y-%m-%dT00:00:00.000Z")

        # Create the task
        task = {
            "title": title,
            "notes": description,
            "due": due_datetime_iso # Store only the date
        }

        # Insert the task into Google Tasks
        service.tasks().insert(tasklist=tasklist_id, body=task).execute()

        return "✅ Task added successfully!"
    except Exception as e:
        print("Error adding task:", e)
        return "❌ Failed to add task. Please check your format."


def list_upcoming_tasks(creds):
    try:
        # Build the service
        service = build("tasks", "v1", credentials=creds)
        tasklist_id = '@default'

        tasks_result = service.tasks().list(tasklist=tasklist_id, showCompleted=False).execute()
        tasks = tasks_result.get('items', [])

        if not tasks:
            return "📭 No upcoming tasks."

        # Current date
        today_date = datetime.datetime.now().date()

        upcoming = []
        for task in tasks:
            if 'due' in task:
                # Parse the due date (we assume it's saved as yyyy-mm-dd)
                due_date_str = task['due']
                due_date = datetime.datetime.fromisoformat(due_date_str).date()

                # Check if the due date is today or in the future
                if due_date >= today_date:
                    upcoming.append(f"📝 *{task['title']}*\n📅 {due_date.strftime('%d-%m-%Y')}\n🧾 {task.get('notes', '')}")

        # Sort tasks by the due date
        upcoming.sort(key=lambda x: x.split("\n")[1])  # Sort based on the date in the task description

        if not upcoming:
            return "📭 No upcoming tasks."

        # Join all the tasks with new lines
        result = "\n\n".join(upcoming)
        return result

    except Exception as e:
        print("Error listing tasks:", e)
        return "❌ Failed to fetch tasks."




def generate_google_auth_url(phone_number: str) -> str:
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    # Embed the phone number in the `state` param
    flow.redirect_uri = REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', state=phone_number)
    return auth_url

@app.route('/callback', methods=['GET'])
def oauth2_callback():
    code = request.args.get('code')
    state = request.args.get('state')

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES,
            redirect_uri="https://d5d0-103-172-72-14.ngrok-free.app/callback"  # ✅ set this!
        )
        flow.fetch_token(code=code)  # ✅ redirect_uri is now already set in the flow
        credentials = flow.credentials

        # Save to Supabase
        supabase.table('user_info').upsert({
            'phone_number': state,
            'token': credentials.to_json()
        }).execute()

        return "Authentication successful! You can now use the bot."

    except Exception as e:
        print("Error during token fetch:", e)
        return "Authentication failed. Please try again."

if __name__ == "__main__":
    app.run(debug=True)