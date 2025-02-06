import os
from datetime import timedelta

from app.services.pdf_service import PDFService
from config import CONFIG
from flask_session import Session
from flask_talisman import Talisman
from flask import Flask, render_template
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5000"]}})

Talisman(app, content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com'],
        'style-src': ["'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com'],
    }
)

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
Session(app)

pdf_service = PDFService()


def create_run():
    app.run(debug=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    return pdf_service.upload_file()


@app.route('/analyze', methods=['POST'])
def analyze_cv():
    pdf_service.convert_pdf_to_txt()
    return pdf_service.get_cvscore_from_gpt()


@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    try:
        output_dir = CONFIG.DIRECTORIES.OUTPUT

        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        return {'message': 'Cleanup successful'}, 200
    except Exception as e:
        return {'error': str(e)}, 500
