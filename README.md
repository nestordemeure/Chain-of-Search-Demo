# Chain of Search Demo

A Python chatbot demonstrating tool-based search capabilities.

## Install

```bash
# Setup virtual environment and dependencies
python -m venv venv
source venv/bin/activate
pip install llm rich

# Initialize documentation submodule
git submodule update --init --recursive
```

## CBORG Setup

You can configure llm to use CBORG as follows, adding our model of choice (here `openai/o4-mini`, check the [CBORG Models page](https://cborg.lbl.gov/models/) for a list of models currently available with tool use) to its configuration file (do not forget to also set it in [`config.json`](./config.json)):

```sh
# Load the env
source venv/bin/activate

# Register your CBORG API key
llm keys set cborg

# Locate the LLM configuration file
LLM_DIR=$(dirname "$(llm logs path)")
CONFIG_FILE="$LLM_DIR/extra-openai-models.yaml"
touch $CONFIG_FILE

# Create a local shortcut to the config file for ease of use
ln -s "$CONFIG_FILE" llm_models.yaml

# Write our model configuration to the YAML file
# Note the use of the (here openai) pass-through in the url to enable tool use
cat <<EOF > "$CONFIG_FILE"
- model_id: cborg-o4-mini
  model_name: openai/o4-mini
  api_base: "https://api.cborg.lbl.gov"
  api_key_name: cborg
  supports_tools: True
  supports_schema: True
EOF

# Check that we did add our model to the list
llm models
```

## Usage

```bash
# Run the chatbot interactively
./doc.sh

# Ask a question directly
./doc.sh "how do i run a ssh command?"

# Or manually
source venv/bin/activate
python doc_chatbot.py
python doc_chatbot.py "your question here"
```

Edit [`config.json`](./config.json) to:
- Change the model in use (set `model.name`)
- Toggle debug mode (`debug: true/false`)
- Configure documentation folder path (`docs_folder`)
- Pass the documentation structure to the LLM (`include_folder_structure: true/false`)
- etc.

## Inner Workings

The model autonomously searches documentation by chaining three tools:

- `strings_search(strings: Set[str])` - grep-based basic string search
- `readline(file: Path, start_line: int, end_line: int)` - read specific file sections

Unlike classic retrieval, it can refine searches and try alternative keywords by itself if initial results are incomplete or not relevant.
For example, a complex user question like the one below triggers a series of string searches and file reads to gather relevant documentation:

```
🤖 Documentation Bot: Hello! I'm here to help you with your NERSC questions. What would you like to know?                                               

You: How can I install JAX with a container then work inside it with VScode?

🔍 Calling strings_search(strings=['jax', 'container', 'vscode'], nb_lines_outputs=5)
🔍 Calling strings_search(strings=['container', 'vscode'], nb_lines_outputs=5)
🔍 Calling strings_search(strings=['jax', 'container'], nb_lines_outputs=5)
📖 Calling readline(file='development/languages/python/using-python-perlmutter.md', start_line=250, end_line=310)
📖 Calling readline(file='development/containers/shifter/faq-troubleshooting.md', start_line=420, end_line=440) 
```

## TODO

* restrict number of matches in tool outputs
