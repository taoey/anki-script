#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过 API 批量添加单词或句子的脚本

用法:
    # 添加单个单词
    python add_words.py hello

    # 添加多个单词（空格分隔）
    python add_words.py hello world amazing

    # 添加句子（用引号包裹）
    python add_words.py "The quick brown fox jumps over the lazy dog"

    # 从文件读取（每行一个单词/句子）
    python add_words.py --file words.txt

    # 指定服务器地址和密码
    python add_words.py --server http://localhost:8076 --password anki2024 hello
"""

import argparse
import requests
import sys
import time


def add_word(server: str, password: str, word: str) -> dict:
    """调用 API 添加单词或句子"""
    url = f"{server}/api/word"
    auth = requests.auth.HTTPBasicAuth("", password)

    try:
        resp = requests.post(url, json={"word": word}, auth=auth, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="通过 API 批量添加单词或句子",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python add_words.py hello
    python add_words.py hello world amazing
    python add_words.py "The quick brown fox"
    python add_words.py --file words.txt
    python add_words.py --file -  # 从 stdin 读取
        """
    )
    parser.add_argument("words", nargs="*", help="要添加的单词或句子")
    parser.add_argument("--file", "-f", help="从文件读取（每行一个），用 - 表示 stdin")
    parser.add_argument("--server", "-s", default="http://localhost:8076", help="服务器地址 (默认: http://localhost:8076)")
    parser.add_argument("--password", "-p", default="anki2024", help="认证密码 (默认: anki2024)")
    parser.add_argument("--delay", "-d", type=float, default=0, help="每个请求之间的延迟秒数 (默认: 0)")

    args = parser.parse_args()

    # 收集所有要处理的词
    all_words = []

    if args.words:
        all_words.extend(args.words)

    if args.file:
        if args.file == "-":
            lines = sys.stdin.read().splitlines()
        else:
            with open(args.file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):  # 跳过空行和注释
                all_words.append(line)

    if not all_words:
        parser.print_help()
        sys.exit(1)

    # 去重（保持顺序）
    seen = set()
    unique_words = []
    for w in all_words:
        if w not in seen:
            seen.add(w)
            unique_words.append(w)

    total = len(unique_words)
    success = 0
    failed = 0
    skipped = 0

    print(f"📚 开始处理 {total} 个词条...\n")

    for i, word in enumerate(unique_words, 1):
        print(f"[{i}/{total}] {word} ... ", end="", flush=True)

        result = add_word(args.server, args.password, word)

        if result.get("status") == "ok":
            source = result.get("source", "unknown")
            data = result.get("data", {})

            if source == "cache":
                # 已存在
                print(f"✅ 已存在 (cached)")
                skipped += 1
            else:
                # 新添加
                print(f"✅ 已添加 ({source})")
                success += 1
        else:
            msg = result.get("message", "未知错误")
            print(f"❌ 失败: {msg}")
            failed += 1

        # 延迟
        if args.delay > 0 and i < total:
            time.sleep(args.delay)

    # 统计
    print(f"\n{'='*40}")
    print(f"📊 完成! 共 {total} 个:")
    print(f"   ✅ 新添加: {success}")
    print(f"   ⏭️  已存在: {skipped}")
    if failed > 0:
        print(f"   ❌ 失败:   {failed}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
