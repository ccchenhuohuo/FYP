from flask import Blueprint, request, jsonify
import json
import requests

ai_analysis = Blueprint('ai_analysis', __name__)

@ai_analysis.route('/user/api/ai_analysis', methods=['POST'])
def analyze_with_ai():
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 提取所需信息
        tickers = data.get('tickers', [])
        thresholds = data.get('thresholds', {})
        results = data.get('results', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        if not tickers or not results:
            return jsonify({'error': 'Missing required data'}), 400
        
        # 为每个股票构建单独的分析提示
        reports = []
        
        for ticker in tickers:
            # 查找对应的结果数据
            ticker_result = next((r for r in results if r.get('ticker') == ticker), None)
            
            if not ticker_result or 'error' in ticker_result:
                reports.append({
                    'ticker': ticker,
                    'content': f"<p>Unable to generate analysis for {ticker}. Insufficient data available.</p>"
                })
                continue
            
            # 构建AI提示
            prompt = generate_analysis_prompt(ticker, ticker_result, thresholds, start_date, end_date)
            
            # 调用AI API进行分析
            ai_response = query_ai_api(prompt)
            
            reports.append({
                'ticker': ticker,
                'content': ai_response
            })
        
        return jsonify({'reports': reports})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_analysis_prompt(ticker, result_data, thresholds, start_date, end_date):
    """生成用于AI分析的提示"""
    
    # 提取风险指标
    volatility = result_data.get('volatility')
    max_drawdown = result_data.get('max_drawdown')
    sharpe_ratio = result_data.get('sharpe_ratio')
    beta = result_data.get('beta')
    var_95 = result_data.get('var_95')
    sortino_ratio = result_data.get('sortino_ratio')
    
    # 构建提示
    prompt = f"""
As a financial expert, analyze the risk profile of {ticker} based on historical data from {start_date} to {end_date}.

Risk metrics:
- Annualized Volatility: {volatility}% (Threshold: {thresholds.get('volatility', 'N/A')})
- Maximum Drawdown: {max_drawdown}% (Threshold: {thresholds.get('drawdown', 'N/A')})
- Sharpe Ratio: {sharpe_ratio} (Threshold: {thresholds.get('sharpe', 'N/A')})
- Beta: {beta if beta is not None else 'N/A'} (Threshold: {thresholds.get('beta', 'N/A')})
- Value at Risk (95%): {var_95}% (Threshold: {thresholds.get('var', 'N/A')})
- Sortino Ratio: {sortino_ratio} (Threshold: {thresholds.get('sortino', 'N/A')})

Provide a brief but insightful analysis of the stock's risk profile. Include:
1. An overall assessment of the stock's risk level
2. Explanation of concerning risk factors
3. Interpretation of key metrics in the context of the market
4. Recommendations for risk management strategies

Format the output in HTML format with paragraphs and bullet points for clarity.
"""
    return prompt

def query_ai_api(prompt):
    """查询AI API并获取响应"""
    
    # 使用Gemini API进行实际分析
    try:
        from utils.chat_ai import chat_with_gemini_api
        
        # 调用Gemini API获取实际分析结果
        ai_response = chat_with_gemini_api(prompt)
        
        # 如果返回的不是HTML格式，添加基本的HTML格式化
        if not ("<p>" in ai_response or "<ul>" in ai_response or "<h" in ai_response):
            # 将普通文本转为HTML格式
            formatted_response = ""
            for paragraph in ai_response.split("\n\n"):
                if paragraph.strip():
                    formatted_response += f"<p>{paragraph}</p>\n"
            ai_response = formatted_response if formatted_response else f"<p>{ai_response}</p>"
        
        return ai_response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_message = f"""
<p class="text-danger">Error connecting to AI service: {str(e)}</p>
<p>Using fallback analysis:</p>
<p>Based on the risk metrics provided, this stock requires careful consideration before investing. 
Please review the metrics manually and consider consulting a financial advisor.</p>
"""
        return error_message 