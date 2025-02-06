import logging

from openai import OpenAI
from openai.error import APIConnectionError
from retry import retry

from config import CONFIG


class ChatMessage:
    """Represents a message exchanged in a chat conversation."""

    def __init__(self, role: str, text: str):
        self.role = role
        self.text = text

    def __repr__(self):
        """
        Returns a string representation of the ChatMessage.

        Returns:
            str: String representation of the ChatMessage.
        """
        return f'{self.role}: {self.text}'

    def to_dict(self):
        """
        Converts the ChatMessage to a dictionary.

        Returns:
            dict: Dictionary representation of the ChatMessage.
        """
        return {
            'role': self.role,
            'content': self.text,
        }


class GPT4:
    """Class to interact with GPT4."""

    def __init__(self, engine='gpt-4o'):
        self.client = OpenAI(api_key=CONFIG.ENV_CREDENTIALS.get('OPEN_AI_API_KEY'))
        self.engine = engine

    @retry(APIConnectionError, tries=5, delay=2, backoff=2, logger=logging.getLogger(__name__))
    def chat_completion_request(self, messages: list, output_structure: dict):
        """Sends a request to the OpenAI API to complete a chat message."""
        response = self.client.chat.completions.create(
            model=self.engine,
            messages=[message.to_dict() for message in messages],
            max_tokens=512,
            response_format=output_structure,
        )
        return response

