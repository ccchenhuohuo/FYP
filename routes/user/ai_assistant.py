"""
用户AI助手相关路由
包含AI智能助手页面和对话API
"""
from flask import render_template, jsonify, request
from flask_login import login_required
from utils.chat_ai import chat_with_gemini_api
import traceback

from . import user_bp

@user_bp.route('/ai_assistant')
@login_required
def ai_assistant_page():
    """AI智能助手页面"""
    return render_template('user/ai_assistant.html')

@user_bp.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    """
    AI助手聊天接口
    
    请求体:
    {
        "message": "用户输入的消息"
    }
    
    返回:
    {
        "response": "AI助手的回复"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
            
        # 使用utils/chat_ai.py中的功能与Gemini AI交互
        response_text = chat_with_gemini_api(user_message)
        
        return jsonify({
            'response': response_text
        })
    except Exception as e:
        # 打印详细的错误信息到控制台
        print(f"AI聊天API错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'AI交互出错: {str(e)}'}), 500 