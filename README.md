# 英语助手

一个集成了 Anki 卡片管理、AI 单词查询、句子翻译、发音播放的英语学习工具。

## 功能

### Web 应用（Flask）

- **单词查询** — 输入单词自动查询释义、音标、词组、例句
- **句子翻译** — 输入句子自动翻译并提取重点单词
- **发音播放** — 单词使用 Google TTS，句子使用 MiMo TTS
- **例句音频** — 自动生成并缓存例句发音
- **单词/句子列表** — 分别管理已查询的单词和句子
- **单词高亮链接** — 页面中已收录的单词自动高亮可点击，支持子串匹配（按首字母索引+长度降序匹配）
- **句子标签** — 为句子添加/删除自定义标签
- **学习记录** — 标记句子学习状态
- **数据缓存** — 所有查询结果本地缓存，支持自定义存储路径
- **密码认证** — HTTP Basic Auth 保护

### Anki 卡片脚本

- **ankiconnect.py** — AnkiConnect API 客户端封装
- **create_vocab_cards.py** — 批量创建英语单词记忆卡片

## 快速开始

```bash
# 1. 安装依赖
./install.sh

# 2. 配置 .env
cp .env.example .env
# 编辑 .env 填入 API Key 和密码

# 3. 启动服务
./run.sh

# 4. 访问 http://localhost:8076
```

## 环境变量 (.env)

```bash
PORT=8076                    # 服务端口
AUTH_PASSWORD=anki2024       # 访问密码
DATA_DIR=./data              # 数据存储目录（可选）
MIMO_API_KEY=sk-xxx          # MiMo API Key（句子翻译、TTS）
DEEPSEEK_API_KEY=sk-xxx      # DeepSeek API Key（可选）
```

## 目录结构

```
anki-script/
├── app.py                    # Flask API 服务
├── aniconnect.py             # AnkiConnect 客户端
├── create_vocab_cards.py     # Anki 卡片脚本
├── install.sh                # 安装脚本（国内镜像）
├── run.sh                    # 启动脚本
├── requirements.txt          # 依赖
├── .env                      # 环境变量配置
├── templates/                # 页面模板
│   ├── index.html            # 首页（查询）
│   ├── words.html            # 单词列表
│   ├── word_detail.html      # 单词详情
│   ├── sentences.html        # 句子列表
│   └── sentence_detail.html  # 句子详情
├── src/
│   └── util/
│       ├── audio.py          # Google TTS 音频模块
│       └── mimo.py           # MiMo API（翻译、TTS）
└── data/                     # 数据存储
    ├── words/                # 单词数据
    │   └── hello/
    │       ├── word.json     # 单词信息
    │       ├── meta.json     # 元数据（时间戳）
    │       ├── word-audit.mp3      # 单词发音
    │       └── sentence-audit-1.wav # 例句发音
    └── sentences/            # 句子数据
        └── <md5>/
            ├── sentence.json # 句子信息
            ├── meta.json     # 元数据
            └── sentence-audit.wav # 句子发音
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ping` | 健康检查（无需认证） |
| GET | `/` | 查询页面 |
| GET | `/words` | 单词列表页面 |
| GET | `/word/<word>` | 单词详情页面 |
| GET | `/sentences` | 句子列表页面 |
| GET | `/sentence/<dir>` | 句子详情页面 |
| GET | `/api/word/<word>` | 查询单词/句子（GET） |
| POST | `/api/word` | 查询单词/句子（POST，推荐，避免 URL 长度限制） |
| GET | `/api/words` | 单词列表 |
| GET | `/api/words/exists` | 已收录单词列表（用于前端高亮） |
| GET | `/api/sentences` | 句子列表 |
| GET | `/api/sentence/<dir>` | 句子详情 |
| DELETE | `/api/sentence/<dir>` | 删除句子 |
| POST | `/api/sentence/<dir>/tag` | 添加句子标签 |
| DELETE | `/api/sentence/<dir>/tag/<tag>` | 删除句子标签 |
| POST | `/api/sentence/<dir>/study` | 标记句子学习状态 |
| GET | `/api/audio/<word>` | 单词发音 |
| GET | `/api/audio/<word>/sentence/<n>` | 例句发音 |
| GET | `/api/audio/sentence/<dir>` | 句子发音 |
| GET | `/api/config` | 获取配置 |
| POST | `/api/config` | 更新配置 |

## Anki 卡片使用

```bash
# 需要 Anki 已启动 + AnkiConnect 插件已安装
python create_vocab_cards.py
```

编辑 `create_vocab_cards.py` 中的 `SAMPLE_WORDS` 添加单词：

```python
{
    "Front": "ephemeral",           # 单词
    "Phonetic": "/ɪˈfemərəl/",     # 音标
    "Back": "adj. 短暂的",          # 释义
    "Example": "Life is ephemeral.", # 例句
    "Mnemonic": "ep- + hemer(天)",  # 助记
    "Audio": "",                     # 留空，自动生成
}
```
