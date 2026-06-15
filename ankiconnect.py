"""AnkiConnect 客户端封装"""

import requests


class AnkiConnect:
    """AnkiConnect API 客户端"""

    def __init__(self, url="http://localhost:8765"):
        self.url = url

    def invoke(self, action, params=None):
        """调用 AnkiConnect API"""
        payload = {"action": action, "version": 6, "params": params or {}}
        resp = requests.post(self.url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result.get("result")

    def is_connected(self):
        """测试连接是否可达，返回版本号或 None"""
        try:
            return self.invoke("version")
        except requests.ConnectionError:
            return None

    # ---------- 读取 ----------

    def get_deck_names(self):
        """获取所有牌组名称"""
        return self.invoke("deckNames")

    def get_model_names(self):
        """获取所有笔记类型（模型）名称"""
        return self.invoke("modelNames")

    def get_model_field_names(self, model_name):
        """获取指定模型的字段名列表"""
        return self.invoke("modelFieldNames", {"modelName": model_name})

    def find_cards(self, query):
        """按查询语句搜索卡片，返回卡片 ID 列表"""
        return self.invoke("findCards", {"query": query})

    def get_cards_info(self, card_ids):
        """获取卡片详细信息"""
        return self.invoke("cardsInfo", {"cards": card_ids})

    # ---------- 写入 ----------

    def create_deck(self, deck_name):
        """创建牌组（已存在则跳过）"""
        return self.invoke("createDeck", {"deck": deck_name})

    def add_note(self, deck_name, model_name, fields, tags=None):
        """添加单条笔记

        Args:
            deck_name:   牌组名称
            model_name:  笔记类型名称（如 "Basic"、"Cloze"）
            fields:      字段字典，如 {"Front": "问题", "Back": "答案"}
            tags:        标签列表，如 ["python", "anki"]

        Returns:
            新建笔记的 ID
        """
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": tags or [],
        }
        return self.invoke("addNote", {"note": note})

    def add_notes(self, notes):
        """批量添加笔记

        Args:
            notes: 笔记字典列表，每个字典包含
                   deckName, modelName, fields, tags(可选)

        Returns:
            新建笔记的 ID 列表（失败的位置为 None）
        """
        return self.invoke("addNotes", {"notes": notes})

    def update_note_fields(self, note_id, fields):
        """更新已有笔记的字段

        Args:
            note_id: 笔记 ID
            fields:  要更新的字段字典
        """
        return self.invoke("updateNoteFields", {
            "note": {"id": note_id, "fields": fields}
        })

    def delete_notes(self, note_ids):
        """批量删除笔记"""
        return self.invoke("deleteNotes", {"notes": note_ids})

    def store_media(self, filename, data):
        """存储媒体文件到 Anki 媒体库

        Args:
            filename: 文件名，如 "hello.mp3"
            data:     文件内容（bytes）
        """
        import base64
        return self.invoke("storeMediaFile", {
            "filename": filename,
            "data": base64.b64encode(data).decode(),
        })

    def create_model(self, model_name, fields, template, css=""):
        """创建笔记类型（模型）

        Args:
            model_name: 模型名称
            fields:     字段名列表，如 ["单词", "音标", "解释"]
            template:   卡片模板字典，包含 Name, Front, Back
            css:        卡片样式

        Returns:
            创建结果
        """
        return self.invoke("createModel", {
            "modelName": model_name,
            "inOrderFields": fields,
            "cardTemplates": [template],
            "css": css,
        })


# ---------------------------------------------------------------------------
# 示例：写入一条笔记
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    anki = AnkiConnect()

    # 1. 检查连接
    version = anki.is_connected()
    if not version:
        print("❌ 无法连接 AnkiConnect，请确认 Anki 已启动且插件已安装")
        exit(1)
    print(f"✅ 已连接 AnkiConnect v{version}\n")

    # 2. 确保牌组存在
    deck = "测试牌组"
    anki.create_deck(deck)
    print(f"📚 牌组「{deck}」就绪")

    # 3. 列出可用模型，取第一个作为示例
    models = anki.get_model_names()
    print(f"📝 可用笔记类型: {models}")
    model_name = models[0]
    fields = anki.get_model_field_names(model_name)
    print(f"   使用「{model_name}」，字段: {fields}\n")

    # 4. 写入一条笔记
    #    fields 的 key 必须与模型字段名完全一致
    front_field = fields[0]
    back_field = fields[1] if len(fields) > 1 else fields[0]
    note_id = anki.add_note(
        deck_name=deck,
        model_name=model_name,
        fields={front_field: "AnkiConnect 用什么协议通信？", back_field: "JSON-RPC over HTTP"},
        tags=["测试", "ankiconnect"],
    )
    print(f"✏️  笔记已写入，ID: {note_id}")

    # 5. 批量写入
    batch = [
        {
            "deckName": deck,
            "modelName": model_name,
            "fields": {front_field: "AnkiConnect 默认端口？", back_field: "8765"},
            "tags": ["测试"],
        },
        {
            "deckName": deck,
            "modelName": model_name,
            "fields": {front_field: "AnkiConnect 版本号用哪个字段？", back_field: "version: 6"},
            "tags": ["测试"],
        },
    ]
    note_ids = anki.add_notes(batch)
    print(f"✏️  批量写入 {len([n for n in note_ids if n])} 条笔记")

    # 6. 验证写入结果
    cards = anki.find_cards(f"deck:{deck}")
    print(f"\n🃏 「{deck}」现有 {len(cards)} 张卡片")
