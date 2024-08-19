import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
from flask_cors import CORS
from functools import lru_cache

load_dotenv()
app = Flask(__name__)
CORS(app)

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('DATABASE_ID')
IMAGES_PER_PAGE = 15
INITIAL_IMAGES = IMAGES_PER_PAGE // 2  # Load half the images initially

# Dictionary to store processed entry IDs and cursors for each session
sessions = {}

@lru_cache(maxsize=128)
def query_notion_database(api_key, database_id, start_cursor=None):
    url = f'https://api.notion.com/v1/databases/{database_id}/query'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    body = {
        "page_size": 100,  # Fetch more to account for potential duplicates
        "sorts": [{"property": "Created time", "direction": "descending"}]  # Sort by creation time, newest first
    }
    if start_cursor:
        body["start_cursor"] = start_cursor
    
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")
    
    return response.json()

def get_title_safely(entry):
    try:
        return entry.get("properties", {}).get("Title", {}).get("title", [{}])[0].get("plain_text", "No Title")
    except IndexError:
        return "No Title"

@app.route('/images', methods=['GET'])
def get_images():
    try:
        session_id = request.args.get('session_id')
        is_initial = request.args.get('initial', 'false').lower() == 'true'
        
        if not session_id or session_id == 'null':
            return jsonify({"error": "Invalid session ID"}), 400
        
        if session_id not in sessions:
            sessions[session_id] = {'processed_ids': set(), 'current_cursor': None}
        
        session = sessions[session_id]
        start_cursor = session['current_cursor']
        
        print(f"Received request with session_id: {session_id}, initial: {is_initial}, start_cursor: {start_cursor}")
        
        database_entries = query_notion_database(NOTION_API_KEY, DATABASE_ID, start_cursor)
        print(f"Fetched {len(database_entries.get('results', []))} entries from Notion")
        
        image_data = []
        images_to_fetch = INITIAL_IMAGES if is_initial else IMAGES_PER_PAGE
        for entry in database_entries.get("results", []):
            entry_id = entry.get("id")
            if entry_id not in session['processed_ids']:
                title = get_title_safely(entry)
                images = entry.get("properties", {}).get("Images", {}).get("files", [])
                if images:
                    image_url = images[0].get("file", {}).get("url")
                    if image_url:
                        image_data.append({
                            "id": entry_id,
                            "title": title,
                            "url": image_url
                        })
                        session['processed_ids'].add(entry_id)
                        print(f"ID: {entry_id}, Title: {title}, Image URL: {image_url}")
                        if len(image_data) == images_to_fetch:
                            break
        
        session['current_cursor'] = database_entries.get("next_cursor")
        has_more = database_entries.get("has_more", False) or len(image_data) == images_to_fetch
        
        print(f"Sending response with {len(image_data)} unique images, next_cursor: {session['current_cursor']}, has_more: {has_more}")
        
        return jsonify({
            "image_data": image_data,
            "next_cursor": session['current_cursor'],
            "has_more": has_more
        })
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)