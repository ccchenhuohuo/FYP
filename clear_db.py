#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清空数据库中的用户和相关记录
"""

from flask import Flask
from models import db, User, Order, Transaction, Portfolio, AccountBalance, FundTransaction
import os
import sys

def create_app():
    app = Flask(__name__)
    
    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Cyy-20030611@localhost/stock_data_v1'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化SQLAlchemy
    db.init_app(app)
    
    return app

def clear_database():
    """清空数据库中的用户和相关记录"""
    print("开始清空数据库中的用户和相关记录...")
    
    try:
        # 先处理旧表中的外键约束
        print("处理旧表外键约束...")
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # 清空旧表
        print("清空旧表 deposit...")
        db.session.execute(db.text("TRUNCATE TABLE deposit"))
        
        print("清空旧表 withdrawal...")
        db.session.execute(db.text("TRUNCATE TABLE withdrawal"))
        
        # 删除有外键关联的表
        print("删除交易记录...")
        db.session.execute(db.text("DELETE FROM transaction"))
        
        print("删除订单记录...")
        db.session.execute(db.text("DELETE FROM orders"))
        
        print("删除资金交易记录...")
        db.session.execute(db.text("DELETE FROM fund_transaction"))
        
        print("删除持仓记录...")
        db.session.execute(db.text("DELETE FROM portfolio"))
        
        print("删除账户余额记录...")
        db.session.execute(db.text("DELETE FROM account_balance"))
        
        print("删除用户记录...")
        db.session.execute(db.text("DELETE FROM user"))
        
        # 重新启用外键约束
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        
        db.session.commit()
        print("数据库清空完成！")
        
    except Exception as e:
        db.session.rollback()
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))  # 确保恢复外键检查
        print(f"清空数据库时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        clear_database() 