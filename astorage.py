import json


def has_dialog(username: str) -> bool:
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    if username in users:
        return True
    else:
        users.append(username)
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return False


def load() -> dict:
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            s = json.load(f)
        return s
    except:
        return {}


def save(user_id, user_message: str, ai_message: str, deepness: int):
    user_id = str(user_id)
    storage = load()
    if not storage.get(user_id):
        storage[user_id] = {
            "history": [],
            "deepness": None
        }
    history = storage[user_id]["history"]
    history.append({
        "role": "user",
        "content": user_message
    })
    history.append({
        "role": "assistant",
        "content": ai_message
    })
    storage[user_id] = {
        "history": history,
        "deepness": int(deepness + 2)
    }
    with open("storage.json", "w", encoding="utf-8") as f:
        json.dump(storage, f, indent=4, ensure_ascii=False)


def get_history(user_id, deepness=None):
    user_id = str(user_id)
    storage = load()
    if not storage.get(user_id):
        storage[user_id] = {
            "history": [],
            "deepness": None
        }
    history = storage[user_id]["history"][:]
    if not deepness:
        deepness = storage[user_id]["deepness"]

    if not deepness:
        deepness = len(history)

    return {
        "history": history[len(history) - deepness:],
        "deepness": deepness
    }


if __name__ == "__main__":
    usr = """"""""
    print(has_dialog(usr))
