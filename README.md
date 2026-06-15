# anki-script

通过 [AnkiConnect](https://ankiweb.net/shared/info/2055492159) 批量管理 Anki 卡片的 Python 脚本。

## 功能

- **ankiconnect.py** — AnkiConnect API 客户端封装
  - 读取：牌组、笔记类型、卡片搜索、卡片详情
  - 写入：创建牌组/笔记类型、添加/更新/删除笔记、存储媒体文件
- **create_vocab_cards.py** — 英语单词记忆卡片
  - 字段：单词、音标、释义、例句、助记、发音音频
  - 音频：优先读本地 `data/` 缓存，未命中则从 Google TTS 下载并缓存
  - 去重：已存在的单词自动更新，不会产生重复卡片

## 使用

```bash
# 1. 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 启动 Anki 并确保 AnkiConnect 插件已安装

# 3. 运行
python create_vocab_cards.py
```

## 添加自己的单词

编辑 `create_vocab_cards.py` 中的 `SAMPLE_WORDS` 列表：

```python
{
    "Front": "ephemeral",           # 单词
    "Phonetic": "/ɪˈfemərəl/",     # 音标
    "Back": "adj. 短暂的",          # 释义
    "Example": "Life is ephemeral.", # 例句（可选）
    "Mnemonic": "ep- + hemer(天)",  # 助记（可选）
    "Audio": "",                     # 留空，脚本自动生成
}
```

## 目录结构

```
anki-script/
├── aniconnect.py          # AnkiConnect 客户端
├── create_vocab_cards.py  # 英语单词卡片脚本
├── requirements.txt       # 依赖
├── data/                  # 音频本地缓存（已 gitignore）
└── venv/                  # 虚拟环境（已 gitignore）
```
