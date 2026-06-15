"""创建英语单词记忆卡片

笔记类型字段：单词 / 音标 / 解释 / 例句 / 助记
卡片模板：正面显示单词，背面显示全部信息
"""

import importlib.util, os, urllib.request, time

_spec = importlib.util.spec_from_file_location("ankiconnect", os.path.join(os.path.dirname(__file__), "ankiconnect.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
AnkiConnect = _mod.AnkiConnect

# 音频本地缓存目录
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_audio(word):
    """获取单词发音音频，优先读本地缓存，否则从 Google TTS 下载并缓存

    Returns:
        mp3 bytes，失败返回 None
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)
    local_path = os.path.join(AUDIO_DIR, f"{word}.mp3")

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

MODEL_NAME = "VocabCard2"
DECK_NAME = "英语::单词"

FIELDS = ["Front", "Phonetic", "Back", "Example", "Mnemonic", "Audio"]

# 卡片正面：显示单词 + 音标 + 发音
FRONT_HTML = """
<div class="word">{{Front}}</div>
<div class="phonetic">{{Phonetic}}</div>
<div class="audio">{{Audio}}</div>
<div class="hint">点击显示释义 ↓</div>
"""

# 卡片背面：显示完整信息
BACK_HTML = """
{{FrontSide}}
<hr id="answer">
<div class="word">{{Front}}</div>
<div class="phonetic">{{Phonetic}}</div>
<div class="definition">{{Back}}</div>
{{#Example}}
<div class="example">
  <div class="label">📖 例句</div>
  <div class="sentence">{{Example}}</div>
</div>
{{/Example}}
{{#Mnemonic}}
<div class="mnemonic">
  <div class="label">💡 助记</div>
  <div class="content">{{Mnemonic}}</div>
</div>
{{/Mnemonic}}
"""

CARD_CSS = """
.card {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  text-align: center;
  background: #fafafa;
  color: #333;
  padding: 40px 20px;
}
.word {
  font-size: 2.4em;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 8px;
}
.phonetic {
  font-size: 1.2em;
  color: #888;
  margin-bottom: 16px;
}
.hint {
  font-size: 0.9em;
  color: #bbb;
  margin-top: 24px;
}
.definition {
  font-size: 1.3em;
  color: #2c3e50;
  margin: 20px 0;
  line-height: 1.6;
}
.example {
  background: #eef6ff;
  border-left: 4px solid #5b9bd5;
  text-align: left;
  padding: 12px 16px;
  margin: 16px auto;
  max-width: 500px;
  border-radius: 4px;
}
.example .label {
  font-size: 0.85em;
  color: #5b9bd5;
  margin-bottom: 6px;
}
.example .sentence {
  font-size: 1.05em;
  line-height: 1.6;
  color: #444;
}
.mnemonic {
  background: #fff8e1;
  border-left: 4px solid #f0ad4e;
  text-align: left;
  padding: 12px 16px;
  margin: 16px auto;
  max-width: 500px;
  border-radius: 4px;
}
.mnemonic .label {
  font-size: 0.85em;
  color: #f0ad4e;
  margin-bottom: 6px;
}
.mnemonic .content {
  font-size: 1.0em;
  line-height: 1.6;
  color: #555;
}
"""

# ---------------------------------------------------------------------------
# 示例单词数据
# ---------------------------------------------------------------------------
SAMPLE_WORDS = [
    {
        "Front": "ephemeral",
        "Phonetic": "/ɪˈfemərəl/",
        "Back": "adj. 短暂的，转瞬即逝的",
        "Example": "Fame in the modern world is often ephemeral.",
        "Mnemonic": "ep-(在…上) + hemer(天) → 只存活一天 → 短暂的",
    },
    {
        "Front": "ubiquitous",
        "Phonetic": "/juːˈbɪkwɪtəs/",
        "Back": "adj. 无处不在的，普遍存在的",
        "Example": "Smartphones have become ubiquitous in modern society.",
        "Mnemonic": "ubi(哪里) + quitous → 哪里都有 → 无处不在的",
    },
    {
        "Front": "eloquent",
        "Phonetic": "/ˈeləkwənt/",
        "Back": "adj. 雄辩的，有说服力的；口才好的",
        "Example": "She gave an eloquent speech that moved the audience to tears.",
        "Mnemonic": "e-(出) + loqu(说) → 说出来的 → 雄辩的",
    },
    {
        "Front": "pragmatic",
        "Phonetic": "/præɡˈmætɪk/",
        "Back": "adj. 务实的，注重实际的",
        "Example": "We need a pragmatic approach to solve this problem.",
        "Mnemonic": "pragm(做) → 注重做事 → 务实的",
    },
    {
        "Front": "resilient",
        "Phonetic": "/rɪˈzɪliənt/",
        "Back": "adj. 有弹性的；能迅速恢复的",
        "Example": "Children are often more resilient than adults think.",
        "Mnemonic": "re-(再) + sili(跳) → 能再跳起来 → 有恢复力的",
    },
]


def main():
    anki = AnkiConnect()

    # 1. 连接检查
    version = anki.is_connected()
    if not version:
        print("❌ 无法连接 AnkiConnect，请确认 Anki 已启动且插件已安装")
        return
    print(f"✅ 已连接 AnkiConnect v{version}\n")

    # 2. 创建笔记类型（已存在则跳过）
    existing_models = anki.get_model_names()
    if MODEL_NAME not in existing_models:
        anki.create_model(
            model_name=MODEL_NAME,
            fields=FIELDS,
            template={
                "Name": "卡片 1",
                "Front": FRONT_HTML,
                "Back": BACK_HTML,
            },
            css=CARD_CSS,
        )
        print(f"📝 笔记类型「{MODEL_NAME}」已创建")
    else:
        print(f"📝 笔记类型「{MODEL_NAME}」已存在，跳过创建")

    # 3. 创建牌组
    anki.create_deck(DECK_NAME)
    print(f"📚 牌组「{DECK_NAME}」就绪\n")

    # 4. 获取已有笔记（Front 字段 -> note_id）
    existing_cards = anki.find_cards(f"deck:{DECK_NAME}")
    existing_map = {}
    if existing_cards:
        for info in anki.get_cards_info(existing_cards):
            front_val = info["fields"]["Front"]["value"]
            existing_map[front_val] = info["note"]

    # 5. 逐个单词处理：已存在则更新，不存在则新增
    new_notes = []
    updated = 0
    created = 0
    for word in SAMPLE_WORDS:
        word_text = word["Front"]

        # 获取音频（优先本地缓存）并存入 Anki 媒体库
        audio_data = get_audio(word_text)
        if audio_data:
            audio_file = f"{word_text}.mp3"
            anki.store_media(audio_file, audio_data)
            word["Audio"] = f"[sound:{audio_file}]"
            print(f"🔊 {word_text} — 音频已存储")
            time.sleep(0.3)
        else:
            word["Audio"] = ""

        if word_text in existing_map:
            # 已存在 → 更新
            anki.update_note_fields(existing_map[word_text], word)
            updated += 1
        else:
            # 不存在 → 收集起来批量新增
            new_notes.append({
                "deckName": DECK_NAME,
                "modelName": MODEL_NAME,
                "fields": word,
                "tags": ["英语", "单词"],
            })
            created += 1

    if new_notes:
        anki.add_notes(new_notes)

    print(f"✏️  写入完成：新增 {created} 条，更新 {updated} 条")

    # 6. 验证
    cards = anki.find_cards(f"deck:{DECK_NAME}")
    print(f"🃏 「{DECK_NAME}」现有 {len(cards)} 张卡片")


if __name__ == "__main__":
    main()
