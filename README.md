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

## Inner Workings

The model autonomously searches documentation by chaining three tools:

- `keywords(keywords: List[str])` - grep-based basic keyword search
- `grep(pattern: str)` - grep-based regex search  
- `readline(file: Path, start_line: int, end_line: int)` - read specific file sections

Unlike classic retrieval, it can refine searches and try alternative keywords by itself if initial results are incomplete or not relevant.

For example, here is an answer to a (terrible) multifaceted, complex question:

```
🤖 Documentation Bot: Hello! I'm here to help you with your NERSC questions. What would you like to know?                                               

You: Which filesystem should I use to store my software? and my datas? and my conda env?

🔍 Calling keywords(keywords='filesystem software', nb_lines_outputs=5)
🔍 Calling keywords(keywords='filesystem data', nb_lines_outputs=5)
🔍 Calling keywords(keywords='filesystem conda environment', nb_lines_outputs=5)
📖 Calling readline(file='development/installing-software/index.md', start_line=7, end_line=17)
📖 Calling readline(file='policies/data-policy/policy.md', start_line=66, end_line=78)
📖 Calling readline(file='development/installing-software/index.md', start_line=18, end_line=25)
📖 Calling readline(file='development/installing-software/index.md', start_line=26, end_line=38)
📖 Calling readline(file='development/installing-software/index.md', start_line=39, end_line=49)
📖 Calling readline(file='filesystems/global-common.md', start_line=1, end_line=20)
📖 Calling readline(file='filesystems/global-common.md', start_line=21, end_line=38)
📖 Calling readline(file='filesystems/global-home.md', start_line=1, end_line=20)
📖 Calling readline(file='filesystems/global-home.md', start_line=21, end_line=40)
📖 Calling readline(file='filesystems/community.md', start_line=1, end_line=20)
📖 Calling readline(file='filesystems/community.md', start_line=21, end_line=40)
📖 Calling readline(file='filesystems/community.md', start_line=41, end_line=60)
📖 Calling readline(file='filesystems/community.md', start_line=61, end_line=75)
🔍 Calling grep(pattern='conda environment filesystem', nb_lines_outputs=5)
🔍 Calling keywords(keywords='conda environment', nb_lines_outputs=5)
📖 Calling readline(file='development/languages/python/nersc-python.md', start_line=35, end_line=55)
📖 Calling readline(file='development/languages/python/nersc-python.md', start_line=56, end_line=75)
🤖 Documentation Bot:                                                                                                                                   

Here is the information about filesystems to store your software, data, and conda environments at NERSC:                                                

 1 Software:                                                                                                                                            
    • When installing software on NERSC file systems, it is recommended to use the /global/common/software/<your NERSC project> directory.              
    • This filesystem is optimized for sharing software and is read-only on the compute nodes.                                                          
    • You can install software in a prefix such as:                                                                                                     
                                                                                                                                                        
       /global/common/software/<your NERSC project>/public/<name>-<version>-<build ID>                                                                  
                                                                                                                                                        
    • Make a symbolic link to a standard name for the installation for seamless deployments.                                                            
    • See more details in the global common file system.                                                                                                
 2 Data:                                                                                                                                                
    • For data, NERSC provides the Community File System (CFS) at /global/cfs/cdirs/<your_project_name>.                                                
    • Community directories are for sharing data among users and collaborators on a project.                                                            
    • It is advised to store important data at multiple sites for disaster recovery.                                                                    
    • See more about the Community filesystem here.                                                                                                     
 3 Conda Environment:                                                                                                                                   
    • It is recommended to install conda environments to your project directory on /global/common/software if they will be used to run parallel         
      applications.                                                                                                                                     
    • Avoid installing conda environments in $HOME because it is not optimized for large-scale I/O and may cause slowdowns.                             
    • Also avoid using $CFS for many-node compute jobs because it is not meant for heavy I/O at scale.                                                  
    • First, load the conda module, then create and activate your environment. For example:                                                             
                                                                                                                                                        
       module load conda                                                                                                                                
       conda create --name myenv python=3.11 numpy                                                                                                      
       conda activate myenv                                                                                                                             
                                                                                                                                                        
    • More details on using conda at NERSC can be found here.                                                                                           

References:                                                                                                                                             

 • Software installation: https://docs.nersc.gov/development/installing-software/index#nersc-file-systems                                               
 • Global Common filesystem: https://docs.nersc.gov/filesystems/global-common                                                                           
 • Community filesystem: https://docs.nersc.gov/filesystems/community                                                                                   
 • Conda environments: https://docs.nersc.gov/development/languages/python/nersc-python#option-2-custom-conda-environment     
```

## TODO

* restrict number of matches in tool outputs
* cut the `grep` tool as it is redundant with keywords?
* have `keywords` search for any ordering of the keywords by converting the space seperated list into a big regexp?