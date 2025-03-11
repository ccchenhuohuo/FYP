from app import app
from models import MarketData

with app.app_context():
    # 检查是否有市场数据
    data = MarketData.query.first()
    print("市场数据:", data)
    
    if data:
        # 打印字段名
        print("字段名:")
        for column in MarketData.__table__.columns:
            print(f"  {column.name}")
        
        # 打印第一条数据的详细信息
        print("\n第一条数据详细信息:")
        print(f"  ID: {data.id}")
        print(f"  股票代码: {data.ticker}")
        print(f"  日期: {data.date}")
        print(f"  开盘价: {data.open}")
        print(f"  最高价: {data.high}")
        print(f"  最低价: {data.low}")
        print(f"  收盘价: {data.close}")
        print(f"  交易量: {data.volume}")
    else:
        print("数据库中没有市场数据") 