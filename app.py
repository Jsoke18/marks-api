import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
from flask_cors import CORS
import yagmail

load_dotenv()
app = Flask(__name__)
CORS(app)

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('DATABASE_ID')
# Replace with your database ID

APP_SPECIFIC_PASSWORD = os.getenv('PASSWORD')
@app.route('/send_email', methods=['POST'])
def send_email():
    print("Request received:", request.form)  # For debugging

    try:
        # Extract data from form
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Set up yagmail SMTP client
        # Replace with your app-specific password
        yag = yagmail.SMTP('joshsoke@gmail.com', 'rpde xzuz ihmr jqha')

        # Prepare email content
        subject = "New Message from Contact Form"
        content = f"Name: {name}\nEmail: {email}\nMessage: {message}"

        # Send email
        yag.send('joshsoke@gmail.com', subject, content)

        return jsonify({"status": "success", "message": "Email sent successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def query_notion_database(api_key, database_id):
    url = f'https://api.notion.com/v1/databases/{database_id}/query'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data: {response.status_code} - {response.text}")

    return response.json()


@app.route('/images', methods=['GET'])
def get_images():
    try:
        database_entries = query_notion_database(NOTION_API_KEY, DATABASE_ID)
        total_images = 0
        image_urls = []

        for entry in database_entries.get("results", []):
            images = entry.get("properties", {}).get(
                "Images", {}).get("files", [])
            for image in images:
                image_url = image.get("file", {}).get("url")
                if image_url:
                    image_urls.append(image_url)
                    total_images += 1

        return jsonify({"total_images": total_images, "image_urls": image_urls})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
