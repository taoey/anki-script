#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 mimo.py 的 chat 函数
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from util.mimo import chat

# 测试 chat 函数
print("🧪 测试 MiMo chat 函数...")
print("-" * 50)

response = chat(
    system_message="You are MiMo, an AI assistant developed by Xiaomi.",
    user_message="请用一句话介绍你自己"
)

if response:
    print(f"✅ 测试成功!")
    print(f"回复: {response}")
else:
    print("❌ 测试失败，请检查 MIMO_API_KEY 是否配置正确")
