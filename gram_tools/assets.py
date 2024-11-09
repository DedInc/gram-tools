import os
import hashlib
import tempfile
from pathlib import Path

import aiofiles
import orjson
from aiogram import Bot
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile

TEMP = tempfile.gettempdir()
ATTACHMENTS_PATH = Path(TEMP) / 'attachments.json'
HASHES_PATH = Path(TEMP) / 'hashes.json'

CONTENT_TYPES = {
    'photo': {'jpg', 'jpeg', 'png', 'svg', 'webp', 'bmp', 'jfif', 'heic', 'heif'},    
    'video': {'mp4', 'mov', 'avi', 'mkv', 'm4v', '3gp'},    
    'audio': {'mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac'},    
    'voice': {'ogg', 'oga'},
    'animation': {'gif'}
}

async def get_hash(file_path: str) -> str:
    md5_hash = hashlib.md5()
    async with aiofiles.open(file_path, 'rb') as file:
        while True:
            byte_block = await file.read(4096)
            if not byte_block:
                break
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

async def load_json(path: Path) -> dict:
    if path.exists():
        async with aiofiles.open(path, 'rb') as f:
            return orjson.loads(await f.read())
    return {}

async def save_json(path: Path, data: dict) -> None:
    async with aiofiles.open(path, 'wb') as f:
        await f.write(orjson.dumps(data))

async def get_file_id(file_path: str) -> str:
    file_hash = await get_hash(file_path)
    hashes = await load_json(HASHES_PATH)
    attachments = await load_json(ATTACHMENTS_PATH)

    if hashes.get(file_path) != file_hash:
        return None

    return attachments.get(file_hash)

async def update_file_id(file_path: str, file_id: str) -> None:
    file_hash = await get_hash(file_path)
    hashes = await load_json(HASHES_PATH)
    attachments = await load_json(ATTACHMENTS_PATH)

    old_hash = hashes.get(file_path)

    hashes[file_path] = file_hash

    if old_hash and old_hash != file_hash:
        attachments.pop(old_hash, None)

    attachments[file_hash] = file_id

    await save_json(HASHES_PATH, hashes)
    await save_json(ATTACHMENTS_PATH, attachments)

def get_content_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower().lstrip('.')
    
    for content_type, extensions in CONTENT_TYPES.items():
        if ext in extensions:
            return content_type
    return 'document'

async def answer_with_asset(message: Message, file_path: str, **kwargs) -> Message:
    content_type = get_content_type(file_path)
    answer_method = getattr(message, f'answer_{content_type}')
    
    file_id = await get_file_id(file_path)
    
    if file_id:
        try:
            return await answer_method(file_id, **kwargs)
        except Exception:
            file_id = None
    
    input_file = FSInputFile(file_path)
    answered_message = await answer_method(input_file, **kwargs)
    
    if answered_message:
        new_file_id = None
        if content_type == 'photo':
            new_file_id = answered_message.photo[-1].file_id
        elif hasattr(answered_message, content_type):
            new_file_id = getattr(answered_message, content_type).file_id
            
        if new_file_id:
            await update_file_id(file_path, new_file_id)
    
    return answered_message

async def send_with_asset(bot: Bot, chat_id: int | str, file_path: str, **kwargs) -> Message:
    content_type = get_content_type(file_path)
    send_method = getattr(bot, f'send_{content_type}')
    
    file_id = await get_file_id(file_path)    
    
    if file_id:
        try:
            return await send_method(chat_id, file_id, **kwargs)
        except Exception:
            file_id = None
    
    input_file = FSInputFile(file_path)
    sent_message = await send_method(chat_id, input_file, **kwargs)
    
    if sent_message:
        new_file_id = None
        if content_type == 'photo':
            new_file_id = sent_message.photo[-1].file_id
        elif hasattr(sent_message, content_type):
            new_file_id = getattr(sent_message, content_type).file_id
            
        if new_file_id:
            await update_file_id(file_path, new_file_id)
    
    return sent_message
