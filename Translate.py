from openai import OpenAI
from flask import jsonify
import json
import logging
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Function translate:
# takes raw text data, translates from source_lang to target_lang
# source_lang is optional, if source_lang is undefined system will automatically detect language
# returns string response
# Error codes: 400 (required parameters not set), 500 (JSON parsing or server error)
def translate(text_file, source_lang, target_lang):
    if not text_file:
        return jsonify({'error': 'No text file provided'}), 400
    if not target_lang:
        return jsonify({'error': 'No target language provided'}), 400
    if not source_lang:
        prompt = f"Translate the following prompt into {target_lang}: {text_file}"
    else:
        prompt = f"Translate the following prompt from {source_lang} into {target_lang}: {text_file}"
    message1 = {"role": "system", "content": "You are a system who can translate text into a given language. Your input may have errors made by common text-to-speech software, correct for that. Reply only with your best-guess translation. Add punctuation where it makes sense."}
    message2 = {"role": "user", "content": prompt}
    try:
        translation = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                message1,
                message2
                ],
                temperature=0
            )
        
        raw_response = translation.choices[0].message.content

        print(f"Raw OpenAI response: {raw_response}")
        return jsonify({"result":raw_response})
    except Exception as e:
        logging.error(f"OpenAI request failed: {str(e)}")
        return jsonify({'error': f'OpenAI request failed: {str(e)}'}), 500
    

