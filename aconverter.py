import json
import time

import requests

import config


def save_iam_token(token: str):
    i = {
        "updated": time.time(),
        "token": token
    }
    with open("yandex_speechkit.json", "w", encoding="utf-8") as f:
        json.dump(i, f, indent=4, ensure_ascii=False)


def get_iam_token(force_create=False) -> str:
    try:
        if force_create:
            raise

        with open("yandex_speechkit.json", "r", encoding="utf-8") as f:
            i = json.load(f)
        updated = i["updated"]
        token = i["token"]

        t = time.time()
        if t - updated >= 21600:
            raise

        return token
    except:
        new_token = create_iam_token()
        save_iam_token(new_token)
        return new_token


def create_iam_token() -> str:
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    d = {
        "yandexPassportOauthToken": config.OAUTH_TOKEN
    }
    r = requests.post(url, json=d)

    return r.json()["iamToken"]


def voice_to_text(voice_path: str) -> str:
    with open(voice_path, "rb") as f:
        voice = f.read()

    for fc in (False, True):
        iam_token = get_iam_token(force_create=fc)
        params = "&".join([
            "topic=general",
            f"folderId={config.FOLDER_ID}",
            "lang=ru-RU",
            "punctuation=true"
        ])
        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?" + params
        headers = {"Authorization": f"Bearer {iam_token}"}
        r = requests.post(url, headers=headers, data=voice)

        print(r.json())

        if r.json().get("error_code") != "UNAUTHORIZED":
            return r.json()["result"]


if __name__ == "__main__":
    voice_to_text("tmp/voice_2.ogg")
