#!/usr/bin/env python3
# Copyright (C) @subinps
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from utils import get_admins, get_buttons, get_playlist_str, pause, restart_playout, resume, shuffle_playlist, skip
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
from pyrogram import Client
from config import Config
from asyncio import sleep
from logger import LOGGER

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    admins = await get_admins(Config.CHAT)
    if query.from_user.id not in admins and query.data != "help":
        await query.answer(
            "😒 Played Joji.mp3",
            show_alert=True
            )
        return
    if query.data == "shuffle":
        if not Config.playlist:
            await query.answer("Playlist is empty.", show_alert=True)
            return
        await shuffle_playlist()
        await sleep(1)
        pl=await get_playlist_str()
        
        try:
            await query.message.edit(
                    f"{pl}",
                    parse_mode="Markdown",
                    reply_markup=await get_buttons()
            )
        except MessageNotModified:
            pass

    elif query.data.lower() == "pause":
        if Config.PAUSE:
            await query.answer("Already Paused", show_alert=True)
        else:
            await pause()
            await sleep(1)
        pl=await get_playlist_str()
        try:
            await query.message.edit(f"{pl}",
                disable_web_page_preview=True,
                reply_markup=await get_buttons()
            )
        except MessageNotModified:
            pass
    
    elif query.data.lower() == "resume":   
        if not Config.PAUSE:
            await query.answer("Nothing Paused to resume", show_alert=True)
        else:
            await resume()
            await sleep(1)
        pl=await get_playlist_str()
        try:
            await query.message.edit(f"{pl}",
                disable_web_page_preview=True,
                reply_markup=await get_buttons()
            )
        except MessageNotModified:
            pass

    elif query.data=="skip":   
        if not Config.playlist:
            await query.answer("No songs in playlist", show_alert=True)
        else:
            await skip()
            await sleep(1)
        pl=await get_playlist_str()
        try:
            await query.message.edit(f"{pl}",
                disable_web_page_preview=True,
                reply_markup=await get_buttons()
            )
        except MessageNotModified:
            pass
    elif query.data=="replay":
        if not Config.playlist:
            await query.answer("No songs in playlist", show_alert=True)
        else:
            await restart_playout()
            await sleep(1)
        pl=await get_playlist_str()
        try:
            await query.message.edit(f"{pl}",
                disable_web_page_preview=True,
                reply_markup=await get_buttons()
            )
        except MessageNotModified:
            pass

    elif query.data=="help":
        buttons = [
            [
                InlineKeyboardButton('⚙️ Update Channel', url='https://t.me/subin_works'),
                InlineKeyboardButton('🧩 Source', url='https://github.com/subinps/VCPlayerBot'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        try:
            await query.message.edit(
                Config.HELP,
                reply_markup=reply_markup

            )
        except MessageNotModified:
            pass
    await query.answer()

