from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from typing import List, Any, Optional

class SearchButton:
    def __init__(
        self, 
        button_text: str = '🔍', 
        callback_prefix: str = 'search'
    ):
        self.button_text = button_text

        class DynamicSearchCallbackData(CallbackData, prefix=callback_prefix):
            pass

        self.search_callback = DynamicSearchCallbackData

    def create_button(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=self.button_text,
            callback_data=self.search_callback().pack()
        )

class InlinePageBuilder:
    def __init__(
        self, 
        per_page: int = 5, 
        layout: int = 1,  
        next_button_text: str = '↪️', 
        prev_button_text: str = '↩️',
        page_callback_prefix: str = 'page',
        ignore_callback_prefix: str = 'ignore',
        id_sep: str = ':', 
        not_exist_page: str = '⛔',
        search_button: Optional[SearchButton] = None
    ):
        self.per_page = per_page
        self.layout = layout  
        self.next_button_text = next_button_text
        self.prev_button_text = prev_button_text
        self.id_sep = id_sep
        self.not_exist_page = not_exist_page
        self.search_button = search_button

        class DynamicPageCallbackData(CallbackData, prefix=page_callback_prefix):
            action: str
            value: int

        self.page_callback = DynamicPageCallbackData

        class DynamicIgnoreCallbackData(CallbackData, prefix=ignore_callback_prefix):
            pass

        self.ignore_callback = DynamicIgnoreCallbackData

    def get_paginated(
        self, 
        items: List[Any], 
        page: int = 1, 
        search_term: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        if search_term:
            items = [item for item in items if search_term.lower() in str(item).lower()]

        total_items = len(items)
        total_pages = (total_items + self.per_page - 1) // self.per_page
        page = max(1, min(page, total_pages))

        start_index = (page - 1) * self.per_page
        end_index = start_index + self.per_page
        items_on_page = items[start_index:end_index]

        for idx, item in enumerate(items_on_page):
            button_text = str(item)
            item_index = start_index + idx
            callback_data = self.page_callback(
                action='sel', 
                value=item_index
            ).pack()
            builder.add(InlineKeyboardButton(
                text=button_text, 
                callback_data=callback_data
            ))

        builder.adjust(self.layout)

        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text=self.prev_button_text,
                callback_data=self.page_callback(
                    action='prev', 
                    value=page - 1
                ).pack()
            ))
        else:
            nav_buttons.append(InlineKeyboardButton(
                text=self.not_exist_page,
                callback_data=self.ignore_callback().pack()
            ))

        if self.search_button:
            nav_buttons.append(self.search_button.create_button())

        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text=self.next_button_text,
                callback_data=self.page_callback(
                    action='next', 
                    value=page + 1
                ).pack()
            ))
        else:
            nav_buttons.append(InlineKeyboardButton(
                text=self.not_exist_page,
                callback_data=self.ignore_callback().pack()
            ))

        if nav_buttons:
            builder.row(*nav_buttons)

        return builder.as_markup()
