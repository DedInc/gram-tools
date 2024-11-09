# gram_tools

Utilities for streamlined [aiogram 3](https://github.com/aiogram/aiogram) bot development.

## Features

- 📦 **Message Packing**: Serialize and deserialize Telegram messages with support for all media types
- 🗄️ **Asset Management**: Efficient handling of media files with caching and file_id reuse
- 📚 **CRUD Operations**: Generic async CRUD operations for SQLAlchemy models
- ⌨️ **Pagination**: Flexible inline keyboard pagination with search capability
- 🔧 **Template System**: Simple template system for message text formatting

## Installation

```bash
pip install gram-tools
```

## Components

### Message Packer

Pack and unpack Telegram messages with all their content for easy storage and reuse.

```python
from gram_tools.packer import pack_message, unpack_message, send_packed_message, answer_packed_message

# Pack a message
packed = await pack_message(message)

# Send packed message
await send_packed_message(bot, chat_id, packed)

# Answer with packed message
await answer_packed_message(message, packed)
```

### Whole example

```python
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command

from gram_tools.packer import (
    pack_message,
    send_packed_message,
)

API_TOKEN = "BOT TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# In-memory storage for packed messages
packed_messages = {}

@router.message(Command("save"))
async def save_message(message: Message):
    if not message.reply_to_message:
        await message.answer("Please reply to the message you want to save.")
        return

    # Pack the replied message
    packed = await pack_message(message.reply_to_message)

    # Store the packed message using user's chat ID
    packed_messages[message.from_user.id] = packed
    await message.answer("Message saved!")

@router.message(Command("send"))
async def send_saved_message(message: Message):
    packed = packed_messages.get(message.from_user.id)
    if not packed:
        await message.answer("No message saved. Use /save to save a message.")
        return

    # Send the packed message back to the user
    await send_packed_message(bot, message.chat.id, packed)

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### Asset Management

Efficiently handle media files with automatic file_id caching.

```python
from gram_tools.assets import answer_with_asset, send_with_asset

# Send media file
await send_with_asset(bot, chat_id, "path/to/file.jpg", caption="My photo") # also u can without caption, and also you can use reply_markup and more

# Answer with media file
await answer_with_asset(message, "path/to/file.mp4")
```

### Whole example how to use

```python
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command

from gram_tools.assets import send_with_asset, answer_with_asset

API_TOKEN = "BOT TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(Command("photo"))
async def send_photo(message: Message):
    await send_with_asset(
        bot,
        chat_id=message.chat.id,
        file_path=r"D:\Dokumenti\Pictures\photo_2024-08-11_18-25-01.jpg",
        caption="Here is a photo!"
    )

@router.message(Command("video"))
async def send_video(message: Message):
    await answer_with_asset(
        message=message,
        file_path=r"D:\Dokumenti\Documents\Untitled.mp4",
        caption="Here is a video!"
    )

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

```

Supported media types:
- Photos: jpg, jpeg, png, svg, webp, bmp, jfif, heic, heif
- Videos: mp4, mov, avi, mkv, m4v, 3gp
- Audio: mp3, wav, flac, m4a, ogg, aac
- Voice: ogg, oga
- Animations: gif
- Any other file type as document

### CRUD Operations

Generic CRUD operations for SQLAlchemy models.

```python
from gram_tools.crud import get_crud
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    name = Column(String)


user_crud = get_crud(User)

# Add new instance
await user_crud.add(session, user)

# Get instance
user = await user_crud.get(session, id=1)

# Get all instances
active_users = await user_crud.get_all(session, status="active")

# Get count of instances
active_users_count = await user_crud.get_all_count(session, status="active")

# Update instance
await user_crud.update(session, user, name="New Name")

# Delete instance
await user_crud.delete(session, user)
```

### Pagination Keyboards

Create paginated inline keyboards with optional search functionality.

```python
from gram_tools.keyboards import InlineBuilder, SearchButton

# Create pagination with search
builder = InlineBuilder(
    per_page=5,
    layout=1,
    search_button=SearchButton("🔍")
)

items = ["Item 1", "Item 2", "Item 3", ...]
keyboard = builder.get_paginated(items, page=1)

# With search
keyboard = builder.get_paginated(items, page=1, search_term="search query")
```

Customization options:
- `per_page`: Items per page
- `layout`: Number of buttons per row
- `next_button_text`: Next page button text
- `prev_button_text`: Previous page button text
- `page_callback_prefix`: Optional callback prefix of core paginator and item selection
- `ignore_callback_prefix`: Optional callback prefox on click ignore items
- `not_exist_page`: Text for disabled navigation buttons
- `search_button`: Optional search button configuration

### Whole example:

```python
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from gram_tools.keyboards import (
    InlineBuilder,
    SearchButton
)

API_TOKEN = "7350010616:AAHQXoWzmMuffBkv5mPAI2-cBziZBkvoTI8"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

items = [f"Item {i}" for i in range(1, 21)]
search_button = SearchButton(button_text="🔍 Search")
inline_builder = InlineBuilder(per_page=5, search_button=search_button)

class Form(StatesGroup):
    waiting_for_search_term = State()

@router.message(Command("start"))
async def show_inline_keyboard(message: Message, state: FSMContext):
    await state.clear()
    keyboard = inline_builder.get_paginated(items, page=1)
    await message.answer("Select an item:", reply_markup=keyboard)

@router.callback_query(inline_builder.page_callback.filter())
async def handle_callback(callback: CallbackQuery, callback_data: inline_builder.page_callback, state: FSMContext):
    action = callback_data.action
    value = callback_data.value

    data = await state.get_data()
    search_term = data.get('search_term')

    if action in ("next", "prev"):
        page = value
        keyboard = inline_builder.get_paginated(items, page=page, search_term=search_term)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
    elif action == "sel":
        item_index = value
        if search_term:
            filtered_items = [item for item in items if search_term.lower() in str(item).lower()]
        else:
            filtered_items = items

        if 0 <= item_index < len(filtered_items):
            selected_item = filtered_items[item_index]
            await callback.message.answer(f"You selected: {selected_item}")
        else:
            await callback.message.answer("Element not found.")
        await callback.answer()

@router.callback_query(search_button.search_callback.filter())
async def handle_search_callback(callback: CallbackQuery, state: FSMContext):
    print(callback.data)
    await state.update_data(search_term=None)
    await callback.message.answer("Type text to search:")
    await state.set_state(Form.waiting_for_search_term)
    await callback.answer()

@router.message(Form.waiting_for_search_term)
async def perform_search(message: Message, state: FSMContext):
    search_term = message.text
    await state.update_data(search_term=search_term)
    await state.set_state(None)

    keyboard = inline_builder.get_paginated(items, page=1, search_term=search_term)

    if keyboard.inline_keyboard:
        await message.answer("Results:", reply_markup=keyboard)
    else:
        await message.answer("Nothing found.")

@router.callback_query(inline_builder.ignore_callback.filter())
async def handle_ignore_callback(callback: CallbackQuery):
    await callback.answer()

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### Template System

Simple template system for message text formatting.

```python
from gram_tools.messages import T

template = T("Hello, ${name}!")
text = template.text(name="User")
```

### Whole example

```python
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command

from gram_tools.messages import T

API_TOKEN = "BOT TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Define a template
welcome_template = T("Hello, ${name}! Welcome to our bot.")

@router.message(Command("start"))
async def send_welcome(message: Message):
    # Render the template with the user's name
    text = welcome_template.text(name=message.from_user.full_name)
    await message.answer(text)

@router.message(Command("info"))
async def send_info(message: Message):
    info_template = T(
        "User Info:\n"
        "- ID: ${id}\n"
        "- Username: ${username}\n"
        "- First Name: ${first_name}\n"
        "- Last Name: ${last_name}"
    )
    text = info_template.text(
        id=message.from_user.id,
        username=message.from_user.username or "N/A",
        first_name=message.from_user.first_name or "N/A",
        last_name=message.from_user.last_name or "N/A"
    )
    await message.answer(text)

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.