# gram_tools

Utilities for streamlined [aiogram 3](https://github.com/aiogram/aiogram) bot development.

## Features

- 📦 **Message Packing**: Serialize and deserialize Telegram messages with support for all media types
- 🗄️ **Asset Management**: Efficient handling of media files with caching and file_id reuse
- 📚 **CRUD Operations**: Generic async CRUD operations for SQLAlchemy models
- ⌨️ **Pagination**: Flexible inline keyboard pagination with search capability
- 🧩 **Menu Builder**: Create complex nested menus with ease
- 🎯 **FSM Visualizer**: Generate visual diagrams of your Finite State Machines (FSM)

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

#### Whole Example

```python
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from gram_tools.packer import pack_message, send_packed_message

API_TOKEN = "YOUR_BOT_TOKEN"

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

Efficiently handle media files with automatic `file_id` caching.

```python
from gram_tools.assets import answer_with_asset, send_with_asset

# Send media file
await send_with_asset(bot, chat_id, "path/to/file.jpg", caption="My photo")  # Optional caption and other parameters

# Answer with media file
await answer_with_asset(message, "path/to/file.mp4")
```

#### Whole Example

```python
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from gram_tools.assets import send_with_asset, answer_with_asset

API_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(Command("photo"))
async def send_photo(message: Message):
    await send_with_asset(
        bot,
        chat_id=message.chat.id,
        file_path="path/to/your/photo.jpg",
        caption="Here is a photo!"
    )

@router.message(Command("video"))
async def send_video(message: Message):
    await answer_with_asset(
        message=message,
        file_path="path/to/your/video.mp4",
        caption="Here is a video!"
    )

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

**Supported Media Types:**

- **Photos**: jpg, jpeg, png, svg, webp, bmp, jfif, heic, heif
- **Videos**: mp4, mov, avi, mkv, m4v, 3gp
- **Audio**: mp3, wav, flac, m4a, ogg, aac
- **Voice**: ogg, opus
- **Animations**: gif
- **Documents**: Any other file type

### CRUD Operations

Generic CRUD operations for SQLAlchemy models.

```python
from gram_tools.crud import get_crud
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
from gram_tools.keyboards.pagination import InlinePageBuilder, SearchButton

# Create pagination with search
builder = InlinePageBuilder(
    per_page=5,
    layout=1,
    search_button=SearchButton("🔍")
)

items = ["Item 1", "Item 2", "Item 3", ...]
keyboard = builder.get_paginated(items, page=1)

# With search
keyboard = builder.get_paginated(items, page=1, search_term="search query")
```

**Customization Options:**

- `per_page`: Items per page
- `layout`: Number of buttons per row
- `next_button_text`: Next page button text
- `prev_button_text`: Previous page button text
- `page_callback_prefix`: Optional callback prefix of core paginator and item selection
- `ignore_callback_prefix`: Optional callback prefix on click ignore items
- `not_exist_page`: Text for disabled navigation buttons
- `search_button`: Optional search button configuration

#### Whole Example

```python
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from gram_tools.keyboards.pagination import InlinePageBuilder, SearchButton

API_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

items = [f"Item {i}" for i in range(1, 21)]
search_button = SearchButton(button_text="🔍 Search")
inline_builder = InlinePageBuilder(per_page=5, search_button=search_button)

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

### Menu Builder

Create complex nested menus with ease.

```python
from gram_tools.keyboards.menu import InlineMenuBuilder, MenuCallbackData, ActionCallbackData

# Initialize the menu builder
menu_builder = InlineMenuBuilder()

# Define menus and buttons
main_menu_buttons = [
    {'text': '➡️ Go to Submenu 1', 'menu': 'submenu1'},
    {'text': '📋 Option in Main Menu', 'action': 'option_main'},
    {'text': 'ℹ️ Info', 'action': 'info'},
    {'text': '⚙️ Settings', 'menu': 'settings_menu'}
]

submenu1_buttons = [
    {'text': '📋 Option in Submenu 1', 'action': 'option_sub1'},
    {'text': '⬅️ Back to Main Menu', 'menu': 'main_menu'}
]

settings_menu_buttons = [
    {'text': '🔔 Notifications', 'action': 'notifications'},
    {'text': '🌐 Language', 'action': 'language'},
    {'text': '🔒 Privacy', 'action': 'privacy'},
    {'text': '⬅️ Back to Main Menu', 'menu': 'main_menu'}
]

# Create menus with row sizes
menu_builder.create_menu('main_menu', main_menu_buttons, row_sizes=[2, 2])
menu_builder.create_menu('submenu1', submenu1_buttons, row_sizes=[1, 1])
menu_builder.create_menu('settings_menu', settings_menu_buttons, row_sizes=[2, 1])

# Register action handlers
@router.callback_query(ActionCallbackData.filter())
async def handle_action(callback: CallbackQuery, callback_data: ActionCallbackData):
    action = callback_data.action
    value = callback_data.value
    handler = menu_builder.get_handler(action)
    if handler:
        await handler(callback, value)
    else:
        await callback.message.answer(f"Action '{action}' is not handled.")
    await callback.answer()

@router.callback_query(MenuCallbackData.filter())
async def handle_menu(callback: CallbackQuery, callback_data: MenuCallbackData):
    action = callback_data.action
    menu_name = callback_data.menu_name
    if action in ('open', 'back'):
        markup = menu_builder.get_menu(menu_name)
        if markup:
            await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()

# Action Handlers
async def option_main_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("You selected an option in the Main Menu.")

async def info_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("This is some information about the bot.")

async def notifications_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("Notification settings.")

async def language_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("Language settings.")

async def privacy_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("Privacy settings.")

async def option_sub1_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("You selected an option in Submenu 1.")

# Register the handlers
menu_builder.register_handler('option_main', option_main_handler)
menu_builder.register_handler('info', info_handler)
menu_builder.register_handler('notifications', notifications_handler)
menu_builder.register_handler('language', language_handler)
menu_builder.register_handler('privacy', privacy_handler)
menu_builder.register_handler('option_sub1', option_sub1_handler)

# Start command handler
@router.message(Command("start"))
async def start_cmd(message: Message):
    markup = menu_builder.get_menu('main_menu')
    await message.answer("Welcome to the bot. Choose an option:", reply_markup=markup)
```

#### Whole Example

```python
import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from gram_tools.keyboards.menu import InlineMenuBuilder, MenuCallbackData, ActionCallbackData

API_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

menu_builder = InlineMenuBuilder()

# Define menus and buttons

# Main Menu with buttons per row specified
main_menu_buttons = [
    {'text': '➡️ Go to Submenu 1', 'menu': 'submenu1'},
    {'text': '📋 Option in Main Menu', 'action': 'option_main'},
    {'text': 'ℹ️ Info', 'action': 'info'},
    {'text': '⚙️ Settings', 'menu': 'settings_menu'}
]

# Submenu 1
submenu1_buttons = [
    {'text': '📋 Option in Submenu 1', 'action': 'option_sub1'},
    {'text': '⬅️ Back to Main Menu', 'menu': 'main_menu'}
]

# Settings Menu with custom row sizes
settings_menu_buttons = [
    {'text': '🔔 Notifications', 'action': 'notifications'},
    {'text': '🌐 Language', 'action': 'language'},
    {'text': '🔒 Privacy', 'action': 'privacy'},
    {'text': '⬅️ Back to Main Menu', 'menu': 'main_menu'}
]

# Create menus with row_sizes
menu_builder.create_menu('main_menu', main_menu_buttons, row_sizes=[2, 2])
menu_builder.create_menu('submenu1', submenu1_buttons, row_sizes=[1, 1])
menu_builder.create_menu('settings_menu', settings_menu_buttons, row_sizes=[2, 1])

# Register action handlers
@router.callback_query(ActionCallbackData.filter())
async def handle_action(callback: CallbackQuery, callback_data: ActionCallbackData):
    action = callback_data.action
    value = callback_data.value
    handler = menu_builder.get_handler(action)
    if handler:
        await handler(callback, value)
    else:
        await callback.message.answer(f"Action '{action}' is not handled.")
    await callback.answer()

@router.callback_query(MenuCallbackData.filter())
async def handle_menu(callback: CallbackQuery, callback_data: MenuCallbackData):
    action = callback_data.action
    menu_name = callback_data.menu_name
    if action in ('open', 'back'):
        markup = menu_builder.get_menu(menu_name)
        if markup:
            await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()

# Action Handlers
async def option_main_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("You selected an option in the Main Menu.")

async def info_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("This is some information about the bot.")

async def notifications_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("Notification settings.")

async def language_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("Language settings.")

async def privacy_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("Privacy settings.")

async def option_sub1_handler(callback: CallbackQuery, value: Optional[str]):
    await callback.message.answer("You selected an option in Submenu 1.")

# Register the handlers
menu_builder.register_handler('option_main', option_main_handler)
menu_builder.register_handler('info', info_handler)
menu_builder.register_handler('notifications', notifications_handler)
menu_builder.register_handler('language', language_handler)
menu_builder.register_handler('privacy', privacy_handler)
menu_builder.register_handler('option_sub1', option_sub1_handler)

# Start command handler
@router.message(Command("start"))
async def start_cmd(message: Message):
    markup = menu_builder.get_menu('main_menu')
    await message.answer("Welcome to the bot. Choose an option:", reply_markup=markup)

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### FSM Visualizer

Easily generate visual diagrams of your Finite State Machines (FSM) defined in your aiogram bot by analyzing your bot's Python code. The visualize_fsm function parses your bot's code to extract handlers, FSM states, and transitions, and generates a visual representation of the FSM using NetworkX and Matplotlib.


#### How to Use

1. **Import the Visualizer Function**

   Add the following import statement to your script:

   ```python
   from gram_tools.visual import visualize_fsm
   ```

2. **Call the Visualizer Function**

   Use the `visualize_fsm` function, providing the path to your Python file containing the FSM definitions:

   ```python
   visualize_fsm('path/to/your_code.py')
   ```

   This will generate an image representing the FSM.

#### Example

Suppose you have a bot script `bot.py` with FSM states defined:

```python
# bot.py

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

API_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()

@router.message(Command('register'))
async def cmd_register(message: types.Message, state: FSMContext):
    await message.answer("What's your name?")
    await state.set_state(Registration.waiting_for_name)

@router.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("What's your email?")
    await state.set_state(Registration.waiting_for_email)

@router.message(Registration.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer(f"Registration complete! Name: {user_data['name']}, Email: {message.text}")
    await state.clear()
```

To visualize the FSM, create a separate script

```python
from gram_tools.visual import visualize_fsm

visualize_fsm('bot.py')
```

Run this script:

```bash
python visualize.py
```

This will generate an image representing the FSM in your `bot.py`:

![FSM Diagram](fsm.png)

#### Additional Information

- The `visualize_fsm` function parses your Python code to extract FSM states and transitions.
- It supports aiogram's FSM implementations using `StatesGroup` and `State`.
- The generated diagram can help in understanding and debugging the flow of states in your bot.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
