import json
import os
from json import JSONDecodeError
from pathlib import Path

import convertapi

from app.services import logger
from app.services.openai_service import ChatMessage, GPT4
from config import CONFIG

from flask import request
from werkzeug.utils import secure_filename


def get_prompt(prompt_file: str, input_string: str = '') -> str:
    with open(
            Path().cwd() / 'prompts' / prompt_file, 'r', encoding='utf-8'
    ) as file:
        prompt = file.read()

    return prompt.format(input_string=input_string)


class PDFService:
    """This Class Has to Deal with Everything Processing of our PDF CV to the desired result."""
    ALLOWED_EXTENSIONS = {'pdf'}
    GPT_JSON_FORMAT = {
        'type': 'json_schema',
        'json_schema': {
            'name': 'rating_response',
            'strict': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'recommendations': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                    "score": {'type': 'string'},
                },
                'required': ['score', 'recommendations'],
                'additionalProperties': False,
            },
        },
    }

    def __init__(self):
        self.text_path = None
        self.pdf_path = None
        self.gpt4 = GPT4()

    def _allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def upload_file(self):
        """This Method Helps Download the CV to our bucket once it is passed to our UI."""
        if 'cv' not in request.files:
            return {'error': 'No file part'}, 400

        file = request.files['cv']
        if file.filename == '':
            return {'error': 'No selected file'}, 400

        if file and self._allowed_file(file.filename):
            filename = secure_filename(file.filename)
            self.pdf_path = os.path.join(CONFIG.DIRECTORIES.OUTPUT, filename)
            file.save(self.pdf_path)

            return {'message': 'File uploaded successfully', 'path': self.pdf_path}

        return {'error': 'Invalid file type'}, 400

    def convert_pdf_to_txt(self):
        """Method to Help Us Convert the Downloaded PDF file to a txt file using convert-api."""
        convertapi.api_credentials = CONFIG.ENV_CREDENTIALS.get('CONVERT_API_SECRET')
        text_file_name = 'extracted_text.txt'
        self.text_path = os.path.join(CONFIG.DIRECTORIES.OUTPUT, text_file_name)

        try:
            convertapi.convert('txt', {
                'File': self.pdf_path,
                'PageRange': '1-5',
                'EnableOcr': 'true',
                'OcrLanguage': 'automatic',
                'IncludeFormatting': 'false',
                'RemoveHeadersFooters': 'true',
                'RemoveFootnotes': 'true',
                'RemoveTables': 'true'
            }, from_format='pdf').save_files(self.text_path)
        except Exception as e:
            logger.exception(e)
            return {'error': 'Error When Transforming pdf to txt.'}, 400

    def get_cvscore_from_gpt(self):
        """From our txt representation of the CV, get the score and recommended improvements by passing it to GPT."""
        system_prompt = get_prompt('system_prompt.txt')
        with open(self.text_path, "r") as file:
            input_str = file.read()

        input_prompt = get_prompt('input_prompt.txt', input_str)
        messages = [ChatMessage(role='system', text=system_prompt), ChatMessage(role='user', text=input_prompt)]
        response = self.gpt4.chat_completion_request(messages=messages, output_structure=self.GPT_JSON_FORMAT)

        response_text = response.choices[0].message.content
        try:
            response_json = json.loads(response_text.replace('""""', '""'))
        except JSONDecodeError:
            logger.warning("Error processing Json.")
            logger.debug(response_text)
            return {'error': 'Invalid file type'}, 400
        return response_json

