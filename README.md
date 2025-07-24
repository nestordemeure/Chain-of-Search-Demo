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
- etc.

## TODO

* confirm the model is functional
* Add `grep` tool
* Add `read` tool
* update system prompt