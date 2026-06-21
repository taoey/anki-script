#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API 服务
"""

import os
import sys
import json
import time
import hashlib
from functools import wraps
from flask import Flask, jsonify, request, Response, render_template
from dotenv import load_dotenv

load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from util.mimo import explain_word, generate_sentence_audio, classify_input, translate_sentence
from util.audio import get_audio

app = Flask(__name__)

PORT = int(os.getenv("PORT", 8076))
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "anki2024")
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), 'data'))

# 缓存相关
words_cache = {
    "data": None,
    "updated_at": 0
}
existing_words_cache = {
    "data": None,
    "updated_at": 0
}


def check_auth(password):
    """检查密码是否正确"""
    return password == AUTH_PASSWORD


def require_auth(f):
    """认证装饰器 - 使用 HTTP Basic Auth"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.password):
            return Response(
                '请输入密码访问',
                401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return f(*args, **kwargs)
    return decorated


def invalidate_words_cache():
    """使单词缓存失效"""
    words_cache["data"] = None
    words_cache["updated_at"] = 0
    existing_words_cache["data"] = None
    existing_words_cache["updated_at"] = 0


@app.route("/ping", methods=["GET"])
def ping():
    """健康检查接口（不需要认证）"""
    return jsonify({"status": "ok", "message": "pong"})


@app.route("/", methods=["GET"])
@require_auth
def index():
    """首页"""
    return render_template("index.html")


@app.route("/api/word/<word>", methods=["GET"])
@require_auth
def get_word(word):
    """查询单词或句子"""
    word = word.strip()
    input_type = classify_input(word)

    # 对于句子，使用 MD5 作为目录名
    if input_type == "sentence":
        dir_name = hashlib.md5(word.encode('utf-8')).hexdigest()
        parent_dir = os.path.join(DATA_DIR, "sentences")
    else:
        dir_name = word.lower()
        parent_dir = os.path.join(DATA_DIR, "words")

    word_dir = os.path.join(parent_dir, dir_name)
    json_path = os.path.join(word_dir, "sentence.json" if input_type == "sentence" else "word.json")

    # 检查本地是否已有缓存
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 读取 meta.json 获取时间戳和类型
            meta_path = os.path.join(word_dir, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    data['created_at'] = meta.get('created_at', 0)
                    data['created_at_str'] = meta.get('created_at_str', '')
                    data['type'] = meta.get('type', input_type)
            # 返回目录名（用于句子音频播放）
            if input_type == "sentence":
                data['dir_name'] = dir_name
            # 确保音频也已缓存
            if input_type == "sentence":
                audio_path = os.path.join(word_dir, "sentence-audit.wav")
                if not os.path.exists(audio_path):
                    from util.mimo import tts_builtin_non_stream
                    tts_builtin_non_stream(data.get("original", word), audio_path)
            else:
                words_dir = os.path.join(DATA_DIR, "words")
                get_audio(dir_name, words_dir)
            # 确保例句音频已生成（仅单词）
            if input_type == "word":
                examples = data.get("examples", [])
                if examples:
                    words_dir = os.path.join(DATA_DIR, "words")
                    generate_sentence_audio(dir_name, words_dir, examples)
            # 查询时也刷新单词列表缓存
            invalidate_words_cache()
            return jsonify({"status": "ok", "data": data, "source": "cache"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"读取缓存失败: {str(e)}"}), 500

    # 根据类型调用不同 API
    if input_type == "sentence":
        result = translate_sentence(word)
    else:
        result = explain_word(word)

    if not result:
        return jsonify({"status": "error", "message": "查询失败，请检查网络或 API Key"}), 500

    # 对于单词，检查 MIMO 返回的 word 是否与用户输入一致
    if input_type == "word" and "word" in result:
        mimo_word = result["word"].lower().strip()
        if mimo_word != dir_name:
            # 使用 MIMO 返回的正确单词作为目录名
            correct_dir = os.path.join(parent_dir, mimo_word)
            # 如果旧目录已存在，移动到新目录
            if os.path.exists(word_dir) and word_dir != correct_dir:
                import shutil
                if os.path.exists(correct_dir):
                    shutil.rmtree(correct_dir)
                os.rename(word_dir, correct_dir)
            word_dir = correct_dir
            dir_name = mimo_word
            json_path = os.path.join(word_dir, "word.json")

    # 保存到本地
    try:
        os.makedirs(word_dir, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 保存 meta.json（包含时间戳和类型）
        meta_path = os.path.join(word_dir, "meta.json")
        created_at = time.time()
        created_at_str = time.strftime("%Y-%m-%d %H:%M:%S")
        meta_data = {
            "text": word,
            "type": input_type,
            "created_at": created_at,
            "created_at_str": created_at_str
        }
        if input_type == "word":
            meta_data["word"] = dir_name
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
        result['created_at'] = created_at
        result['created_at_str'] = created_at_str
        result['type'] = input_type
        if input_type == "sentence":
            result['dir_name'] = dir_name
        # 新增内容，清除缓存
        invalidate_words_cache()
    except Exception as e:
        print(f"保存缓存失败: {e}")

    # 下载并缓存发音音频
    if input_type == "sentence":
        from util.mimo import tts_builtin_non_stream
        audio_path = os.path.join(word_dir, "sentence-audit.wav")
        tts_builtin_non_stream(word, audio_path)
    else:
        words_dir = os.path.join(DATA_DIR, "words")
        get_audio(dir_name, words_dir)
        # 生成例句音频（仅单词）
        examples = result.get("examples", [])
        if examples:
            generate_sentence_audio(dir_name, words_dir, examples)

    return jsonify({"status": "ok", "data": result, "source": "api"})


@app.route("/api/audio/<word>", methods=["GET"])
@require_auth
def get_word_audio(word):
    """获取单词发音音频"""
    word = word.lower().strip()
    words_dir = os.path.join(DATA_DIR, "words")
    data = get_audio(word, words_dir)

    if not data:
        return jsonify({"status": "error", "message": "音频获取失败"}), 500

    return Response(data, mimetype="audio/wav")


@app.route("/api/audio/<word>/sentence/<int:index>", methods=["GET"])
@require_auth
def get_sentence_audio(word, index):
    """获取例句音频"""
    word = word.lower().strip()
    audio_path = os.path.join(DATA_DIR, "words", word, f"sentence-audit-{index}.wav")

    if not os.path.exists(audio_path):
        return jsonify({"status": "error", "message": "音频不存在"}), 404

    with open(audio_path, "rb") as f:
        data = f.read()

    return Response(data, mimetype="audio/wav")


@app.route("/api/audio/sentence/<dir_name>", methods=["GET"])
@require_auth
def get_sentence_audio_file(dir_name):
    """获取句子发音音频"""
    audio_path = os.path.join(DATA_DIR, "sentences", dir_name, "sentence-audit.wav")

    if not os.path.exists(audio_path):
        return jsonify({"status": "error", "message": "音频不存在"}), 404

    with open(audio_path, "rb") as f:
        data = f.read()

    return Response(data, mimetype="audio/wav")


@app.route("/words", methods=["GET"])
@require_auth
def words_page():
    """单词列表页面"""
    return render_template("words.html")


@app.route("/word/<word>", methods=["GET"])
@require_auth
def word_detail_page(word):
    """单词详情页面"""
    return render_template("word_detail.html", word=word)


@app.route("/api/words", methods=["GET"])
@require_auth
def get_words_list():
    """获取所有已查询的单词列表"""
    # 检查缓存
    if words_cache["data"] is not None:
        return jsonify({"status": "ok", "data": words_cache["data"]})

    words = []
    words_dir = os.path.join(DATA_DIR, "words")

    if not os.path.exists(words_dir):
        return jsonify({"status": "ok", "data": words})

    try:
        for word_dir in os.listdir(words_dir):
            word_path = os.path.join(words_dir, word_dir)
            word_json_path = os.path.join(word_path, "word.json")
            meta_path = os.path.join(word_path, "meta.json")

            # 确定使用哪个 JSON 文件
            json_path = None
            input_type = "word"
            if os.path.exists(word_json_path):
                json_path = word_json_path
                input_type = "word"

            # 检查是否是目录且包含 JSON 文件
            if os.path.isdir(word_path) and json_path and os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 读取 meta.json 获取时间戳和类型
                created_at = 0
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        created_at = meta.get("created_at", 0)
                        input_type = meta.get("type", input_type)
                else:
                    # 如果没有 meta.json，使用文件修改时间并创建
                    created_at = os.path.getmtime(json_path)
                    try:
                        meta_data = {
                            "text": word_dir,
                            "type": input_type,
                            "created_at": created_at,
                            "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))
                        }
                        with open(meta_path, 'w', encoding='utf-8') as f:
                            json.dump(meta_data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass

                # 只返回单词类型
                if input_type != "word":
                    continue

                # 提取摘要信息（优先使用 word.json 中的 word）
                display_text = data.get("word", word_dir)
                definitions = data.get("definitions", [])
                first_meaning = definitions[0].get("meaning", "") if definitions else ""
                phonetic = data.get("phonetic", "")

                words.append({
                    "word": display_text,
                    "dir_name": word_dir,
                    "type": input_type,
                    "phonetic": phonetic,
                    "meaning": first_meaning,
                    "definition_count": len(data.get("definitions", [])),
                    "phrase_count": len(data.get("phrases", [])),
                    "created_at": created_at
                })

        # 按时间戳倒序排序（新添加的在最上面）
        words.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    # 更新缓存
    words_cache["data"] = words
    words_cache["updated_at"] = time.time()

    return jsonify({"status": "ok", "data": words})


@app.route("/sentences", methods=["GET"])
@require_auth
def sentences_page():
    """句子列表页面"""
    return render_template("sentences.html")


@app.route("/sentence/<dir_name>", methods=["GET"])
@require_auth
def sentence_detail_page(dir_name):
    """句子详情页面"""
    return render_template("sentence_detail.html", dir_name=dir_name)


@app.route("/api/sentences", methods=["GET"])
@require_auth
def get_sentences_list():
    """获取所有已查询的句子列表"""
    sentences = []
    sentences_dir = os.path.join(DATA_DIR, "sentences")

    if not os.path.exists(sentences_dir):
        return jsonify({"status": "ok", "data": sentences})

    try:
        for dir_name in os.listdir(sentences_dir):
            sentence_path = os.path.join(sentences_dir, dir_name)
            json_path = os.path.join(sentence_path, "sentence.json")
            meta_path = os.path.join(sentence_path, "meta.json")

            if not os.path.isdir(sentence_path) or not os.path.exists(json_path):
                continue

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 读取 meta.json 获取时间戳
            created_at = 0
            text = ""
            tags = []
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    created_at = meta.get("created_at", 0)
                    text = meta.get("text", "")
                    tags = meta.get("tags", [])
            else:
                created_at = os.path.getmtime(json_path)
                try:
                    meta_data = {
                        "text": data.get("original", ""),
                        "type": "sentence",
                        "created_at": created_at,
                        "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))
                    }
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta_data, f, ensure_ascii=False, indent=2)
                    text = meta_data["text"]
                except Exception:
                    pass

            sentences.append({
                "original": data.get("original", ""),
                "translation": data.get("translation", ""),
                "dir_name": dir_name,
                "text": text,
                "key_word_count": len(data.get("key_words", [])),
                "created_at": created_at,
                "tags": tags
            })

        # 按时间戳倒序排序
        sentences.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok", "data": sentences})


@app.route("/api/words/exists", methods=["GET"])
@require_auth
def get_existing_words():
    """获取所有已存在的单词列表（用于前端高亮）"""
    # 检查缓存
    if existing_words_cache["data"] is not None:
        return jsonify({"status": "ok", "data": existing_words_cache["data"]})

    words = []
    words_dir = os.path.join(DATA_DIR, "words")

    if os.path.exists(words_dir):
        try:
            for word_dir in os.listdir(words_dir):
                word_path = os.path.join(words_dir, word_dir)
                if os.path.isdir(word_path) and os.path.exists(os.path.join(word_path, "word.json")):
                    words.append(word_dir)
        except Exception:
            pass

    # 更新缓存
    existing_words_cache["data"] = words
    existing_words_cache["updated_at"] = time.time()

    return jsonify({"status": "ok", "data": words})


@app.route("/api/sentence/<dir_name>", methods=["GET"])
@require_auth
def get_sentence_detail(dir_name):
    """获取句子详情"""
    sentences_dir = os.path.join(DATA_DIR, "sentences")
    sentence_path = os.path.join(sentences_dir, dir_name)
    json_path = os.path.join(sentence_path, "sentence.json")
    meta_path = os.path.join(sentence_path, "meta.json")

    if not os.path.exists(json_path):
        return jsonify({"status": "error", "message": "句子不存在"}), 404

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 读取 meta.json
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                data['created_at'] = meta.get('created_at', 0)
                data['created_at_str'] = meta.get('created_at_str', '')
                data['type'] = 'sentence'
                data['tags'] = meta.get('tags', [])

        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sentence/<dir_name>/tag", methods=["POST"])
@require_auth
def add_sentence_tag(dir_name):
    """为句子添加 tag"""
    sentences_dir = os.path.join(DATA_DIR, "sentences")
    sentence_path = os.path.join(sentences_dir, dir_name)
    meta_path = os.path.join(sentence_path, "meta.json")

    if not os.path.exists(sentence_path):
        return jsonify({"status": "error", "message": "句子不存在"}), 404

    try:
        tag = request.json.get("tag", "").strip()
        if not tag:
            return jsonify({"status": "error", "message": "tag 不能为空"}), 400

        # 读取现有 meta.json
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

        tags = meta.get("tags", [])
        if tag not in tags:
            tags.append(tag)
            meta["tags"] = tags
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

        return jsonify({"status": "ok", "data": {"tags": tags}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sentence/<dir_name>/tag/<tag>", methods=["DELETE"])
@require_auth
def delete_sentence_tag(dir_name, tag):
    """删除句子的 tag"""
    sentences_dir = os.path.join(DATA_DIR, "sentences")
    sentence_path = os.path.join(sentences_dir, dir_name)
    meta_path = os.path.join(sentence_path, "meta.json")

    if not os.path.exists(sentence_path):
        return jsonify({"status": "error", "message": "句子不存在"}), 404

    try:
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            tags = meta.get("tags", [])
            if tag in tags:
                tags.remove(tag)
                meta["tags"] = tags
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

            return jsonify({"status": "ok", "data": {"tags": tags}})
        else:
            return jsonify({"status": "ok", "data": {"tags": []}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/config", methods=["GET"])
@require_auth
def get_config():
    """获取当前配置"""
    return jsonify({
        "status": "ok",
        "data": {
            "data_dir": DATA_DIR
        }
    })


@app.route("/api/config", methods=["POST"])
@require_auth
def update_config():
    """更新配置（保存到 .env 文件）"""
    global DATA_DIR

    new_data_dir = request.json.get("data_dir", "").strip()
    if not new_data_dir:
        return jsonify({"status": "error", "message": "数据目录不能为空"}), 400

    # 如果是相对路径，转为绝对路径
    if not os.path.isabs(new_data_dir):
        new_data_dir = os.path.abspath(new_data_dir)

    # 创建目录
    try:
        os.makedirs(new_data_dir, exist_ok=True)
    except Exception as e:
        return jsonify({"status": "error", "message": f"创建目录失败: {str(e)}"}), 400

    # 更新 .env 文件
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    _update_env_file(env_path, "DATA_DIR", new_data_dir)

    # 更新运行时变量
    DATA_DIR = new_data_dir

    return jsonify({
        "status": "ok",
        "message": "配置已保存",
        "data": {"data_dir": DATA_DIR}
    })


def _update_env_file(env_path, key, value):
    """更新 .env 文件中的键值"""
    lines = []
    found = False

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    with open(env_path, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.strip().startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
