"""
AI聊天模块
用于与Gemini AI进行聊天
"""
import google.generativeai as genai
import os
from rich.console import Console
from rich.markdown import Markdown
from config import GEMINI_API_KEY

# 创建Rich控制台实例，用于美化输出
console = Console()

# 配置API密钥
genai.configure(api_key=GEMINI_API_KEY)

# 初始化模型
model = genai.GenerativeModel('gemini-2.0-flash')

def print_markdown(text):
    """
    使用Rich打印markdown格式的文本
    
    参数:
    text (str): markdown格式的文本
    """
    md = Markdown(text)
    console.print(md)

def chat_with_gemini_api(message):
    """
    与Gemini AI进行单次对话，用于API调用
    
    参数:
    message (str): 用户消息
    
    返回:
    str: Gemini的响应文本
    """
    try:
        # 创建聊天会话并发送消息
        chat = model.start_chat(history=[])
        response = chat.send_message(message)
        return response.text
    except Exception as e:
        raise Exception(f"AI聊天出错: {str(e)}")

def chat_with_gemini():
    """
    与Gemini AI进行交互式聊天
    """
    # 创建聊天会话
    chat = model.start_chat(history=[])
    
    console.print("\n[bold green]欢迎使用Gemini聊天程序![/bold green]")
    console.print("[yellow]输入'quit'或'exit'结束对话[/yellow]\n")
    
    while True:
        # 获取用户输入
        user_input = input("[bold blue]你: [/bold blue]")
        
        # 检查是否退出
        if user_input.lower() in ['quit', 'exit']:
            console.print("\n[bold green]感谢使用，再见！[/bold green]")
            break
            
        try:
            # 发送消息给Gemini并获取响应
            response = chat.send_message(user_input)
            
            # 打印Gemini的响应
            console.print("\n[bold purple]Gemini: [/bold purple]")
            print_markdown(response.text)
            console.print("\n" + "-"*50 + "\n")
            
        except Exception as e:
            console.print(f"\n[bold red]发生错误: {str(e)}[/bold red]\n")

# 测试函数
def run_chat():
    """运行聊天程序"""
    try:
        chat_with_gemini()
    except KeyboardInterrupt:
        console.print("\n\n[bold green]程序已被用户中断，再见！[/bold green]") 