import requests
import firebase_admin
from firebase_admin import credentials, storage, firestore
from flask import Flask, send_file, jsonify, request, url_for
from io import BytesIO
from flask_cors import CORS
import logging
from PIL import Image
from werkzeug.utils import secure_filename
import os
from openai import OpenAI
import logging
import json
import Translate

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


app = Flask(__name__)
CORS(app)

# Root page
# Allowed requests: GET
# returns a basic online page
@app.route("/")
def base():
    logo_url = url_for('static', filename='travelai_logo.png')
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Service Status</title>
        <style>
            body, html {{
                height: 100%;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                font-family: Arial, sans-serif;
                background-color: #FFFFFF; /* Set the background color */
                color: #000000; /* Set text color to white */

            }}
            .content {{
                text-align: center;
            }}
            .logo {{
                width: 256px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            <img src="{logo_url}" alt="Logo" class="logo">
            <h1>All Systems Operational</h1>
        </div>
    </body>
    </html>
    '''

            
# /translate
# Allowed requests: POST
# Required JSON arguments: text (text to translate), source_lang, target_lang (source and target languages)
# Translates the specified text from source_lang to target_lang
# Source_lang is optional, if empty, source language will be automatically decided
# Error codes: 400 (One or more arguments not provided), 500 (JSON parsing or server error)
@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    if(data == None):
        return jsonify({'error': f'JSON data not available'}), 400
    try:
        response = Translate.translate(data["text"], data["source_lang"], data["target_lang"])    
        return response
    except Exception as e:
        logging.error(f"OpenAI request failed: {str(e)}")
        return jsonify({'error': f'OpenAI request failed: {str(e)}'}), 500
    
# /analyze_menu_url
# Allowed requests: POST
# Required JSON arguments: image_url (URL of image to read), source_lang (source language), target_lang (target language)
# Reads the specified menu image, translates and returns menu items in a JSON format
# Error codes: 400 (one or more JSON arguments not provided), 500 (JSON parsing or server error)
@app.route('/analyze_menu_url', methods=['POST'])
def analyze_menu_url():
    # Parse the JSON body for the image URL
    data = request.json
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({'error': 'No image URL provided'}), 400
    target_lang = data.get('target_lang')

    if not target_lang:
        return jsonify({'error': 'No target language provided'}), 400

    # Log the image URL
    logging.info(f"Image URL: {image_url}")
    prompt = f"""
    You are a menu parser. Please return all the menu items translated into {target_lang} in a JSON format with an "items" key. The JSON format should look like this:

    {{
        "items": [
            {{
                "itemName": "Burrito de Pollo",
                "translatedItemName": "Chicken Burrito",
                "price": "$2.99",
                "type": "Burrito"
            }},
            {{
                "itemName": "Quesadilla",
                "translatedItemName": "Quesadilla",
                "price": "$3.50",
                "type": "Appetizer"
            }}
        ]
    }}
    """

    # Send the image URL to OpenAI for analysis
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Replace with the appropriate model
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Read this menu and translate its contents into {target_lang}."},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            response_format={"type": "json_object"}
        )


        # Log the raw response for debugging
        raw_response = response.choices[0].message.content
        print(f"Raw OpenAI response: {raw_response}")

        try:
            # Parse the JSON string into a Python object using json.loads
            content_data = json.loads(raw_response)
            logging.info(f"Parsed content: {content_data}")
            # Return the parsed content with a 'menuItems' key
            return jsonify({'menuItems': content_data})

        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            logging.error(f"Failed to decode JSON from response content: {str(e)}")
            return jsonify({'error': 'Failed to decode JSON from response content', 'menuItems': []}), 500

    except Exception as e:
        # Handle any other exceptions such as request failures
        logging.error(f"OpenAI request failed: {str(e)}")
        return jsonify({'error': f'OpenAI request failed: {str(e)}', 'menuItems': []}), 500

   
if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True, debug=True)
