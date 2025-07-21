#!/usr/bin/env python3
import json
import os
import subprocess
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

def load_system_prompt():
    """Load system prompt from prompts/system.md"""
    with open('prompts/system.md', 'r') as f:
        return f.read().strip()

def load_parameters():
    """Load model parameters from parameters.json"""
    with open('parameters.json', 'r') as f:
        return json.load(f)

def search_docs(keywords, docs_folder, context_lines=3):
    """Search for keywords in docs folder using grep and return paragraphs with sources"""
    if not os.path.exists(docs_folder):
        return f"Error: docs folder '{docs_folder}' not found"
    
    results = []
    
    for keyword in keywords:
        try:
            cmd = [
                'grep', '-r', '-i', '-n', 
                f'-A{context_lines}', f'-B{context_lines}',
                '--include=*.md', '--include=*.sh',
                keyword, docs_folder
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                current_file = None
                current_matches = []
                
                for line in lines:
                    if line == '--':
                        if current_file and current_matches:
                            results.append({
                                'keyword': keyword,
                                'file': current_file,
                                'content': '\n'.join(current_matches)
                            })
                        current_file = None
                        current_matches = []
                        continue
                    
                    # Handle both matching lines (with :) and context lines (with -)
                    if ':' in line or '-' in line:
                        # Try splitting on : first (matching lines), then - (context lines)
                        if ':' in line and line.count(':') >= 2:
                            parts = line.split(':', 2)
                        elif '-' in line and line.count('-') >= 2:
                            parts = line.split('-', 2)
                        else:
                            continue
                            
                        if len(parts) >= 3:
                            file_path = parts[0]
                            if file_path != current_file:
                                if current_file and current_matches:
                                    results.append({
                                        'keyword': keyword,
                                        'file': current_file,
                                        'content': '\n'.join(current_matches)
                                    })
                                current_file = file_path
                                current_matches = []
                            
                            current_matches.append(parts[2])
                
                if current_file and current_matches:
                    results.append({
                        'keyword': keyword,
                        'file': current_file,
                        'content': '\n'.join(current_matches)
                    })
                        
        except Exception as e:
            results.append({
                'keyword': keyword,
                'error': f"Search error: {str(e)}"
            })
    
    return results

def format_search_results(results, for_llm=False):
    """Format search results for display"""
    if not results:
        return "No results found."
    
    if for_llm:
        # Compact format for LLM consumption
        formatted = []
        for result in results:
            if 'error' in result:
                formatted.append(f"Error searching '{result['keyword']}': {result['error']}")
            else:
                formatted.append(f"[{result['file']}] {result['content']}")
        return '\n\n'.join(formatted)
    else:
        # Verbose format for human users
        formatted = []
        for result in results:
            if 'error' in result:
                formatted.append(f"❌ {result['keyword']}: {result['error']}")
            else:
                formatted.append(f"🔍 Keyword: {result['keyword']}")
                formatted.append(f"📁 Source: {result['file']}")
                formatted.append(f"📄 Content:\n{result['content']}")
                formatted.append("-" * 60)
        
        return '\n'.join(formatted)

def search_docs_tool(keywords_str, docs_folder, context_lines=3):
    """Tool function for OpenAI function calling"""
    keywords = [kw.strip() for kw in keywords_str.split(',')]
    search_results = search_docs(keywords, docs_folder, context_lines)
    return format_search_results(search_results, for_llm=True)

def main():
    # Parse command line arguments
    debug_mode = len(sys.argv) > 1 and sys.argv[1] == '-debug'
    
    load_dotenv()
    
    # Initialize rich console
    console = Console()
    
    api_key = os.getenv('CBORG_API_KEY')
    api_url = os.getenv('CBORG_API_URL')
    
    if not api_key or not api_url:
        console.print("Error: CBORG_API_KEY and CBORG_API_URL must be set in .env file", style="bold red")
        return
    
    client = OpenAI(
        api_key=api_key,
        base_url=api_url
    )
    
    system_prompt = load_system_prompt()
    params = load_parameters()
    
    # Define the search tool for function calling
    tools = [{
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search through NERSC documentation for relevant information",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Comma-separated keywords to search for"
                    }
                },
                "required": ["keywords"]
            }
        }
    }]
    
    conversation_history = []
    
    console.print("Chatbot initialized. Type 'quit' to exit.", style="bold green")
    console.print("Use '/search keyword1, keyword2, ...' to search docs manually", style="cyan")
    if debug_mode:
        console.print("🐛 DEBUG MODE: Tool call thinking and I/O will be displayed", style="bold yellow")
    console.print("-" * 40, style="dim")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            console.print("Goodbye!", style="bold blue")
            break
        
        if not user_input:
            continue
        
        # Manual search command for users
        if user_input.lower().startswith('/search '):
            search_query = user_input[8:].strip()
            if search_query:
                keywords = [kw.strip() for kw in search_query.split(',')]
                docs_folder = params.get('docs_folder', 'docs')
                context_lines = params.get('search_context_lines', 3)
                
                console.print(f"\n🔍 [Manual Search: {', '.join(keywords)}]", style="bold yellow")
                search_results = search_docs(keywords, docs_folder, context_lines)
                formatted_results = format_search_results(search_results, for_llm=False)
                console.print(f"\n{formatted_results}")
            else:
                console.print("\nUsage: /search keyword1, keyword2, ...", style="red")
            continue
        
        try:
            conversation_history.append({"role": "user", "content": user_input})
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history[-10:])
            
            # Track tool calls with detailed information
            tool_call_info = []
            
            if debug_mode:
                console.print("\n🔧 [DEBUG] Sending request to LLM...", style="dim cyan")
                debug_messages = []
                for msg in messages[-3:]:
                    content = msg.get("content") or "(No content)"
                    truncated_content = content[:200] + "..." if len(content) > 200 else content
                    debug_messages.append({"role": msg["role"], "content": truncated_content})
                console.print(Panel(json.dumps(debug_messages, indent=2), title="Request Messages (last 3)", border_style="cyan"))
            
            # First API call with tools
            response = client.chat.completions.create(
                model=params['model'],
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=params['max_tokens'],
                temperature=params['temperature'],
                top_p=params['top_p'],
                frequency_penalty=params['frequency_penalty'],
                presence_penalty=params['presence_penalty']
            )
            
            assistant_message = response.choices[0].message
            
            if debug_mode:
                console.print("\n🧠 [DEBUG] LLM Response received", style="dim cyan")
                if assistant_message.content:
                    console.print(Panel(assistant_message.content, title="LLM Thinking/Content", border_style="green"))
                else:
                    console.print("[DEBUG] No content in response (likely pure tool call)", style="dim")
            
            # Handle tool calls if any
            if assistant_message.tool_calls:
                # Detect if this was likely from thinking/chain-of-thought
                # This happens when there's no visible content but tools are called
                in_thinking = assistant_message.content is None or assistant_message.content.strip() == ""
                
                # Add assistant message with tool calls to conversation
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls]
                })
                
                # Execute tool calls
                for tool_call in assistant_message.tool_calls:
                    if tool_call.function.name == "search_docs":
                        keywords = json.loads(tool_call.function.arguments)["keywords"]
                        tool_call_info.append({
                            'keywords': keywords,
                            'in_thinking': in_thinking
                        })
                        
                        if debug_mode:
                            console.print(f"\n🔍 [DEBUG] Tool Call Input: search_docs", style="dim yellow")
                            console.print(Panel(f"Keywords: {keywords}", title="Tool Input", border_style="yellow"))
                        
                        docs_folder = params.get('docs_folder', 'docs')
                        context_lines = params.get('search_context_lines', 3)
                        
                        result = search_docs_tool(keywords, docs_folder, context_lines)
                        
                        if debug_mode:
                            console.print(f"\n📤 [DEBUG] Tool Call Output:", style="dim yellow")
                            result_preview = result[:500] + "..." if len(result) > 500 else result
                            console.print(Panel(result_preview, title="Tool Output (truncated)", border_style="yellow"))
                        
                        # Add tool result to conversation
                        conversation_history.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id
                        })
                
                # Single API call with tool results - let model decide on further tool calls
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(conversation_history[-10:])
                
                if debug_mode:
                    console.print("\n🔧 [DEBUG] Sending follow-up request with tool results...", style="dim cyan")
                
                final_response = client.chat.completions.create(
                    model=params['model'],
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=params['max_tokens'],
                    temperature=params['temperature'],
                    top_p=params['top_p'],
                    frequency_penalty=params['frequency_penalty'],
                    presence_penalty=params['presence_penalty']
                )
                
                assistant_response = final_response.choices[0].message.content
                
                if debug_mode:
                    console.print("\n💬 [DEBUG] Final LLM Response:", style="dim cyan")
                    console.print(Panel(assistant_response or "(No final response)", title="Final Response", border_style="green"))
                
                # If no response was generated after tool calls, provide a fallback
                if not assistant_response:
                    assistant_response = "I searched for information but couldn't find relevant results or generate a response. Please try rephrasing your question or using more specific terms."
            else:
                assistant_response = assistant_message.content
                # Handle case where direct response is also None
                if not assistant_response:
                    assistant_response = "I'm having trouble generating a response. Please try rephrasing your question."
            
            # Show detailed search status
            if tool_call_info:
                for call_info in tool_call_info:
                    context_type = "🧠 thinking" if call_info['in_thinking'] else "💬 response"
                    keywords_display = call_info['keywords']
                    console.print(f"\n🔧 [Search Tool Called] Keywords: '{keywords_display}' | Context: {context_type}", style="dim")
            else:
                console.print(f"\n[No Search]", style="dim")
            
            console.print("\nBot:", style="bold magenta", end=" ")
            # Render assistant response as markdown
            if assistant_response:
                markdown = Markdown(assistant_response)
                console.print(markdown)
            else:
                console.print("(No response)")
            
            # Add final assistant response to conversation history
            # Ensure we don't add None content to conversation history
            if assistant_response is not None:
                conversation_history.append({"role": "assistant", "content": assistant_response})
            else:
                conversation_history.append({"role": "assistant", "content": "(No response generated)"})
            
        except Exception as e:
            console.print(f"Error: {e}", style="bold red")

if __name__ == "__main__":
    main()