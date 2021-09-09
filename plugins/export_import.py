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

from utils import get_buttons, is_admin, get_playlist_str, shuffle_playlist, import_play_list
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from logger import LOGGER
import json
import os

admin_filter=filters.create(is_admin)   


@Client.on_message(filters.command(["export", f"export@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def export_play_list(client, message: Message):
    if not Config.playlist:
        await message.reply_text("Playlist is Empty")
        return
    file=f"{message.chat.id}_{message.message_id}.json"
    with open(file, 'w+') as outfile:
        json.dump(Config.playlist, outfile, indent=4)
    await client.send_document(chat_id=message.chat.id, document=file, file_name="PlayList.json", caption=f"Playlist\n\nNumber Of Songs: <code>{len(Config.playlist)}</code>\n\nJoin [XTZ Bots](https://t.me/subin_works)")
    try:
        os.remove(file)
    except:
        pass

@Client.on_message(filters.command(["import", f"import@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def import_playlist(client, m: Message):
    if m.reply_to_message is not None and m.reply_to_message.document:
        if m.reply_to_message.document.file_name != "PlayList.json":
            k=await m.reply("Invalid PlayList file given. Use @GetPlayListBot to get a playlist file. Or Export your current Playlist using /export.")
            return
        myplaylist=await m.reply_to_message.download()
        status=await m.reply("Trying to get details from playlist.")
        n=await import_play_list(myplaylist)
        if not n:
            await status.edit("Errors Occured while importing playlist.")
            return
        if Config.SHUFFLE:
            await shuffle_playlist()
        pl=await get_playlist_str()
        if m.chat.type == "private":
            await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())        
        elif not Config.LOG_GROUP and m.chat.type == "supergroup":
            await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())
        else:
            await status.delete()
    else:
        await m.reply("No playList file given. Use @GetPlayListBot  or search for a playlist in @DumpPlaylist to get a playlist file.")
