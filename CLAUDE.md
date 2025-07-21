# Chain of Search Demo - Project Summary

## Project Structure
This is a Python chatbot project that demonstrates OpenAI API integration with a custom configuration and built-in documentation search functionality.

### Key Files:
- `search.py` - Main chatbot application with integrated search tool
- `parameters.json` - Model configuration and search settings
- `prompts/system.md` - System prompt for the chatbot
- `.env` - Contains CBORG_API_KEY and CBORG_API_URL for API access
- `requirements.txt` - Python dependencies (openai, python-dotenv)
- `nersc-docs/` - Documentation repository for search functionality

## Setup Requirements
1. Python virtual environment in `venv/`
2. Dependencies installed via `pip install -r requirements.txt`
3. `.env` file with CBORG_API_KEY and CBORG_API_URL configured
4. NERSC documentation cloned in `nersc-docs/` folder

## Usage
Run `python search.py` to start the interactive chatbot. Type 'quit' to exit.

### Search Tool
The chatbot includes a built-in search tool for querying NERSC documentation:
- **Manual usage**: `/search keyword1, keyword2, ...` 
- **Automatic usage**: LLM can trigger searches by including `/search` in responses
- Searches through files in `nersc-docs/docs` using grep with context
- Returns matching paragraphs with source file paths
- Supports multiple keywords and configurable context lines
- File types: `.md` and `.sh` files
- Results formatted differently for human vs LLM consumption

## Current Configuration (parameters.json)
- **Model**: `openai/o4-mini` 
- **Max tokens**: 4000
- **Temperature**: 0.3
- **Top-p**: 0.9
- **Frequency penalty**: 0.1
- **Presence penalty**: 0.1
- **Docs folder**: `nersc-docs/docs`
- **Search context lines**: 15 (lines before/after matches)

## Features
- Conversation history (keeps last 10 messages for context)
- Automatic search integration for LLM responses
- Custom API endpoint support via environment variables
- Configurable search parameters and model settings
- Error handling for missing files and API failures
- Debug mode support: Use `python search.py -debug` or `./doc.sh -debug` to display LLM thinking, tool call inputs, and outputs

## Development Guidelines
- **Never test code or functionality unless explicitly told to do so by the user**