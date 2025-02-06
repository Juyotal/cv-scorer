import os
from datetime import timedelta

from flask import Flask, render_template, request
from flask_cors import CORS
from flask_talisman import Talisman

from app.libraries import logger
from app.services.cvscorer_service import CVScorerService
from app.services.file_uploader_service import FileUploader
from config import CONFIG
from flask_session import Session

app = Flask(__name__)

CORS(app, resources={r'/api/*': {'origins': ['http://localhost:5000']}})

Talisman(app, content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com'],
        'style-src': ["'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com'],
    }
)

app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR='./flask_session/',
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
)
Session(app)

scorer_service = CVScorerService()
file_uploader_service = FileUploader(request)


def cleanup_files():
    """Method to Help us clear our Output Directory."""
    try:
        output_dir = CONFIG.DIRECTORIES.OUTPUT

        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        logger.exception(f'Failed to clear the output Directory: {e}')


def create_run():
    app.run(debug=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    return file_uploader_service.upload_file()


@app.route('/analyze', methods=['POST'])
def analyze_cv():
    data = request.json
    file_path = data.get('file_path')

    convert_response = scorer_service.convert_pdf_to_txt(file_path)
    if 'error' in convert_response[0]:
        cleanup_files()
        return convert_response

    score_result = scorer_service.get_cvscore_from_gpt()
    cleanup_files()
    return score_result
