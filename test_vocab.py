#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试英语单词解释功能
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from util.mimo import explain_word

# 测试单词
test_words = ["serendipity"]

for word in test_words:
    print(f"\n{'='*60}")
    print(f"📖 查询单词: {word}")
    print('='*60)

    result = explain_word(word)

    print(result)
    print("--------------")

    if result:
        print(f"\n✅ 单词: {result.get('word')}")
        print(f"🔊 音标: {result.get('phonetic')}")

        print("\n📝 释义:")
        for i, defn in enumerate(result.get('definitions', []), 1):
            print(f"  {i}. [{defn.get('pos')}] {defn.get('meaning')}")
            print(f"     {defn.get('english')}")

        print("\n💡 常用词组:")
        for phrase in result.get('phrases', []):
            print(f"  • {phrase.get('phrase')} - {phrase.get('meaning')}")

        print("\n🎬 例句:")
        for i, ex in enumerate(result.get('examples', []), 1):
            print(f"  {i}. {ex.get('sentence')}")
            print(f"     来源: {ex.get('source')}")
            print(f"     翻译: {ex.get('translation')}")
    else:
        print(f"❌ 查询失败")
