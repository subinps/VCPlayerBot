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

from utils import get_playlist_str, is_admin, mute, restart_playout, skip, pause, resume, unmute, volume, get_buttons, is_admin, seek_file, get_player_string
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from logger import LOGGER

admin_filter=filters.create(is_admin)   

@Client.on_message(filters.command(["playlist", f"playlist@{Config.BOT_USERNAME}"]) & (filters.chat(Config.CHAT) | filters.private))
async def player(client, message):
    pl = await get_playlist_str()
    if message.chat.type == "private":
        await message.reply_text(
            pl,
            disable_web_page_preview=True,
        )
    else:
        if Config.msg.get('playlist') is not None:
            await Config.msg['playlist'].delete()
        Config.msg['playlist'] = await message.reply_text(
            pl,
            disable_web_page_preview=True,
        )

@Client.on_message(filters.command(["skip", f"skip@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def skip_track(_, m: Message):
    if not Config.playlist:
        await m.reply("Playlist is Empty.\nLive Streaming.")
        return
    if len(m.command) == 1:
        await skip()
    else:
        try:
            items = list(dict.fromkeys(m.command[1:]))
            items = [int(x) for x in items if x.isdigit()]
            items.sort(reverse=True)
            for i in items:
                if 2 <= i <= (len(Config.playlist) - 1):
                    Config.playlist.pop(i)
                    await m.reply(f"Succesfully Removed from Playlist- {i}. **{Config.playlist[i][1]}**")
                else:
                    await m.reply(f"You Cant Skip First Two Songs- {i}")
        except (ValueError, TypeError):
            await m.reply_text("Invalid input")
    pl=await get_playlist_str()
    if m.chat.type == "private":
        await m.reply_text(pl, disable_web_page_preview=True, reply_markup=await get_buttons())
    elif not Config.LOG_GROUP and m.chat.type == "supergroup":
        await m.reply_text(pl, disable_web_page_preview=True, reply_markup=await get_buttons())

@Client.on_message(filters.command(["pause", f"pause@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def pause_playing(_, m: Message):
    if Config.PAUSE:
        return await m.reply("Already Paused")
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    await m.reply("Paused Video Call")
    await pause()
    

@Client.on_message(filters.command(["resume", f"resume@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def resume_playing(_, m: Message):
    if not Config.PAUSE:
        return await m.reply("Nothing paused to resume")
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    await m.reply("Resumed Video Call")
    await resume()
    


@Client.on_message(filters.command(['volume', f"volume@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def set_vol(_, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    if len(m.command) < 2:
        await m.reply_text('You forgot to pass volume (1-200).')
        return
    await m.reply_text(f"Volume set to {m.command[1]}")
    await volume(int(m.command[1]))


@Client.on_message(filters.command(['mute', f"mute@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def set_mute(_, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    if Config.MUTED:
        return await m.reply_text("Already muted.")
    k=await mute()
    if k:
        await m.reply_text(f" 🔇 Succesfully Muted ")
    else:
        await m.reply_text("Already muted.")
    
@Client.on_message(filters.command(['unmute', f"unmute@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def set_unmute(_, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    if not Config.MUTED:
        return await m.reply("Stream already unmuted.")
    k=await unmute()
    if k:
        await m.reply_text(f"🔊 Succesfully Unmuted ")
    else:
        await m.reply_text("Not muted, already unmuted.")    


@Client.on_message(filters.command(["replay", f"replay@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def replay_playout(client, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    await m.reply_text(f"Replaying from begining")
    await restart_playout()


@Client.on_message(filters.command(["player", f"player@{Config.BOT_USERNAME}"]) & (filters.chat(Config.CHAT) | filters.private))
async def show_player(client, m: Message):
    data=Config.DATA.get('FILE_DATA')
    if not data.get('dur', 0) or \
        data.get('dur') == 0:
        title="<b>Playing Live Stream</b>"
    else:
        if Config.playlist:
            title=f"<b>{Config.playlist[0][1]}</b>"
        elif Config.STREAM_LINK:
            title=f"<b>Stream Using [Url]({data['file']}) </b>"
        else:
            title=f"<b>Streaming Startup [stream]({Config.STREAM_URL})</b>"
    if m.chat.type == "private":
        await m.reply_text(
            title,
            disable_web_page_preview=True,
            reply_markup=await get_buttons()
        )
    else:
        if Config.msg.get('player') is not None:
            await Config.msg['playlist'].delete()
        Config.msg['player'] = await m.reply_text(
            title,
            disable_web_page_preview=True,
            reply_markup=await get_buttons()
        )


@Client.on_message(filters.command(["seek", f"seek@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def seek_playout(client, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not Playing anything.")
    if not (Config.playlist or Config.STREAM_LINK):
        return await m.reply("Startup stream cant be seeked.")
    data=Config.DATA.get('FILE_DATA')
    if not data.get('dur', 0) or \
        data.get('dur') == 0:
        return await m.reply("This stream cant be seeked..")
    if ' ' in m.text:
        i, time = m.text.split(" ")
        try:
            time=int(time)
        except:
            return await m.reply('Invalid time specified')
        k, string=await seek_file(time)
        if k == False:
            return await m.reply(string)
        if not data.get('dur', 0) or \
            data.get('dur') == 0:
            title="<b>Playing Live Stream</b>"
        else:
            if Config.playlist:
                title=f"<b>{Config.playlist[0][1]}</b>"
            elif Config.STREAM_LINK:
                title=f"<b>Stream Using [Url]({data['file']}</b>)"
            else:
                title=f"<b>Streaming Startup [stream]({Config.STREAM_URL})</b>"
        await m.reply(f"🎸{title}", reply_markup=await get_buttons(), disable_web_page_preview=True)
    else:
        await m.reply('No time specified')