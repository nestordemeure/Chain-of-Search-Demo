#!/usr/bin/env python3
import json
import os
import subprocess
import re
from openai import OpenAI
from dotenv import load_dotenv

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
    load_dotenv()
    
    api_key = os.getenv('CBORG_API_KEY')
    api_url = os.getenv('CBORG_API_URL')
    
    if not api_key or not api_url:
        print("Error: CBORG_API_KEY and CBORG_API_URL must be set in .env file")
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
    
    print("Chatbot initialized. Type 'quit' to exit.")
    print("Use '/search keyword1, keyword2, ...' to search docs manually")
    print("-" * 40)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
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
                
                print(f"\n🔍 **[Manual Search: {', '.join(keywords)}]**")
                search_results = search_docs(keywords, docs_folder, context_lines)
                formatted_results = format_search_results(search_results, for_llm=False)
                print(f"\n{formatted_results}")
            else:
                print("\nUsage: /search keyword1, keyword2, ...")
            continue
        
        try:
            conversation_history.append({"role": "user", "content": user_input})
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history[-10:])
            
            # Track if any tools were called
            tools_used = []
            
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
            
            # Handle tool calls if any
            if assistant_message.tool_calls:
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
                        tools_used.append(keywords)
                        
                        docs_folder = params.get('docs_folder', 'docs')
                        context_lines = params.get('search_context_lines', 3)
                        
                        result = search_docs_tool(keywords, docs_folder, context_lines)
                        
                        # Add tool result to conversation
                        conversation_history.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id
                        })
                
                # Single API call with tool results - let model decide on further tool calls
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(conversation_history[-10:])
                
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
            else:
                assistant_response = assistant_message.content
            
            # Show search status automatically  
            if tools_used:
                search_status = f"**[Searched: {', '.join(tools_used)}]**"
                print(f"\n{search_status}")
            else:
                print(f"\n**[No Search]**")
            
            print(f"Bot: {assistant_response}")
            
            # Add final assistant response to conversation history
            conversation_history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()