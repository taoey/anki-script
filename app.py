#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API 服务
"""

import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PORT = int(os.getenv("PORT", 8076))


@app.route("/ping", methods=["GET"])
def ping():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "pong"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
