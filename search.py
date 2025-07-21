#!/usr/bin/env python3
import json
import os
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
    
    print("Chatbot initialized. Type 'quit' to exit.")
    print("-" * 40)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            response = client.chat.completions.create(
                model=params['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=params['max_tokens'],
                temperature=params['temperature'],
                top_p=params['top_p'],
                frequency_penalty=params['frequency_penalty'],
                presence_penalty=params['presence_penalty']
            )
            
            print(f"\nBot: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()