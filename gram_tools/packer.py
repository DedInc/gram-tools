from aiogram import Bot
from aiogram.types import Message
import orjson
import base64

async def pack_message(message: Message):

    content = {}
    if message.content_type == 'photo':
        content = {'photo': message.photo[-1].file_id}
    elif message.content_type == 'video':
        content = {'video': message.video.file_id}
    elif message.content_type == 'audio':
        content = {'audio': message.audio.file_id}
    elif message.content_type == 'document':
        content = {'document': message.document.file_id}
    elif message.content_type == 'voice':
        content = {'voice': message.voice.file_id}
    elif message.content_type == 'sticker':
        content = {'sticker': message.sticker.file_id}
    elif message.content_type == 'animation':
        content = {'animation': message.animation.file_id}

    message_data = {
        'text': message.text,
        'caption': message.caption,
        'content_type': message.content_type,
        **content  
    }

    message_data = {k: v for k, v in message_data.items() if v is not None}

    temple = orjson.dumps(message_data)
    return base64.b64encode(temple).decode()

async def unpack_message(packed_message: str):

    unpacked_str = base64.b64decode(packed_message.encode()).decode()
    return orjson.loads(unpacked_str)

async def send_packed_message(bot: Bot, chat_id: int | str, packed_message: str):
    message_data = await unpack_message(packed_message)
    content_type = message_data.pop('content_type')
    
    if content_type == 'text':
        await bot.send_message(chat_id, **message_data)
    else:
        send_message = getattr(bot, f'send_{content_type}')
        await send_message(chat_id, **message_data)

async def answer_packed_message(message: Message, packed_message: str):
    message_data = await unpack_message(packed_message)
    content_type = message_data.pop('content_type')
    
    if content_type == 'text':
        await message.answer(**message_data)
    else:
        answer = getattr(message, f'answer_{content_type}')
        await answer(**message_data)
