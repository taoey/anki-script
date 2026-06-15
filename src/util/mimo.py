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
def tts_builtin_non_stream():
    """使用内置音色进行语音合成（非流式），支持: 冰糖/茉莉/苏打/白桦/Mia/Chloe/Milo/Dean"""
    completion = client.chat.completions.create(
        model="mimo-v2.5-tts",
        messages=[
            {
                "role": "user",
                "content": "用标准美音发音",
            },
            {
                "role": "assistant",
                "content": "I can't believe you forgot my birthday. I reminded you three times this week. You even wrote it on your hand!",
            },
        ],
        audio={"format": "wav", "voice": "茉莉"},
    )

    message = completion.choices[0].message
    audio_bytes = base64.b64decode(message.audio.data)
    with open("output_builtin.wav", "wb") as f:
        f.write(audio_bytes)
    print("内置语音（非流式）已保存到 output_builtin.wav")

# chat 基础函数
def chat(system_message, user_message, model="mimo-v2.5", temperature=0.5, max_tokens=2048):
    """与 MiMo 进行对话

    Args:
        system_message (str): 系统提示词
        user_message (str): 用户消息
        model (str, optional): 模型名称，默认 "mimo-v2.5"
        temperature (float, optional): 温度参数，默认 0.5
        max_tokens (int, optional): 最大 token 数，默认 2048

    Returns:
        str: 模型回复内容，失败返回 None
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_message,
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            max_completion_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
            stream=False,
            stop=None,
            frequency_penalty=0,
            presence_penalty=0
        )
        return completion.choices[0].message.content

    except Exception as e:
        print(f"❌ MiMo API 请求失败: {e}")
        return None


# ========== 英语单词解释 ==========
VOCAB_SYSTEM_PROMPT = """You are an English vocabulary expert. Your task is to provide detailed word explanations in a structured format.

For each word, you MUST return EXACTLY this JSON format:
{
  "word": "the word",
  "phonetic": "/phonetic transcription/",
  "definitions": [
    {
      "pos": "part of speech (n./v./adj./adv./prep./conj.)",
      "meaning": "Chinese meaning",
      "english": "English explanation"
    }
  ],
  "phrases": [
    {
      "phrase": "common phrase",
      "meaning": "Chinese translation"
    }
  ],
  "examples": [
    {
      "sentence": "Example sentence preferably from movies/TV shows",
      "source": "Movie/TV show name (Year)",
      "translation": "Chinese translation"
    }
  ]
}

Rules:
1. Return ONLY the JSON, no other text
2. Include 1-3 most common definitions
3. Include 3-6 common phrases
4. Include 3 example sentences, preferably from famous movies or TV shows
5. All Chinese translations should be accurate
6. Phonetic transcription should use IPA format"""


def explain_word(word):
    """获取英语单词的详细解释

    Args:
        word (str): 要查询的英语单词

    Returns:
        dict: 包含单词信息的字典，失败返回 None
    """
    import json

    response = chat(
        system_message=VOCAB_SYSTEM_PROMPT,
        user_message=f"Please explain the word: {word}",
        temperature=0.3
    )

    if not response:
        return None

    try:
        # 尝试解析 JSON
        # 处理可能的 markdown 代码块
        json_str = response.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1]
            json_str = json_str.rsplit("```", 1)[0]

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"原始响应: {response}")
        return None





if __name__ == "__main__":
    if not os.environ.get("sk") and not os.environ.get("MIMO_API_KEY"):
        print("请先在 .env 中设置 sk 或设置环境变量 MIMO_API_KEY")
        exit(1)

    # 1. 内置语音 - 非流式
    tts_builtin_non_stream()
