from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from typing import List, Dict, Callable, Optional, Union

class MenuCallbackData(CallbackData, prefix='menu'):
    action: str
    menu_name: str

class ActionCallbackData(CallbackData, prefix='action'):
    action: str
    value: Optional[str] = None

class InlineMenuBuilder:
    def __init__(self):
        self.menus: Dict[str, InlineKeyboardMarkup] = {}
        self.handlers: Dict[str, Callable] = {}

    def create_menu(self, 
                name: str, 
                buttons: List[Union[Dict, List[Dict]]],
                back_menu: Optional[str] = None,
                row_sizes: Optional[List[int]] = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        if row_sizes:
            flat_buttons = []
            for item in buttons:
                if isinstance(item, list):
                    flat_buttons.extend(item)
                else:
                    flat_buttons.append(item)

            for button_info in flat_buttons:
                callback_data = self._get_callback_data(button_info)
                builder.button(
                    text=button_info['text'],
                    callback_data=callback_data
                )

            if back_menu:
                builder.button(
                    text='🔙 Back',
                    callback_data=MenuCallbackData(
                        action='back',
                        menu_name=back_menu
                    ).pack()
                )

            builder.adjust(*row_sizes)
        else:

            for row in buttons:
                if isinstance(row, list):
                    for button_info in row:
                        callback_data = self._get_callback_data(button_info)
                        builder.button(
                            text=button_info['text'],
                            callback_data=callback_data
                        )
                    builder.adjust(len(row))
                else:

                    button_info = row
                    callback_data = self._get_callback_data(button_info)
                    builder.button(
                        text=button_info['text'],
                        callback_data=callback_data
                    )
                    builder.adjust(1)

            if back_menu:

                builder.button(
                    text='🔙 Back',
                    callback_data=MenuCallbackData(
                        action='back',
                        menu_name=back_menu
                    ).pack()
                )
                builder.adjust(1)

        markup = builder.as_markup()
        self.menus[name] = markup
        return markup

    def _get_callback_data(self, button_info):
        if 'menu' in button_info:
            return MenuCallbackData(
                action='open',
                menu_name=button_info['menu']
            ).pack()
        else:
            return ActionCallbackData(
                action=button_info['action'],
                value=button_info.get('value')
            ).pack()

    def get_menu(self, name: str) -> Optional[InlineKeyboardMarkup]:
        return self.menus.get(name)

    def register_handler(self, action: str, handler: Callable):
        self.handlers[action] = handler

    def get_handler(self, action: str) -> Optional[Callable]:
        return self.handlers.get(action)
