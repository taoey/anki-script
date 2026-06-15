#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API 服务
"""

import os
import sys
import json
import time
from functools import wraps
from flask import Flask, jsonify, request, Response, render_template
from dotenv import load_dotenv

load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from util.mimo import explain_word

app = Flask(__name__)

PORT = int(os.getenv("PORT", 8076))
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "anki2024")
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


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
    """查询单词解释"""
    word = word.lower().strip()
    word_dir = os.path.join(DATA_DIR, word)
    json_path = os.path.join(word_dir, "word.json")

    # 检查本地是否已有缓存
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({"status": "ok", "data": data, "source": "cache"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"读取缓存失败: {str(e)}"}), 500

    # 调用 API 获取单词解释
    result = explain_word(word)

    if not result:
        return jsonify({"status": "error", "message": "查询失败，请检查网络或 API Key"}), 500

    # 保存到本地
    try:
        os.makedirs(word_dir, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 保存 meta.json（包含时间戳）
        meta_path = os.path.join(word_dir, "meta.json")
        meta_data = {
            "word": word,
            "created_at": time.time(),
            "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存缓存失败: {e}")

    return jsonify({"status": "ok", "data": result, "source": "api"})


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
    words = []

    if not os.path.exists(DATA_DIR):
        return jsonify({"status": "ok", "data": words})

    try:
        for word_dir in os.listdir(DATA_DIR):
            word_path = os.path.join(DATA_DIR, word_dir)
            json_path = os.path.join(word_path, "word.json")
            meta_path = os.path.join(word_path, "meta.json")

            # 检查是否是目录且包含 JSON 文件
            if os.path.isdir(word_path) and os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 读取 meta.json 获取时间戳
                created_at = 0
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        created_at = meta.get("created_at", 0)
                else:
                    # 如果没有 meta.json，使用文件修改时间并创建
                    created_at = os.path.getmtime(json_path)
                    try:
                        meta_data = {
                            "word": word_dir,
                            "created_at": created_at,
                            "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))
                        }
                        with open(meta_path, 'w', encoding='utf-8') as f:
                            json.dump(meta_data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass

                # 提取摘要信息
                definitions = data.get("definitions", [])
                first_meaning = definitions[0].get("meaning", "") if definitions else ""

                words.append({
                    "word": word_dir,
                    "phonetic": data.get("phonetic", ""),
                    "meaning": first_meaning,
                    "definition_count": len(definitions),
                    "phrase_count": len(data.get("phrases", [])),
                    "created_at": created_at
                })

        # 按时间戳倒序排序（新添加的在最上面）
        words.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok", "data": words})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
