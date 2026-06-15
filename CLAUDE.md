# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

英语学习工具，包含：
1. Flask Web 应用 — 单词查询、句子翻译、发音播放
2. AnkiConnect 脚本 — 批量管理 Anki 卡片

## 常用命令

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Web 服务
python app.py
# 或
./run.sh

# 运行 Anki 卡片脚本（需要 Anki + AnkiConnect）
python create_vocab_cards.py

# 安装依赖
pip install -r requirements.txt
# 或
./install.sh
```

## 架构

### Web 应用 (app.py)
- Flask 服务，端口 8076，HTTP Basic Auth 认证
- 单词/句子查询、音频播放、配置管理
- 数据存储在 `data/words/` 和 `data/sentences/` 目录

### 工具模块 (src/util/)
- **audio.py** — Google TTS 音频下载，缓存为 `word-audit.mp3`
- **mimo.py** — MiMo API 客户端
  - `classify_input()` — 判断输入是单词还是句子
  - `explain_word()` — 单词释义查询
  - `translate_sentence()` — 句子翻译+重点词提取
  - `tts_builtin_non_stream()` — MiMo TTS 语音合成
  - `generate_sentence_audio()` — 批量生成例句音频

### Anki 脚本
- **ankiconnect.py** — `AnkiConnect` 类，封装 AnkiConnect API
- **create_vocab_cards.py** — 通过 `importlib.util` 动态加载 ankiconnect.py

## 关键设计决策

- 单词目录名：小写原词 (`data/words/hello/`)
- 句子目录名：MD5 哈希 (`data/sentences/<md5>/`)
- 单词发音：Google TTS → `word-audit.mp3`
- 句子发音：MiMo TTS → `sentence-audit.wav`
- 例句发音：MiMo TTS → `sentence-audit-1.wav`, `sentence-audit-2.wav`...
- `AnkiConnect.create_model()` 的 `inOrderFields` 必须传列表，不能传字符串
- AnkiConnect 对中文字段名支持不稳定，使用英文命名

## 环境变量

```bash
PORT=8076
AUTH_PASSWORD=anki2024
DATA_DIR=./data              # 可选，默认 ./data
MIMO_API_KEY=sk-xxx          # 必须
DEEPSEEK_API_KEY=sk-xxx      # 可选
```
