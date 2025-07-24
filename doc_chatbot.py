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
        self.tools: List[Callable] = [self.grep]
    
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
    
    def grep(self, keywords: List[str], nb_lines_outputs: Optional[int] = None, nb_outputs: Optional[int] = None) -> str:
        """
        Search for keywords in documentation files using grep.
        
        Args:
            keywords: List of keywords to search for
            nb_lines_outputs: Number of lines to show around each match (default from config)
            nb_outputs: Maximum number of matches to return (default from config)
        
        Returns:
            String containing grep results with file paths and line numbers
        """
        # Use config defaults if not specified
        if nb_lines_outputs is None:
            nb_lines_outputs = self.config['grep']['default_nb_lines_outputs']
        if nb_outputs is None:
            nb_outputs = self.config['grep']['default_nb_outputs']
        
        # Get docs folder path
        docs_folder = self.config['docs_folder']
        
        # Build grep command
        cmd = [
            'grep',
            '-r',  # recursive search
            '-n',  # show line numbers
            '-H',  # show filenames
            f'-A{nb_lines_outputs-1}',  # lines after (total will be nb_lines_outputs)
            f'-m{nb_outputs}',  # max matches per file
            '--color=never',  # disable color output
        ]
        
        # Add search pattern - join keywords with OR
        pattern = '|'.join(keywords)
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
            return "No matches found."
        
        # Process output to make paths relative to docs folder
        output = result.stdout.strip()
        if output:
            # Simple string substitution to make paths relative
            docs_folder_with_slash = docs_folder.rstrip('/') + '/'
            output = output.replace(docs_folder_with_slash, '')
        
        return output if output else "No matches found."
    
    def _wrap_tools(self, tools: List[Callable]) -> List[Callable]:
        """Wrap all tools to add display functionality"""
        def create_wrapper(tool_func):
            def wrapper(*args, **kwargs):
                # Get tool name
                tool_name = getattr(tool_func, '__name__', 'Unknown Tool')
                
                # Combine args and kwargs for display
                all_inputs = {}
                if args:
                    all_inputs['args'] = args
                if kwargs:
                    all_inputs.update(kwargs)
                
                # Display tool call
                inputs_text = json.dumps(all_inputs, indent=2) if all_inputs else "No inputs"
                self.console.print(
                    Panel(
                        f"[bold yellow]Tool:[/bold yellow] {tool_name}\n[bold cyan]Inputs:[/bold cyan]\n{inputs_text}",
                        title="🔧 Tool Call",
                        border_style="yellow",
                        padding=(0, 1)
                    )
                )
                
                # Execute the tool
                result = tool_func(*args, **kwargs)
                
                # Display output if debug mode
                if self.config.get('debug', False):
                    self.console.print(
                        Panel(
                            f"[bold green]Output:[/bold green]\n{str(result)}",
                            title=f"🔧 Tool Output: {tool_name}",
                            border_style="green",
                            padding=(0, 1)
                        )
                    )
                
                return result
            
            # Preserve original function attributes
            wrapper.__name__ = getattr(tool_func, '__name__', 'wrapped_tool')
            wrapper.__doc__ = getattr(tool_func, '__doc__', None)
            return wrapper
        
        return [create_wrapper(tool) for tool in tools]
    
    def chat(self, initial_message: Optional[str] = None):
        """Start the chat interaction"""
        # Wrap tools for display
        wrapped_tools = self._wrap_tools(self.tools)
        conversation = self.model.conversation(tools=wrapped_tools)
        
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
                response = conversation.prompt(
                    user_input,
                    system=self.system_prompt
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