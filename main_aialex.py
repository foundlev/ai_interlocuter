import time
import random
import os

import asyncio
from telethon import TelegramClient, events

import config
import achat
import astorage
import aobjects


class Storage:
    def __init__(self):
        self.updated = 0
        self.dv_updated = 0
        self.storage = {
            0: {
                "busy": False,
                "content": [],
                "photos": []
            }
        }

    def available(self) -> bool:
        dev_time = 3.2
        t = time.time()
        if t - self.updated >= dev_time:
            self.updated = t
            return True
        return False

    def busy(self, user_id) -> bool:
        return self.storage.get(user_id, {}).get("busy")

    def set_unbusy(self, user_id):
        self.storage[user_id] = {
            "busy": False,
            "content": [],
            "photos": []
        }

    def get_content(self, user_id) -> str:
        c = self.storage.get(user_id, {}).get("content", "")
        if isinstance(c, list):
            c = ". ".join(c)
        self.set_unbusy(user_id)

        return c

    def add_photo(self, user_id, new_photo: str):
        if not self.storage.get(user_id):
            self.storage[user_id] = {
                "busy": True,
                "content": [],
                "photos": []
            }
        self.storage[user_id]["busy"] = True
        self.storage[user_id]["photos"].append(new_photo)

    def add_content(self, user_id, new_content: str):
        if not self.storage.get(user_id):
            self.storage[user_id] = {
                "busy": True,
                "content": [],
                "photos": []
            }
        self.storage[user_id]["busy"] = True
        self.storage[user_id]["content"].append(new_content)


storage = Storage()
# Подключаемся к Telegram API
api_id = config.APP_ID
api_hash = config.APP_HASH
client = TelegramClient(config.SESSION_NAME, api_id, api_hash)


async def has_messages(usr) -> bool:
    try:
        entity = await client.get_entity(usr)
        messages = await client.get_messages(entity)

        return bool(messages)
    except:
        return False


# Обработчик новых сообщений
@client.on(events.NewMessage)
async def handle_new_message(event):
    try:
        user_id = event.message.peer_id.user_id
        message_type = aobjects.get_message_type(event)

        # Взаимодействие с Дайвинчиком.
        if str(user_id) == config.DAVINCI_ID and not event.message.out:
            pass

        elif event.message and not event.message.out and not event.message.via_bot_id:
            text = event.text

            # Если это голосовое или видео, то конвертируем в текст.
            if message_type in (aobjects.MessageTypes.voice, aobjects.MessageTypes.round_video):

                # Длительность в секундах
                duration = event.message.media.document.attributes[0].duration
                t = time.time()

                if message_type == aobjects.MessageTypes.voice:
                    file_path = f"media_{user_id}.ogg"
                else:
                    file_path = f"media_{user_id}.mp4"

                time_left = duration / 2 - (time.time() - t)
                if time_left > 0:
                    await asyncio.sleep(time_left)

                while True:
                    if storage.available():
                        break
                    else:
                        await asyncio.sleep(0.1)

                # Скачиваем медиа.
                await event.download_media(file=file_path)
                # Получаем текст.
                text = await achat.convert_to_text(file_path)
                # Удаляем временный файл.
                try:
                    os.remove(file_path)
                except:
                    pass

            # Если это фотография.
            elif message_type == aobjects.MessageTypes.photo:
                pass

            # Если отправлен стикер.
            elif message_type == aobjects.MessageTypes.sticker:
                if astorage.get_history(user_id)["history"]:
                    if not storage.busy(user_id):
                        emojis = ['😀', '😃', '😄', '😁', '😆', '🥹', '😅', '😂', '🤣', '🥲', '☺️', '😊', '😇', '🙂', '😗', '😘', '🥰', '😍', '😌', '😉', '🙃', '😙', '😚', '😋', '😛', '😝', '😜', '🤪']
                        text = random.choice(emojis)
                else:
                    text = "Привет"

            # Если объект не содержит текста.
            elif message_type == aobjects.MessageTypes.other and not astorage.get_history(user_id)["history"]:
                text = "Привет"

            # Если ответ уже в процессе.
            if storage.busy(user_id):
                storage.add_content(user_id, text)
                # Отмечаем сообщение как прочитанное
                try:
                    await event.message.mark_read()
                except:
                    pass

            else:
                storage.add_content(user_id, text)

                t = 5 * random.random()
                await asyncio.sleep(t)
                # Отмечаем сообщение как прочитанное
                try:
                    await event.message.mark_read()
                except:
                    pass

                if config.TEST_MODE:
                    t1 = 7
                else:
                    t1 = 15 + 20 * random.random()
                await asyncio.sleep(t1)
                content = storage.get_content(user_id)

                deepness = None
                answer = None
                has_server_error = False

                while True:
                    try:
                        while True:
                            if storage.available():
                                break
                            else:
                                await asyncio.sleep(0.1)

                        user_storage = astorage.get_history(user_id, deepness)
                        history, deepness = user_storage.values()

                        system_message = {
                            "role": "system",
                            "content": config.ROLE_TEXT
                        }
                        history.insert(0, system_message)
                        history.append({
                            "role": "user",
                            "content": content
                        })

                        if config.TEST_MODE:
                            answer = achat.ask_sync(history)
                        else:
                            answer = await achat.ask(history)

                    except Exception as ee:
                        str_ee = str(ee)
                        if "maximum context length is" in str_ee:
                            deepness -= 1
                            print(f"deepness: {deepness}")
                        elif "The server had an error processing your request" in str_ee:
                            print(f"SERVER ERROR [again: {has_server_error}]: {ee}")
                            if has_server_error:
                                break
                            has_server_error = True
                        else:
                            print(f"ERROR: {ee}")
                            break
                    else:
                        if answer:
                            astorage.save(
                                user_id=user_id,
                                user_message=text,
                                ai_message=answer,
                                deepness=deepness
                            )
                        break

                if answer:
                    sleep_sec = len(answer) / config.TYPING_SPEED * 60

                    # Отображаем анимацию печатания
                    async with event.client.action(event.chat_id, 'typing'):
                        await asyncio.sleep(sleep_sec)

                    # Отвечаем на сообщение тем же текстом
                    await client.send_message(event.chat_id, answer[:4000])

        elif not event.message.out:
            await asyncio.sleep(5)
            # Отмечаем сообщение как прочитанное
            try:
                await event.message.mark_read()
            except:
                pass

    except Exception as err:
        print(f"MEGA ERROR: {err}")


async def async_loop():
    await client.connect()
    print("Цикл взаимодействия с Дайвинчиком запущен.")
    pause_time = 2 if config.TEST_MODE else 60 * 3

    while True:
        await asyncio.sleep(pause_time)

        if client.is_connected():
            await asyncio.sleep(2)
            entity = await client.get_input_entity(int(config.DAVINCI_ID))
            await asyncio.sleep(2)
            messages = await client.get_messages(entity, limit=30)
            await asyncio.sleep(2)
            await client.send_read_acknowledge(entity)

            # Обрабатываем новых собеседников.
            for message in messages:
                try:
                    if not message.out and not message.media and message.entities:
                        message_entiry = message.entities[0].url
                        if not ("t.me/" in message_entiry):
                            raise
                        usr = message_entiry.split("/")[-1]

                        # Проверяем использовался ли такой юзернейм уже в переписке.
                        # И не написал ли он нам сам.
                        if not astorage.has_dialog(usr) and not await has_messages(usr):
                            print(f"NEW DIALOG: {usr}")
                            await asyncio.sleep(2)

                            hello_text = random.choice(config.HELLO_PHRASES)
                            await client.send_message(usr, hello_text)

                except:
                    pass

            last_message = [i for i in messages if not i.out][0]
            last_text = last_message.message

            if "4. Смотреть анкеты" in last_text:
                await client.send_message(entity, "4")

            elif "1. Смотреть анкеты" in last_text:
                await client.send_message(entity, "1")

            elif last_message.media:
                await client.send_message(entity, "❤️")

            elif "1. Показать." in last_text:
                await client.send_message(entity, "1")

            elif "Бот знакомств Дайвинчик🍷 в Telegram! Найдет друзей или даже половинку 👫" in last_text:
                await client.send_message(entity, "Назад")

            elif "Нет такого варианта ответа" in last_text:
                await client.send_message(entity, "/myprofile")

            else:
                await client.send_message(entity, "❤️")


def start_loop(lp):
    # Устанавливаем цикл событий в текущий поток
    asyncio.set_event_loop(lp)
    # Запускаем асинхронную функцию
    lp.run_until_complete(async_loop())


async def main():
    await client.connect()
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if config.DATING_APP_UPDATE:
        tasks = [async_loop(), main()]
    else:
        tasks = [main()]
    loop.run_until_complete(asyncio.gather(*tasks))
