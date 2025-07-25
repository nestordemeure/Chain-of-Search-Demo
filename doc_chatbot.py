#!/usr/bin/env python3
"""
Documentation Chatbot - A simple chatbot to answer questions about documentation
"""
import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Callable, Set
import llm
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from itertools import permutations

def tree(path, prefix="", level=0, ignore_folders=set(), ignore_extensions=set()):
    items = sorted(os.listdir(path))
    result = ""
    
    filtered_items = [item for item in items if not (
        (os.path.isdir(os.path.join(path, item)) and item in ignore_folders) or
        (os.path.isfile(os.path.join(path, item)) and any(item.endswith(ext) for ext in ignore_extensions))
    )]
    
    for i, item in enumerate(filtered_items):
        item_path = os.path.join(path, item)
        is_last = i == len(filtered_items) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = prefix + ("    " if is_last else "│   ")
        
        if os.path.isdir(item_path):
            result += f"{prefix}{current_prefix}{item}/\n"
            result += tree(item_path, next_prefix, level + 1, ignore_folders, ignore_extensions)
        elif item.endswith('.md'):
            result += f"{prefix}{current_prefix}{item}\n"
            with open(item_path, 'r', encoding='utf-8') as f:
                headings = [(line_num, match.group(1), match.group(2)) 
                           for line_num, line in enumerate(f, 1) 
                           if (match := re.match(r'^(#{1,6})\s+(.+)', line.strip()))]
                
                for j, (line_num, hashes, title) in enumerate(headings):
                    level = len(hashes)
                    
                    # Find if this is the last heading at this level or deeper
                    is_last_at_level = True
                    for k in range(j + 1, len(headings)):
                        if len(headings[k][1]) <= level:
                            is_last_at_level = False
                            break
                    
                    # Build the tree structure
                    tree_parts = []
                    for l in range(1, level):
                        # Check if there are more headings at this level or deeper after current
                        has_more_at_level = False
                        for k in range(j + 1, len(headings)):
                            if len(headings[k][1]) == l:
                                has_more_at_level = True
                                break
                            elif len(headings[k][1]) < l:
                                break
                        tree_parts.append("│   " if has_more_at_level else "    ")
                    
                    heading_prefix = "└── " if is_last_at_level else "├── "
                    indent = "".join(tree_parts)
                    result += f"{next_prefix}{indent}{heading_prefix}line {line_num}: {hashes} {title}\n"
        else:
            result += f"{prefix}{current_prefix}{item}\n"
    
    return result

class DocumentationChatbot:
    """A simple chatbot for answering documentation questions"""
    
    def __init__(self):
        # Initialize rich console for pretty output
        self.console = Console()
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize the LLM model
        self.model = self._initialize_model()
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Define tools for the model
        self.tools: List[Callable] = [self.strings_search, self.readline]
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file"""
        config_path = Path(__file__).parent / "config.json"
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _initialize_model(self):
        """Initialize the LLM model"""
        model_name = self.config['model']['name']
        return llm.get_model(model_name)
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from markdown file"""
        prompt_path = Path(__file__).parent / "system_prompt.md"
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def strings_search(self, strings: Set[str]) -> str:
        """
        Returns documentation paragraphs that contain *all* of the given strings, in any order (case independent).

        Args:
            strings (Set[str]): One or more strings to search for.
                                Matching is order-independent—only paragraphs containing all strings, regardless of order, will be returned.

        Returns:
            str: Results showing file paths and matching line numbers.

        Notes:
            For best results, keep the number of strings small even if that means running subsequent searches. The more strings you use, the less likely it is that all will appear together in a given piece of text.
            Also, use shorter, more common substrings (e.g., "install") rather than longer or more specific forms (e.g., "installation") to increase match likelihood.
        """
        # Print tool call start
        nb_lines_outputs = self.config['search']['default_nb_lines_outputs']
        self.console.print(f"🔍 Calling strings_search(strings={strings}, nb_lines_outputs={nb_lines_outputs})")

        # Get docs folder path
        docs_folder = self.config['docs_folder']

        # Build grep command
        cmd = [
            'grep',
            '-r',  # recursive search
            '-i',  # case independent
            '-n',  # show line numbers
            '-H',  # show filenames
            f'-C{nb_lines_outputs}',  # lines per hit
            '--color=never'  # disable color output
        ]

        # Add search patterns
        strings_list = [strings] if isinstance(strings, str) else strings # ensures the input is a list
        keywords_list = [word for string in strings_list for word in string.split()] # split each string and flattens
        # Cover all keyword orderings
        for perm in permutations(keywords_list):
            pattern = '.*'.join(perm) # allow any characters between our keywords
            cmd.append('-e')
            cmd.append(pattern)

        # Add search directory
        cmd.append(docs_folder)
        
        # Run grep command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Propagate grep errors as Python exceptions
        if result.returncode == 2:
            raise RuntimeError(f"Grep error: {result.stderr.strip()}")
        
        if result.returncode == 1:
            return "No matches found, you might want to try fewer strings."
        
        # Process output to make paths relative to docs folder
        output = result.stdout.strip()
        if output:
            # Simple string substitution to make paths relative
            docs_folder_with_slash = docs_folder.rstrip('/') + '/'
            output = output.replace(docs_folder_with_slash, '')
        
        result = output if output else "No matches found, you might want to try fewer strings."
        
        # Print debug output if enabled
        if self.config['debug']:
            debug_md = Markdown(f"**🔍 strings search output:**\n```\n{result}\n```")
            self.console.print(debug_md)
        return result

    def readline(self, file: str, start_line: int, end_line: int) -> str:
        """
        Read specific lines from a file in the documentation folder.
        
        Args:
            file: Path to the file relative to docs_folder
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed, inclusive)
        
        Returns:
            String containing the requested lines with line numbers
        """
        # Print tool call start
        self.console.print(f"📖 Calling readline(file='{file}', start_line={start_line}, end_line={end_line})")
        
        # Tool implementation starts here
        # Ensure we have valid line numbers
        if start_line < 1:
            raise ValueError("start_line must be >= 1")
        if end_line < start_line:
            raise ValueError("end_line must be >= start_line")
        
        # Get docs folder path and construct full file path
        docs_folder = Path(self.config['docs_folder'])
        file_path = docs_folder / file
        
        # Security check: ensure the file is within docs_folder
        try:
            file_path = file_path.resolve()
            docs_folder = docs_folder.resolve()
            if not str(file_path).startswith(str(docs_folder)):
                raise ValueError(f"File path '{file}' is outside the documentation folder")
        except Exception as e:
            raise ValueError(f"Invalid file path '{file}': {e}")
        
        # Check if file exists
        if not file_path.exists():
            result = f"File '{file}' not found in documentation folder."
            if self.config['debug']:
                debug_md = Markdown(f"**📖 readline output:**\n```\n{result}\n```")
                self.console.print(debug_md)
            return result
        
        if not file_path.is_file():
            result = f"'{file}' is not a file."
            if self.config['debug']:
                debug_md = Markdown(f"**📖 readline output:**\n```\n{result}\n```")
                self.console.print(debug_md)
            return result
        
        try:
            # Read the file and extract the requested lines
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check if line numbers are within file bounds
            total_lines = len(lines)
            if start_line > total_lines:
                result = f"File '{file}' only has {total_lines} lines, but requested start_line is {start_line}."
                if self.config['debug']:
                    debug_md = Markdown(f"**📖 readline output:**\n```\n{result}\n```")
                    self.console.print(debug_md)
                return result
            
            # Adjust end_line if it exceeds file length
            actual_end_line = min(end_line, total_lines)
            if end_line > total_lines:
                warning = f" (Note: file only has {total_lines} lines, showing up to line {actual_end_line})"
            else:
                warning = ""
            
            # Extract the requested lines (convert to 0-indexed)
            selected_lines = lines[start_line-1:actual_end_line]
            
            # Format output with line numbers
            result_lines = []
            for i, line in enumerate(selected_lines, start=start_line):
                # Remove trailing newline for cleaner output, but preserve the line structure
                clean_line = line.rstrip('\n')
                result_lines.append(f"{i:4d}: {clean_line}")
            
            result = f"Lines {start_line}-{actual_end_line} from '{file}':{warning}\n" + "\n".join(result_lines)
            
            # Print debug output if enabled
            if self.config['debug']:
                debug_md = Markdown(f"**📖 readline output:**\n```\n{result}\n```")
                self.console.print(debug_md)
            return result
            
        except UnicodeDecodeError:
            result = f"Error: File '{file}' appears to be binary or has encoding issues."
            if self.config['debug']:
                debug_md = Markdown(f"**📖 readline output:**\n```\n{result}\n```")
                self.console.print(debug_md)
            return result
        except Exception as e:
            result = f"Error reading file '{file}': {str(e)}"
            if self.config['debug']:
                debug_md = Markdown(f"**📖 readline output:**\n```\n{result}\n```")
                self.console.print(debug_md)
            return result
    
    def chat(self, initial_message: Optional[str] = None):
        """Start the chat interaction"""
        conversation = self.model.conversation(tools=self.tools)
        
        # Display welcome message
        if not initial_message:
            welcome_md = Markdown(f"**🤖 Documentation Bot:** {self.config['prompts']['welcome_message']}")
            self.console.print(welcome_md)
            self.console.print()
        
        # Get initial user input
        if initial_message:
            user_input = initial_message
            self.console.print(f"[bold blue]You:[/bold blue] {user_input}")
        else:
            user_input = self.console.input("[bold blue]You:[/bold blue] ").strip()
            if not user_input:
                return
        
        while True:
            try:
                # Get response from the model
                response = conversation.chain(
                    user_input,
                    system_fragments=[self.system_prompt],
                )
                
                # Format and display the response using markdown
                self.console.print()
                response_md = Markdown(f"**🤖 Documentation Bot:**\n\n{response.text()}")
                self.console.print(response_md)
                self.console.print()
                
                # Get next user input
                user_input = self.console.input("[bold blue]You:[/bold blue] ").strip()
                if not user_input or user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                    goodbye_md = Markdown(f"**🤖 Documentation Bot:** {self.config['prompts']['goodbye_message']}")
                    self.console.print(goodbye_md)
                    break
                
            except KeyboardInterrupt:
                self.console.print()
                goodbye_md = Markdown(f"**🤖 Documentation Bot:** {self.config['prompts']['goodbye_message']}")
                self.console.print(goodbye_md)
                break

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Documentation Chatbot - Answer questions about documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'question',
        nargs='*',
        help='Question to ask (if not provided, starts interactive mode)'
    )
    
    args = parser.parse_args()
    
    chatbot = DocumentationChatbot()
    
    # Check if called with a question
    if args.question:
        initial_message = " ".join(args.question)
        chatbot.chat(initial_message)
    else:
        chatbot.chat()

if __name__ == "__main__":
    main()