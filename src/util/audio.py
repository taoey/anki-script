#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词发音音频模块
"""

import os
import urllib.request


def get_audio(word, data_dir):
    """获取单词发音音频，优先读本地缓存，否则从 Google TTS 下载并缓存

    Args:
        word: 单词
        data_dir: 数据目录

    Returns:
        mp3 bytes，失败返回 None
    """
    word_dir = os.path.join(data_dir, word)
    os.makedirs(word_dir, exist_ok=True)
    local_path = os.path.join(word_dir, "word-audit.mp3")

    # 本地已有缓存
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()

    # 从 Google TTS 下载
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={word}&tl=en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        # 存入本地缓存
        with open(local_path, "wb") as f:
            f.write(data)
        return data
    except Exception as e:
        print(f"   ⚠️  音频下载失败 [{word}]: {e}")
        return None
