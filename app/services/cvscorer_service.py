import json
import os
from json import JSONDecodeError
from pathlib import Path

import convertapi

from app.libraries import logger
from app.services.openai_service import GPT4, ChatMessage
from config import CONFIG


class CVScoreError(Exception):
    """Custom exception for CV scoring errors."""
    pass


class CVScorerService:
    """This Class Has to Deal with Everything Processing of our PDF CV to the desired result."""
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
                    'score': {'type': 'string'},
                },
                'required': ['score', 'recommendations'],
                'additionalProperties': False,
            },
        },
    }

    def __init__(self):
        self.text_path = None
        self.gpt4 = GPT4()

    def convert_pdf_to_txt(self, pdf_path: str):
        """Method to Help Us Convert the Downloaded PDF file to a txt file using convert-api."""
        logger.info('Converting our PDF File to a txt File.')
        text_file_name = 'extracted_text.txt'
        self.text_path = os.path.join(CONFIG.DIRECTORIES.OUTPUT, text_file_name)

        try:
            convertapi.api_credentials = CONFIG.ENV_CREDENTIALS.get('CONVERT_API_SECRET')
            convertapi.convert('txt', {
                'File': pdf_path,
                'PageRange': '1-5',
                'EnableOcr': 'true',
                'OcrLanguage': 'automatic',
                'IncludeFormatting': 'false',
                'RemoveHeadersFooters': 'true',
                'RemoveFootnotes': 'true',
                'RemoveTables': 'true'
            }, from_format='pdf').save_files(self.text_path)
            logger.info('File Successfully Converted.')
            return {'message': 'File successfully converted', 'path': str(self.text_path)}, 200

        except convertapi.ApiError as e:
            logger.exception(f"ConvertAPI error: {str(e)}")
            return {'error': f'API error: {str(e)}'}, 503

        except Exception as e:
            logger.exception(f"Unexpected error during PDF conversion: {str(e)}")
            return {'error': 'Internal server error'}, 500

    @staticmethod
    def _load_prompt(prompt_file: str) -> str:
        try:
            with open(Path().cwd() / 'prompts' / prompt_file, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            raise CVScoreError(f'Prompt file not found: {prompt_file}')

    def _prepare_messages(self, cv_text: str) -> list[ChatMessage]:
        """Prepare the message list for GPT."""
        system_prompt = self._load_prompt('system_prompt.txt')
        input_prompt = self._load_prompt('input_prompt.txt').format(input_string=cv_text)

        return [
            ChatMessage(role='system', text=system_prompt),
            ChatMessage(role='user', text=input_prompt)
        ]

    @staticmethod
    def _parse_gpt_response(response_text: str) -> dict:
        """Parse and validate GPT response."""
        try:
            # Clean up potential JSON formatting issues
            cleaned_response = response_text.replace('""""', '""')
            return json.loads(cleaned_response)
        except JSONDecodeError as e:
            logger.error(f'Failed to parse GPT response: {response_text}')
            raise CVScoreError('Invalid JSON response from GPT') from e

    def get_cvscore_from_gpt(self):
        """From our txt representation of the CV, get the score and recommended improvements by passing it to GPT."""
        logger.info('Initiating CV scoring with GPT-4')
        try:
            with open(self.text_path, 'r') as file:
                cv_text = file.read()

            messages = self._prepare_messages(cv_text)
            response = self.gpt4.chat_completion_request(
                messages=messages,
                output_structure=self.GPT_JSON_FORMAT
            )

            response_json = self._parse_gpt_response(
                response.choices[0].message.content
            )

            logger.info('Successfully retrieved CV score from GPT')
            return response_json, 200

        except FileNotFoundError:
            logger.error(f'CV text file not found: {self.text_path}')
            return {'error': 'CV text file not found'}, 404

        except CVScoreError as e:
            logger.error(f'Error processing CV score: {str(e)}')
            return {'error': str(e)}, 400

        except Exception as e:
            logger.exception(f'Unexpected error during CV scoring: {str(e)}')
            return {'error': 'Internal server error'}, 500
