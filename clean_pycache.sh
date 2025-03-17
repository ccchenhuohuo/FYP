#!/bin/bash
# 查找并删除所有名为 __pycache__ 的目录
find . -type d -name "__pycache__" -exec rm -r {} \;
echo "所有 __pycache__ 目录已删除！"