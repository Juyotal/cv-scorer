# CV Scorer

A Python Flask application that analyzes CVs/resumes and provides scoring and improvement recommendations using OpenAI's API.

## Features

- PDF CV upload functionality
- PDF to text conversion
- AI-powered CV analysis
- Score visualization
- Actionable improvement recommendations
- Clean, responsive user interface

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- ConvertAPI account

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cv-scorer.git
cd cv-scorer
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```
OPEN_AI_API_KEY=your_openai_api_key
CONVERT_API_SECRET=your_convertapi_secret
```

## Project Structure

```
cv-scorer/
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── services/
│   │   ├── cvscorer_service.py
|   |   ├── file_uploader_service.py
│   │   └── openai_service.py
│   └── templates/
├── output/
├── config.py
├── requirements.txt
└── run.py
```

## Running the Application

1. Make sure your virtual environment is activated

2. Start the Flask development server:
```bash
python run.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Click the upload button or drag and drop your CV (PDF format)
2. Verify the file is selected (you'll see a green checkmark)
3. Click "Analyze CV"
4. View your score and recommendations
5. Click "Analyze Another CV" to start over

## License

This project is licensed under the MIT License - see the LICENSE file for details.