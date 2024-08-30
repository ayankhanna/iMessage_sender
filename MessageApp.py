from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import subprocess
import time
import random
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def send_imessage(phone_number, message):
    formatted_message = message.replace('"', '\\"')
    apple_script = f'''
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{phone_number}" of targetService
        send "{formatted_message}" to targetBuddy
    end tell
    '''
    subprocess.run(['osascript', '-e', apple_script])

def fill_in_message_template(template, placeholders):
    try:
        return template.format(**placeholders)
    except KeyError as e:
        missing_key = e.args[0]
        return f"Error: The placeholder '{missing_key}' is missing from the data."

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            return redirect(url_for('customize_message', filename=file.filename))
    return render_template("upload.html")

@app.route("/customize/<filename>", methods=["GET", "POST"])
def customize_message(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)
    column_names = df.columns.tolist()

    if request.method == "POST":
        message_template = request.form.get('message_template')
        recipients = df.to_dict(orient='records')

        for recipient in recipients:
            placeholders = {col: recipient.get(col, '') for col in column_names}
            filled_message = fill_in_message_template(message_template, placeholders)
            phone_number = recipient.get('phone', '')
            if phone_number:
                print(f"Sending to {phone_number}: {filled_message}")  # Debug print
                send_imessage(phone_number, filled_message)
                rateLimiter = random.randrange(30,100)
                time.sleep(rateLimiter)
        
        return "Messages sent!"
    
    return render_template("customize.html", columns=column_names)

if __name__ == "__main__":
    app.run(debug=True)
