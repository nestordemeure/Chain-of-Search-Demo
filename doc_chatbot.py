#!/usr/bin/env python3
"""
Documentation Chatbot - A simple chatbot to answer questions about documentation
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Callable
import llm
from rich.console import Console
from rich.markdown import Markdown

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
        
        # Define tools for the model (empty for now)
        self.tools: List[Callable] = []
    
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