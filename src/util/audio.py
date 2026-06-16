#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词发音音频模块
"""

import os


def get_audio(word, data_dir):
    """获取单词发音音频，优先读本地缓存，否则从 MIMO TTS 下载并缓存

    Args:
        word: 单词
        data_dir: 数据目录（words 目录）

    Returns:
        wav bytes，失败返回 None
    """
    word_dir = os.path.join(data_dir, word)
    os.makedirs(word_dir, exist_ok=True)
    local_path = os.path.join(word_dir, "word-audit.wav")

    # 本地已有缓存
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()

    # 从 MIMO TTS 下载
    from util.mimo import tts_builtin_non_stream

    if tts_builtin_non_stream(word, local_path):
        with open(local_path, "rb") as f:
            return f.read()

    print(f"   ⚠️  音频下载失败 [{word}]")
    return None
