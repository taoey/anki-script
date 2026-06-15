#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API 交互模块
"""

import os
import requests
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def chat(message, model="deepseek-v4-flash", temperature=0.7, max_tokens=2048):
    """与 DeepSeek 进行对话

    Args:
        message (str): 用户消息
        model (str, optional): 模型名称，默认 "deepseek-v4-flash"
        temperature (float, optional): 温度参数，默认 0.7
        max_tokens (int, optional): 最大 token 数，默认 2048

    Returns:
        str: 模型回复内容，失败返回 None
    """
    if not DEEPSEEK_API_KEY:
        print("❌ 未配置 DEEPSEEK_API_KEY")
        return None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=600
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"❌ 解析响应失败: {e}")
        return None


def chat_with_history(messages, model="deepseek-v4-flash", temperature=0.7, max_tokens=2048):
    """带历史记录的对话

    Args:
        messages (list): 消息列表，格式 [{"role": "user/assistant", "content": "..."}]
        model (str, optional): 模型名称
        temperature (float, optional): 温度参数
        max_tokens (int, optional): 最大 token 数

    Returns:
        str: 模型回复内容，失败返回 None
    """
    if not DEEPSEEK_API_KEY:
        print("❌ 未配置 DEEPSEEK_API_KEY")
        return None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        print(f"❌ DeepSeek API 请求失败: {e}")
        if 'response' in locals():
            print(f"服务器响应: {response.text}")
        return None
    except (KeyError, IndexError) as e:
        print(f"❌ 解析响应失败: {e}")
        return None


def summarize_voice_diary(content, model="deepseek-v4-flash"):
    """整理口述录音日记

    Args:
        content (str): 口述录音的转录文本
        model (str, optional): 模型名称

    Returns:
        str: 整理后的日记内容，失败返回 None
    """
    prompt = f"""下面是我的一个口述录音日记，请帮我进行整理。要求如下：
1-总结标题
2-汇总主要观点（逐条）；
3-正文：对原文的整理，整理清楚就好，去除过度的口语化，避免过于机械输出，需要像一个人随笔写的东西，保留人味；
4-tag：提取1个最核心tag

格式示例(需要严格按照下面格式来)：

#tag1 #tag2
## 标题示例
### 内容汇总：
1. 内容汇总示例1
2. 内容汇总示例2

### 主要内容：
主要内容示例

以下是日记内容：
{content}"""

    return chat(prompt, model=model, temperature=0.5)

