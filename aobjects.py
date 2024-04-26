import telethon.tl.types


class MessageTypes:
    voice = "voice"
    round_video = "round_video"
    text = "text"
    other = "other"
    photo = "photo"
    photo_doc = "photo_doc"
    sticker = "sticker"


def get_message_type(event) -> str:
    try:
        if event.message.message:
            return MessageTypes.text
        try:
            if event.message.media.photo:
                return MessageTypes.photo
        except:
            pass
        try:
            if event.message.media.document.mime_type in ("image/png", "image/jpeg"):
                return MessageTypes.photo_doc
        except:
            pass
        try:
            if event.message.media.document.mime_type == "audio/ogg":
                return MessageTypes.voice
        except:
            pass
        try:
            if all((
                event.message.media.document.mime_type == "video/mp4",
                event.message.media.document.attributes[0].round_message
            )):
                return MessageTypes.round_video
        except:
            pass
        try:
            if isinstance(event.message.media, telethon.tl.types.MessageMediaUnsupported):
                return MessageTypes.sticker

        except:
            pass

        raise
    except:
        return MessageTypes.other
