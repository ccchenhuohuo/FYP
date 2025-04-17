"""
AI chat module
"""
import google.generativeai as genai
import os
from rich.console import Console
from rich.markdown import Markdown
from config import GEMINI_API_KEY

# create a rich console instance for beautiful output
console = Console()

# configure the API key
genai.configure(api_key=GEMINI_API_KEY)

# initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

def print_markdown(text):
    """
    Use Rich to print markdown formatted text
    
    Parameters:
    text (str): markdown formatted text
    """
    md = Markdown(text)
    console.print(md)

def chat_with_gemini_api(message):
    """
    Chat with Gemini AI for a single conversation, for API calls
    
    Parameters:
    message (str): user message
    
    Returns:
    str: Gemini's response text
    """
    try:
        print(f"Processing AI request, message: {message[:50]}...")
        
        # 创建生成参数，提高输出质量和一致性
        generation_config = {
            "temperature": 0.7,     # 较低的temperature提高输出确定性
            "top_p": 0.8,           # 控制生成的创造性
            "top_k": 40,            # 提高输出的多样性
            "max_output_tokens": 2048, # 允许足够长的回复
        }
        
        # 设置安全设置
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # create a chat session and send a message with configuration
        chat = model.start_chat(history=[])
        print("chat session created")
        
        response = chat.send_message(
            message,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print("received AI response")
        
        # 处理响应文本，移除可能的markdown代码块标记
        response_text = response.text
        response_text = response_text.replace("```html", "").replace("```", "")
        
        return response_text
    except Exception as e:
        import traceback
        print(f"AI chat error: {str(e)}")
        traceback.print_exc()
        raise Exception(f"AI chat error: {str(e)}")

def chat_with_gemini():
    """
    Interact with Gemini AI in an interactive chat
    """
    # create a chat session
    chat = model.start_chat(history=[])
    
    console.print("\n[bold green]Welcome to the Gemini chat program![/bold green]")
    console.print("[yellow]Enter 'quit' or 'exit' to end the conversation[/yellow]\n")
    
    while True:
        # get user input
        user_input = input("[bold blue]You: [/bold blue]")
        
        # check if the user wants to quit
        if user_input.lower() in ['quit', 'exit']:
            console.print("\n[bold green]Thank you for using, goodbye![/bold green]")
            break
            
        try:
            # send a message to Gemini and get the response
            response = chat.send_message(user_input)
            
            # print the response from Gemini
            console.print("\n[bold purple]Gemini: [/bold purple]")
            print_markdown(response.text)
            console.print("\n" + "-"*50 + "\n")
            
        except Exception as e:
            console.print(f"\n[bold red]An error occurred: {str(e)}[/bold red]\n")

# test function
def run_chat():
    """Run the chat program"""
    try:
        chat_with_gemini()
    except KeyboardInterrupt:
        console.print("\n\n[bold green]The program has been interrupted by the user, goodbye![/bold green]") 