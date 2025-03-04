document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const clearButton = document.getElementById('clear-button');
    let isProcessing = false;

    // 添加消息到聊天界面
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
        
        // 如果是AI消息，支持markdown格式
        if (!isUser) {
            // 这里可以添加markdown解析库，暂时直接显示文本
            messageDiv.style.whiteSpace = 'pre-wrap';
        }
        
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 添加加载动画
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading message';
        loadingDiv.id = 'loading-indicator';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 移除加载动画
    function removeLoadingIndicator() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    // 清空聊天记录
    function clearChat() {
        if (isProcessing) {
            alert('请等待当前消息处理完成');
            return;
        }
        
        if (confirm('确定要清空所有聊天记录吗？')) {
            chatMessages.innerHTML = '';
        }
    }

    // 处理表单提交
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (isProcessing) {
            alert('请等待上一条消息处理完成');
            return;
        }
        
        const message = messageInput.value.trim();
        if (!message) return;

        // 显示用户消息
        addMessage(message, true);
        messageInput.value = '';
        messageInput.disabled = true;
        isProcessing = true;

        try {
            // 添加加载动画
            addLoadingIndicator();

            // 发送消息到服务器
            const response = await fetch('/user/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // 移除加载动画
            removeLoadingIndicator();
            
            if (response.ok) {
                // 显示AI回复
                addMessage(data.response);
            } else {
                // 显示错误消息
                addMessage('抱歉，发生了错误：' + (data.error || '未知错误'));
            }
        } catch (error) {
            removeLoadingIndicator();
            addMessage('抱歉，发生了网络错误，请稍后重试。');
        } finally {
            messageInput.disabled = false;
            messageInput.focus();
            isProcessing = false;
        }
    });

    // 清空聊天记录按钮事件
    clearButton.addEventListener('click', clearChat);

    // 按Enter发送消息，按Shift+Enter换行
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
}); 