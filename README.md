# Whattsapp_bot
# 📱 WhatsApp Task Bot with Google Tasks & Supabase Integration

This project is a **WhatsApp chatbot** that allows users to:
- 🔐 Authenticate via their Google account
- ✅ Add tasks with due dates
- 📋 View upcoming tasks

Built using **Flask**, **Twilio**, **Google Tasks API**, and **Supabase**.

---

## 🚀 Features

- 🌐 Google OAuth 2.0 authentication
- 📲 WhatsApp integration using Twilio
- 🗂 Task management using Google Tasks API
- ☁️ Supabase used to store user tokens securely
- 📅 Command-based interface for task creation and retrieval

---

## 🛠 Technologies Used

- Python (Flask)
- Twilio (WhatsApp API)
- Supabase (PostgreSQL backend)
- Google Tasks API
- Google OAuth 2.0
- dotenv for managing secrets

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Sujal471/Whattsapp_bot.git
cd Whattsapp_bot
```
### 2. Create and activate Python virtual environment
```bash
python3 -m venv Whattsapp-env
source Whattsapp-env/bin/activate  # On Windows: Whattsapp-env\Scripts\activate
```
###  3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment variables
Create a .env file in the project root containing:
```bash

SUPABASE_API=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```
### 5. Prepare Google API credentials
Create OAuth 2.0 credentials from Google Cloud Console

Download credentials.json and place it in the project root

Update the REDIRECT_URI in the code with your ngrok URL callback (see next step)
### 6. Run the app locally
```bash
python app.py

