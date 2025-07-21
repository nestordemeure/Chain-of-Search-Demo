# Chain of Search Demo - Project Summary

## Project Structure
This is a Python chatbot project that demonstrates OpenAI API integration with custom configuration.

### Key Files:
- `search.py` - Main chatbot application
- `parameters.json` - Model configuration (currently set to "o4-mini")
- `prompts/system.md` - System prompt for the chatbot
- `.env` - Contains CBORG_API_KEY and CBORG_API_URL for API access
- `requirements.txt` - Python dependencies including openai and python-dotenv

## Setup Requirements
1. Python virtual environment in `venv/`
2. Dependencies installed via `pip install -r requirements.txt`
3. `.env` file with CBORG_API_KEY and CBORG_API_URL configured

## Usage
Run `python search.py` to start the interactive chatbot. Type 'quit' to exit.

## Configuration
- Model: o4-mini (configurable in parameters.json)
- Uses custom API endpoint instead of standard OpenAI
- System prompt loaded from external markdown file
- All key parameters (temperature, max_tokens, etc.) configurable via JSON