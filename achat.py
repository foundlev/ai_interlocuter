import openai
from pydub import AudioSegment

import config


async def ask(messages: list) -> str:
    openai.api_key = config.CHATGPT_TOKEN
    r = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1,
        max_tokens=1024
    )
    return r["choices"][0]["message"]["content"]


def ask_sync(messages: list) -> str:
    openai.api_key = config.CHATGPT_TOKEN
    r = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1,
        max_tokens=1024
    )
    return r["choices"][0]["message"]["content"]


def convert_to_mp3(voice_path) -> str:
    sound = AudioSegment.from_file(voice_path, format="ogg")
    new_voice_path = ".".join(voice_path.split(".")[:-1]) + ".mp3"
    sound.export(new_voice_path, format="mp3")

    return new_voice_path


async def convert_to_text(file_path):
    if ".ogg" in file_path:
        file_path = convert_to_mp3(file_path)

    openai.api_key = config.CHATGPT_TOKEN
    audio_file = open(file_path, "rb")
    transcript = await openai.Audio.atranscribe("whisper-1", audio_file)
    audio_file.close()

    return transcript["text"]


async def test(m):
    r = await ask(m)
    print(r)


if __name__ == "__main__":
    text = """*Пользователь прислал фотографию / картинку.
На ней изображено следующее: sewing, fashion, craft, embroidery, homemade*
(Отвечай только на русском)"""
    msgs = [
        {
            "role": "system",
            "content": config.ROLE_TEXT
        },
        {
            "role": "user",
            "content": text
        }
    ]
    print(ask_sync(msgs))
