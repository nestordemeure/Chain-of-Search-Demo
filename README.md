# Chain of Search Demo

A Python chatbot demonstrating OpenAI API integration with document search capabilities.

## Overview

This project serves as a proof-of-concept for integrating basic document search functionality into a conversational AI chatbot. The implementation uses simple, reliable tools (grep) to provide keyword-based search across documentation files.

## Features

- **Interactive Chatbot**: OpenAI-compatible API integration with configurable parameters
- **Document Search Tool**: Grep-based keyword search with contextual results
- **NERSC Documentation**: Includes NERSC documentation as a git submodule for testing
- **Configurable Parameters**: JSON-based configuration for model and search settings

## Quick Start

1. **Setup Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Access**:
   Create a `.env` file with:
   ```
   CBORG_API_KEY=your_api_key
   CBORG_API_URL=your_api_endpoint
   ```

3. **Initialize Submodules**:
   ```bash
   git submodule update --init --recursive
   ```

4. **Run the Chatbot**:
   ```bash
   # Option 1: Use the convenience script (updates docs automatically)
   ./doc.sh
   
   # Option 2: Manual approach
   git submodule update --remote nersc-docs  # Update docs
   source venv/bin/activate
   python search.py
   ```

## Search Tool Usage

The chatbot includes a built-in search command:

```
/search keyword1, keyword2, ...
```

**Example**:
```
You: /search NERSC, computing
🔍 Searching for: NERSC, computing
📁 Source: nersc-docs/docs/jobs/policy.md
📄 Content:
NERSC provides high-performance computing resources...
[context lines around matches]
```

## Search Implementation

The search tool is implemented as a **minimal proof-of-concept** using:

- **grep**: Standard Unix text search utility
- **Recursive search**: Searches through `.md` and `.sh` files
- **Context lines**: Configurable paragraph extraction around matches
- **Multiple keywords**: Supports comma-separated search terms
- **Source tracking**: Returns file paths for each match

This approach prioritizes:
- ✅ **Simplicity**: Uses well-tested, standard tools
- ✅ **Reliability**: Minimal dependencies, robust text matching
- ✅ **Transparency**: Clear, understandable search logic
- ✅ **Speed**: Fast grep-based file scanning

## Configuration

Edit `parameters.json` to customize:

```json
{
    "model": "o4-mini",
    "docs_folder": "nersc-docs/docs",
    "search_context_lines": 3,
    "max_tokens": 150,
    "temperature": 0.7
}
```

## Project Structure

```
├── search.py              # Main chatbot application
├── parameters.json        # Configuration settings
├── prompts/system.md      # System prompt
├── requirements.txt       # Python dependencies
├── doc.sh                 # Convenience script to update docs and run chatbot
├── .env                   # API credentials (not tracked)
├── nersc-docs/           # Git submodule with documentation
└── README.md             # This file
```

## Design Philosophy

This implementation demonstrates a pragmatic approach to document search:

- **No complex indexing**: Direct file system search
- **No external dependencies**: Uses standard system tools
- **No preprocessing required**: Works with raw markdown files
- **Human-readable results**: Clear source attribution and context

While more sophisticated search solutions (Elasticsearch, vector databases, etc.) offer advanced features, this proof-of-concept shows that effective document search can be achieved with simple, maintainable tools.

## Future Enhancements

Potential improvements for production use:
- Full-text indexing for large document sets
- Semantic search using embeddings
- Search result ranking and relevance scoring
- Advanced query syntax (phrases, boolean operators)
- Search history and result caching

## TODO

* simplify the hell out of this readme
