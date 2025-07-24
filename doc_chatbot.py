#!/usr/bin/env python3
"""
Documentation Chatbot - A simple chatbot to answer questions about documentation
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Callable
import llm
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

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
        self.tools: List[Callable] = [self.keywords, self.grep, self.readline]
    
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

    def grep(self, pattern: str) -> str:
        """
        Search for a pattern in documentation files using grep with regular expressions.
        
        Args:
            pattern: Grep-compatible regular expression pattern to search for.
                    Common patterns for natural language searches:
                    
                    Basic patterns:
                    - "word" - matches lines containing "word" (case-insensitive)
                    - "jax.*containers" - matches lines with "jax" followed by "containers"
                    - "containers.*jax" - matches lines with "containers" followed by "jax"
                    
                    Word boundaries (exact word matches):
                    - "\\bjax\\b" - matches "jax" as a whole word (not "ajax" or "jaxon")
                    - "\\bcontainers\\b.*\\bjax\\b" - both words as complete words
                    
                    Multiple alternatives:
                    - "(jax|flax|optax)" - matches lines containing any of these words
                    - "container(s)?" - matches "container" or "containers"
                    
                    Line position:
                    - "^Error" - matches lines starting with "Error"
                    - "example$" - matches lines ending with "example"
                    
                    Character classes:
                    - "[Jj]ax" - matches "Jax" or "jax"
                    - "version [0-9]+" - matches "version" followed by numbers
                    
                    Negation (use with caution):
                    - Use grep's -v flag programmatically if you need to exclude patterns
                            
        Returns:
            String containing grep results with file paths and line numbers
            
        Note:
            - Search is case-insensitive by default (-i flag)
            - Searches recursively through all files in docs folder
            - Use double backslashes (\\) in Python strings for single backslash in regex
            - For literal special characters, escape them: "\\." for period, "\\*" for asterisk
        """
        # Print tool call start
        nb_lines_outputs = self.config['grep']['default_nb_lines_outputs']
        self.console.print(f"🔍 Calling grep(pattern='{pattern}', nb_lines_outputs={nb_lines_outputs})")

        # Get docs folder path
        docs_folder = self.config['docs_folder']
        
        # Build grep command
        cmd = [
            'grep',
            '-r',  # recursive search
            '-i',  # case independent
            '-n',  # show line numbers
            '-H',  # show filenames
            f'-C{nb_lines_outputs}',  # lines of context around matches
            '--color=never',  # disable color output
            pattern, # Add the pattern directly as a regexp
            docs_folder, # Add search directory
        ]
        
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
            return "No matches found."
        
        # Process output to make paths relative to docs folder
        output = result.stdout.strip()
        if output:
            # Simple string substitution to make paths relative
            docs_folder_with_slash = docs_folder.rstrip('/') + '/'
            output = output.replace(docs_folder_with_slash, '')
        
        result = output if output else "No matches found."
        
        # Print debug output if enabled
        if self.config['debug']:
            debug_md = Markdown(f"**🔍 grep output:**\n```\n{result}\n```")
            self.console.print(debug_md)
        return result
    
    def keywords(self, keywords: str) -> str:
        """
        Search for keywords in documentation files (using grep under the hood).
        
        Args:
            keywords: Keywords to search for (space-separated if multiple)
        
        Returns:
            String containing grep results with file paths and line numbers
        """
        # Print tool call start
        nb_lines_outputs = self.config['grep']['default_nb_lines_outputs']
        self.console.print(f"🔍 Calling keywords(keywords='{keywords}', nb_lines_outputs={nb_lines_outputs})")

        # Get docs folder path
        docs_folder = self.config['docs_folder']
        
        # Build grep command
        cmd = [
            'grep',
            '-r',  # recursive search
            '-i',  # case independent
            '-n',  # show line numbers
            '-H',  # show filenames
            f'-C{nb_lines_outputs}',  # lines after (total will be nb_lines_outputs)
            '--color=never',  # disable color output
            keywords.replace(" ", ".*"), # Add search pattern
            docs_folder, # Add search directory
        ]
        
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
            return "No matches found."
        
        # Process output to make paths relative to docs folder
        output = result.stdout.strip()
        if output:
            # Simple string substitution to make paths relative
            docs_folder_with_slash = docs_folder.rstrip('/') + '/'
            output = output.replace(docs_folder_with_slash, '')
        
        result = output if output else "No matches found."
        
        # Print debug output if enabled
        if self.config['debug']:
            debug_md = Markdown(f"**🔍 keywords output:**\n```\n{result}\n```")
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