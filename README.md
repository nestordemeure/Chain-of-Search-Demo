# Chain of Search Demo

A Python chatbot demonstrating OpenAI API integration with document search capabilities. This project uses grep-based keyword search to provide contextual results from documentation files, serving as a simple proof-of-concept for integrating document search into conversational AI.

## Install

```bash
# Setup virtual environment and dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API access (create .env file)
echo "CBORG_API_KEY=your_api_key" > .env
echo "CBORG_API_URL=your_api_endpoint" >> .env

# Initialize documentation submodule
git submodule update --init --recursive
```

## Usage

```bash
# Run the chatbot
./doc.sh

# Or manually
source venv/bin/activate
python search.py
```

Use the `-debug` flag to display LLM thinking, tool call inputs, and outputs for development purposes.