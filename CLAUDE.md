# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

通过 AnkiConnect（Anki 插件，监听 localhost:8765）的 JSON-RPC API 批量管理 Anki 卡片的 Python 脚本集。

## 常用命令

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行英语单词卡片脚本（需要 Anki 已启动 + AnkiConnect 插件已安装）
python create_vocab_cards.py

# 运行 AnkiConnect 客户端内置示例
python aniconnect.py

# 安装依赖
pip install -r requirements.txt
```

## 架构

- **ankiconnect.py** — `AnkiConnect` 类，封装所有 AnkiConnect API 调用。其他脚本通过 `importlib.util` 动态加载它（因为 Python 3.14 下直接 import 同目录模块有路径问题）。
- **create_vocab_cards.py** — 英语单词卡片主脚本。定义笔记模型（VocabCard2）、卡片模板 HTML/CSS、单词数据，执行写入。

## 关键设计决策

- `AnkiConnect.create_model()` 的 `inOrderFields` 参数必须传 **列表**，不能传逗号拼接的字符串，否则 AnkiConnect 会报字段找不到。
- 卡片字段用英文命名（Front/Phonetic/Back/Example/Mnemonic/Audio），AnkiConnect 对中文字段名支持不稳定。
- 音频通过 Google TTS 获取，本地缓存在 `data/` 目录（已 gitignore），避免重复下载。
- 写入时先查已有笔记（按 Front 字段匹配），已存在则 `updateNoteFields`，不存在则 `addNotes`，不会产生重复卡片。
- AnkiConnect 的 `deleteModel` 动作在某些版本不可用，不要依赖它。
