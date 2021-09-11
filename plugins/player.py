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

from utils import download, get_admins, is_admin, get_buttons, get_link, import_play_list, leave_call, play, get_playlist_str, send_playlist, shuffle_playlist, start_stream, stream_from_link
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch
from pyrogram import Client, filters
from pyrogram.types import Message
from youtube_dl import YoutubeDL
from datetime import datetime
from pyrogram import filters
from config import Config
from logger import LOGGER
import re

admin_filter=filters.create(is_admin) 

@Client.on_message(filters.command(["play", f"play@{Config.BOT_USERNAME}"]) & (filters.chat(Config.CHAT) | filters.private))
async def add_to_playlist(_, message: Message):
    if Config.ADMIN_ONLY == "Y":
        admins = await get_admins(Config.CHAT)
        if message.from_user.id not in admins:
            await message.reply_sticker("CAADBQADsQIAAtILIVYld1n74e3JuQI")
            return
    type=""
    yturl=""
    ysearch=""
    if message.reply_to_message and message.reply_to_message.video:
        msg = await message.reply_text("⚡️ **Checking Telegram Media...**")
        type='video'
        m_video = message.reply_to_message.video       
    elif message.reply_to_message and message.reply_to_message.document:
        msg = await message.reply_text("⚡️ **Checking Telegram Media...**")
        m_video = message.reply_to_message.document
        type='video'
        if not "video" in m_video.mime_type:
            return await msg.edit("The given file is invalid")
    else:
        if message.reply_to_message:
            link=message.reply_to_message.text
            regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
            match = re.match(regex,link)
            if match:
                type="youtube"
                yturl=link
        elif " " in message.text:
            text = message.text.split(" ", 1)
            query = text[1]
            regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
            match = re.match(regex,query)
            if match:
                type="youtube"
                yturl=query
            else:
                type="query"
                ysearch=query
        else:
            await message.reply_text("You Didn't gave me anything to play.Reply to a video or a youtube link.")
            return
    user=f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    if type=="video":
        now = datetime.now()
        nyav = now.strftime("%d-%m-%Y-%H:%M:%S")
        data={1:m_video.file_name, 2:m_video.file_id, 3:"telegram", 4:user, 5:f"{nyav}_{m_video.file_size}"}
        Config.playlist.append(data)
        await msg.edit("Media added to playlist")
    if type=="youtube" or type=="query":
        if type=="youtube":
            msg = await message.reply_text("⚡️ **Fetching Video From YouTube...**")
            url=yturl
        elif type=="query":
            try:
                msg = await message.reply_text("⚡️ **Fetching Video From YouTube...**")
                ytquery=ysearch
                results = YoutubeSearch(ytquery, max_results=1).to_dict()
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
            except Exception as e:
                await msg.edit(
                    "Song not found.\nTry inline mode.."
                )
                LOGGER.error(str(e))
                return
        else:
            return
        ydl_opts = {
            "geo-bypass": True,
            "nocheckcertificate": True
        }
        ydl = YoutubeDL(ydl_opts)
        try:
            info = ydl.extract_info(url, False)
        except Exception as e:
            LOGGER.error(e)
            await msg.edit(
                f"YouTube Download Error ❌\nError:- {e}"
                )
            LOGGER.error(str(e))
            return
        title = info["title"]
        now = datetime.now()
        nyav = now.strftime("%d-%m-%Y-%H:%M:%S")
        data={1:title, 2:url, 3:"youtube", 4:user, 5:f"{nyav}_{message.from_user.id}"}
        Config.playlist.append(data)
        await msg.edit(f"[{title}]({url}) added to playist", disable_web_page_preview=True)
    if len(Config.playlist) == 1:
        m_status = await msg.edit("Downloading and Processing...")
        await download(Config.playlist[0], m_status)
        await play()
        await m_status.delete()
    else:
        await send_playlist()  
    pl=await get_playlist_str()
    if message.chat.type == "private":
        await message.reply(pl, reply_markup=await get_buttons() ,disable_web_page_preview=True)        
    elif not Config.LOG_GROUP and message.chat.type == "supergroup":
        await message.reply(pl, disable_web_page_preview=True, reply_markup=await get_buttons())          
    for track in Config.playlist[:2]:
        await download(track)


@Client.on_message(filters.command(["leave", f"leave@{Config.BOT_USERNAME}"]) & admin_filter)
async def leave_voice_chat(_, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not joined any voicechat.")
    await leave_call()
    await m.reply("Succesfully left videochat.")



@Client.on_message(filters.command(["shuffle", f"shuffle@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def shuffle_play_list(client, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not joined any voicechat.")
    else:
        if len(Config.playlist) > 2:
            await m.reply_text(f"Playlist Shuffled.")
            await shuffle_playlist()
            
        else:
            await m.reply_text(f"You cant shuffle playlist with less than 3 songs.")


@Client.on_message(filters.command(["clearplaylist", f"clearplaylist@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def clear_play_list(client, m: Message):
    if not Config.CALL_STATUS:
        return await m.reply("Not joined any voicechat.")
    if not Config.playlist:
        return await m.reply("Playlist is empty. May be Live streaming.")  
    Config.playlist.clear()   
    await m.reply_text(f"Playlist Cleared.")
    await start_stream()


@Client.on_message(filters.command(["yplay", f"yplay@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def yt_play_list(client, m: Message):
    if m.reply_to_message is not None and m.reply_to_message.document:
        if m.reply_to_message.document.file_name != "YouTube_PlayList.json":
            await m.reply("Invalid PlayList file given. Use @GetPlayListBot  or search for a playlist in @DumpPlaylist to get a playlist file.")
            return
        ytplaylist=await m.reply_to_message.download()
        status=await m.reply("Trying to get details from playlist.")
        n=await import_play_list(ytplaylist)
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


@Client.on_message(filters.command(["stream", f"stream@{Config.BOT_USERNAME}"]) & admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def stream(client, m: Message):
    if m.reply_to_message:
        link=m.reply_to_message.text
    elif " " in m.text:
        text = m.text.split(" ", 1)
        link = text[1]
    else:
        return await m.reply("Provide a link to stream!")
    regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
    match = re.match(regex,link)
    if match:
        stream_link=await get_link(link)
        if not stream_link:
            return await m.reply("This is an invalid link.")
    else:
        stream_link=link
    await m.reply(f"[Streaming]({stream_link}) Started.", disable_web_page_preview=True)
    await stream_from_link(stream_link)
    


admincmds=["yplay", "leave", "pause", "resume", "skip", "restart", "volume", "shuffle", "clearplaylist", "export", "import", "update", 'replay', 'logs', 'stream', f'stream@{Config.BOT_USERNAME}', f'logs@{Config.BOT_USERNAME}', f"replay@{Config.BOT_USERNAME}", f"yplay@{Config.BOT_USERNAME}", f"leave@{Config.BOT_USERNAME}", f"pause@{Config.BOT_USERNAME}", f"resume@{Config.BOT_USERNAME}", f"skip@{Config.BOT_USERNAME}", f"restart@{Config.BOT_USERNAME}", f"volume@{Config.BOT_USERNAME}", f"shuffle@{Config.BOT_USERNAME}", f"clearplaylist@{Config.BOT_USERNAME}", f"export@{Config.BOT_USERNAME}", f"import@{Config.BOT_USERNAME}", f"update@{Config.BOT_USERNAME}"]

@Client.on_message(filters.command(admincmds) & ~admin_filter & (filters.chat(Config.CHAT) | filters.private))
async def notforu(_, m: Message):
    await _.send_cached_media(chat_id=m.chat.id, file_id="CAADBQADEgQAAtMJyFVJOe6-VqYVzAI", caption="You Are Not Authorized", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⚡️Join Here', url='https://t.me/subin_works')]]))
allcmd = ["play", "player", f"play@{Config.BOT_USERNAME}", f"player@{Config.BOT_USERNAME}"] + admincmds

@Client.on_message(filters.command(allcmd) & ~filters.chat(Config.CHAT) & filters.group)
async def not_chat(_, m: Message):
    buttons = [
        [
            InlineKeyboardButton('⚡️Make Own Bot', url='https://github.com/subinps/VCPlayerBot'),
            InlineKeyboardButton('🧩 Join Here', url='https://t.me/subin_works'),
        ]
        ]
    await m.reply("<b>You can't use this bot in this group, for that you have to make your own bot from the [SOURCE CODE](https://github.com/subinps/VCPlayerBot) below.</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

