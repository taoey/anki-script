"""
小米 MiMo-V2.5-TTS 语音合成调用 Demo

使用前请设置环境变量: export MIMO_API_KEY="your_api_key"
文档: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5
"""

import base64
import os

from dotenv import load_dotenv
from openai import OpenAI

# 从 .env 文件加载环境变量
load_dotenv()

# 初始化客户端（兼容 OpenAI API 格式）
client = OpenAI(
    api_key=os.environ.get("sk") or os.environ.get("MIMO_API_KEY"),
    base_url="https://api.xiaomimimo.com/v1",
)


# ========== 1. 内置语音 - 非流式调用 ==========
def tts_builtin_non_stream(text, save_path, voice="Mia", format="wav"):
    """使用内置音色进行语音合成（非流式）

    Args:
        text (str): 要合成的文本
        save_path (str): 保存文件路径
        voice (str, optional): 音色，支持: 冰糖/茉莉/苏打/白桦/Mia/Chloe/Milo/Dean，默认茉莉
        format (str, optional): 音频格式，默认 wav

    Returns:
        bool: 是否成功
    """
    try:
        completion = client.chat.completions.create(
            model="mimo-v2.5-tts",
            messages=[
                {
                    "role": "user",
                    "content": "用标准美音发音",
                },
                {
                    "role": "assistant",
                    "content": text,
                },
            ],
            audio={"format": format, "voice": voice},
        )

        message = completion.choices[0].message
        audio_bytes = base64.b64decode(message.audio.data)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(audio_bytes)
        return True
    except Exception as e:
        print(f"❌ TTS 合成失败: {e}")
        return False


def generate_sentence_audio(word, data_dir, examples):
    """为单词的例句生成音频

    Args:
        word (str): 单词
        data_dir (str): 数据目录
        examples (list): 例句列表 [{"sentence": "...", ...}, ...]

    Returns:
        list: 成功生成的文件路径列表
    """
    word_dir = os.path.join(data_dir, word)
    generated = []

    for i, example in enumerate(examples):
        sentence = example.get("sentence", "")
        if not sentence:
            continue

        filename = f"sentence-audit-{i + 1}.wav"
        save_path = os.path.join(word_dir, filename)

        # 已存在则跳过
        if os.path.exists(save_path):
            generated.append(filename)
            continue

        if tts_builtin_non_stream(sentence, save_path):
            generated.append(filename)
            print(f"🔊 例句音频已生成: {filename}")
        else:
            print(f"⚠️ 例句音频生成失败: {filename}")

    return generated


def classify_input(text):
    """判断用户输入是单词还是句子

    Args:
        text (str): 用户输入

    Returns:
        str: "word" 或 "sentence"
    """
    # 简单判断：包含空格或长度超过一定值认为是句子
    text = text.strip()
    if len(text.split()) > 1 or len(text) > 20:
        return "sentence"
    return "word"


SENTENCE_PROMPT = """You are an English translation expert. For the given English sentence, you MUST respond with ONLY a valid JSON object.

EXAMPLE:
{
  "original": "Life is like a box of chocolates, you never know what you're gonna get.",
  "translation": "人生就像一盒巧克力，你永远不知道下一颗是什么味道。",
  "key_words": [
    {"word": "chocolates", "meaning": "巧克力"},
    {"word": "never", "meaning": "从不"}
  ]
}

RULES:
1. Response MUST be valid JSON only - no markdown, no explanation
2. Provide accurate Chinese translation
3. Extract 3-5 key vocabulary words from the sentence
4. Include Chinese meaning for each key word"""


def translate_sentence(sentence, max_retries=3):
    """翻译英文句子并提取重点单词

    Args:
        sentence (str): 英文句子
        max_retries (int): 最大重试次数

    Returns:
        dict: 包含翻译和重点单词的字典，失败返回 None
    """
    import json
    import re

    for attempt in range(max_retries):
        response = chat(
            system_message=SENTENCE_PROMPT,
            user_message=f"Translate this sentence: {sentence}",
            temperature=0.1 + attempt * 0.1,
            response_format={"type": "json_object"}
        )

        if not response:
            continue

        json_str = response.strip()

        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str[3:]
            json_str = json_str.rsplit("```", 1)[0]

        match = re.search(r'\{[\s\S]*\}', json_str)
        if match:
            json_str = match.group()

        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        try:
            result = json.loads(json_str)
            if "original" in result and "translation" in result:
                return result
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败 (尝试 {attempt + 1}/{max_retries}): {e}")

    return None


# chat 基础函数
def chat(system_message, user_message, model="mimo-v2.5", temperature=0.5, max_tokens=2048, response_format=None):
    """与 MiMo 进行对话

    Args:
        system_message (str): 系统提示词
        user_message (str): 用户消息
        model (str, optional): 模型名称，默认 "mimo-v2.5"
        temperature (float, optional): 温度参数，默认 0.5
        max_tokens (int, optional): 最大 token 数，默认 2048
        response_format (dict, optional): 响应格式，如 {"type": "json_object"} 强制 JSON 输出

    Returns:
        str: 模型回复内容，失败返回 None
    """
    try:
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.95,
            "stream": False,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

        # 添加 response_format（如果支持）
        if response_format:
            params["response_format"] = response_format

        completion = client.chat.completions.create(**params)
        return completion.choices[0].message.content

    except Exception as e:
        print(f"❌ MiMo API 请求失败: {e}")
        return None


# ========== 英语单词解释 ==========
VOCAB_SYSTEM_PROMPT = """You are an English vocabulary expert. You MUST respond with ONLY a valid JSON object, no other text.

EXAMPLE for word "hello":
{
  "word": "hello",
  "phonetic": "/həˈloʊ/",
  "definitions": [
    {
      "pos": "interj.",
      "meaning": "你好；喂",
      "english": "used as a greeting or to begin a phone conversation"
    }
  ],
  "phrases": [
    {"phrase": "say hello", "meaning": "打招呼"},
    {"phrase": "hello there", "meaning": "你好啊"}
  ],
  "examples": [
    {
      "sentence": "Hello, my name is Inigo Montoya.",
      "source": "The Princess Bride (1987)",
      "translation": "你好，我叫伊尼戈·蒙托亚。"
    },
    {
      "sentence": "I just wanted to say hello.",
      "source": "Forrest Gump (1994)",
      "translation": "我只是想打个招呼。"
    },
    {
      "sentence": "Hello? Is anybody there?",
      "source": "Cast Away (2000)",
      "translation": "喂？有人在吗？"
    }
  ]
}

RULES:
1. Response MUST be valid JSON only - no markdown, no code blocks, no explanation
2. JSON must start with { and end with }
3. Include 1-3 definitions, 3-6 phrases, 3 examples
4. Examples preferably from movies/TV shows with source name and year
5. Use IPA format for phonetic transcription"""


def explain_word(word, max_retries=3):
    """获取英语单词的详细解释

    Args:
        word (str): 要查询的英语单词
        max_retries (int): 最大重试次数，默认 3

    Returns:
        dict: 包含单词信息的字典，失败返回 None
    """
    import json
    import re

    for attempt in range(max_retries):
        response = chat(
            system_message=VOCAB_SYSTEM_PROMPT,
            user_message=f"Explain the word: {word}",
            temperature=0.1 + attempt * 0.1,
            response_format={"type": "json_object"}  # 强制 JSON 输出
        )

        if not response:
            continue

        # 清理响应（使用 response_format 后通常不需要额外清理）
        json_str = response.strip()

        # 移除可能的 markdown 代码块（兼容处理）
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str[3:]
            json_str = json_str.rsplit("```", 1)[0]

        # 尝试提取 JSON 对象
        match = re.search(r'\{[\s\S]*\}', json_str)
        if match:
            json_str = match.group()

        # 尝试修复常见的 JSON 格式问题
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        try:
            result = json.loads(json_str)
            # 验证必要字段
            if "word" in result and ("definitions" in result or "phrases" in result):
                return result
            else:
                print(f"⚠️ 响应缺少必要字段 (尝试 {attempt + 1}/{max_retries})")
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"原始响应: {response[:500]}...")

    return None





if __name__ == "__main__":
    if not os.environ.get("sk") and not os.environ.get("MIMO_API_KEY"):
        print("请先在 .env 中设置 sk 或设置环境变量 MIMO_API_KEY")
        exit(1)

    # 测试 TTS
    tts_builtin_non_stream("Hello, how are you?", "./test_output.wav")
