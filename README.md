# EON Bill Reader

A simple AI-powered chatbot that can analyze and explain energy bills from EON.

## Features

- PDF bill text extraction
- Bill summary generation
- Question answering about specific bill details
- Simple Streamlit web interface

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Set up your OpenAI API key:
   - Option 1: Add your API key to the `.env` file

## Usage

Run the application:
```bash
cd src
python -m streamlit run main.py
```

The web interface will allow you to:
- View a preview of the extracted bill text
- Get a full summary of the bill
- Ask specific questions about the bill

## Project Structure

- `src/data/` - Contains the sample EON bill PDF
- `src/main.py` - Main application code
- `src/test_extractors` - Table extraction options testing
- `.env` - Environment variables (OpenAI API key)

