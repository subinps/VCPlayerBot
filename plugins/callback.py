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

from utils import get_admins, get_buttons, get_playlist_str, mute, pause, restart_playout, resume, seek_file, shuffle_playlist, skip, unmute
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
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
        except MessageNotModified:
            pass

    elif query.data.lower() == "pause":
        if Config.PAUSE:
            await query.answer("Already Paused", show_alert=True)
        else:
            await pause()
            await sleep(1)
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
        except MessageNotModified:
            pass
    
    elif query.data.lower() == "resume":   
        if not Config.PAUSE:
            await query.answer("Nothing Paused to resume", show_alert=True)
        else:
            await resume()
            await sleep(1)
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
        except MessageNotModified:
            pass

    elif query.data=="skip":   
        if not Config.playlist:
            await query.answer("No songs in playlist", show_alert=True)
        else:
            await skip()
            await sleep(1)
        if Config.playlist:
            title=f"<b>{Config.playlist[0][1]}</b>"
        elif Config.STREAM_LINK:
            title=f"<b>Stream Using [Url]({Config.DATA['FILE_DATA']['file']}</b>)"
        else:
            title=f"<b>Streaming Startup [stream]({Config.STREAM_URL})</b>"

        try:
            await query.message.edit(f"<b>{title}</b>",
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
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
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
    elif query.data.lower() == "mute":
        if Config.MUTED:
            await unmute()
        else:
            await mute()
        await sleep(1)
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
        except MessageNotModified:
            pass
    elif query.data.lower() == 'seek':
        if not Config.CALL_STATUS:
            return await query.answer("Not Playing anything.", show_alert=True)
        if not (Config.playlist or Config.STREAM_LINK):
            return await query.answer("Startup stream cant be seeked.", show_alert=True)
        data=Config.DATA.get('FILE_DATA')
        if not data.get('dur', 0) or \
            data.get('dur') == 0:
            return await query.answer("This stream cant be seeked..", show_alert=True)
        k, reply = await seek_file(10)
        if k == False:
            return await query.answer(reply, show_alert=True)
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
        except MessageNotModified:
            pass
    elif query.data.lower() == 'rewind':
        if not Config.CALL_STATUS:
            return await query.answer("Not Playing anything.", show_alert=True)
        if not (Config.playlist or Config.STREAM_LINK):
            return await query.answer("Startup stream cant be seeked.", show_alert=True)
        data=Config.DATA.get('FILE_DATA')
        if not data.get('dur', 0) or \
            data.get('dur') == 0:
            return await query.answer("This stream cant be seeked..", show_alert=True)
        k, reply = await seek_file(-10)
        if k == False:
            return await query.answer(reply, show_alert=True)
        try:
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
        except MessageNotModified:
            pass

    await query.answer()


