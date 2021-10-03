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
from logger import LOGGER
from youtube_search import YoutubeSearch
from contextlib import suppress
from pyrogram.types import Message
from youtube_dl import YoutubeDL
from datetime import datetime
from pyrogram import filters
from config import Config
import re
from utils import (
    add_to_db_playlist, 
    clear_db_playlist, 
    delete_messages, 
    download, 
    get_admins, 
    get_duration, 
    is_admin, 
    get_buttons, 
    get_link, 
    import_play_list, 
    is_audio, 
    leave_call, 
    play, 
    get_playlist_str, 
    send_playlist, 
    shuffle_playlist, 
    start_stream, 
    stream_from_link, 
    chat_filter
)
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
    )
from pyrogram.errors import (
    MessageIdInvalid, 
    MessageNotModified
    )
from pyrogram import (
    Client, 
    filters
    )

admin_filter=filters.create(is_admin) 

@Client.on_message(filters.command(["play", "fplay", f"play@{Config.BOT_USERNAME}", f"fplay@{Config.BOT_USERNAME}"]) & chat_filter)
async def add_to_playlist(_, message: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        if Config.ADMIN_ONLY:
            admins = await get_admins(Config.CHAT)
            if not (message.from_user is None and message.sender_chat or message.from_user.id in admins):
                k=await message.reply_sticker("CAADBQADsQIAAtILIVYld1n74e3JuQI")
                await delete_messages([message, k])
                return
        type=""
        yturl=""
        ysearch=""
        if message.command[0] == "fplay":
            if not (message.from_user is None and message.sender_chat or message.from_user.id in admins):
                k=await message.reply("This command is only for admins.")
                await delete_messages([message, k])
                return
        msg = await message.reply_text("⚡️ **Checking recived input..**")
        if message.reply_to_message and message.reply_to_message.video:
            await msg.edit("⚡️ **Checking Telegram Media...**")
            type='video'
            m_video = message.reply_to_message.video       
        elif message.reply_to_message and message.reply_to_message.document:
            await msg.edit("⚡️ **Checking Telegram Media...**")
            m_video = message.reply_to_message.document
            type='video'
            if not "video" in m_video.mime_type:
                return await msg.edit("The given file is invalid")
        elif message.reply_to_message and message.reply_to_message.audio:
            #if not Config.IS_VIDEO:
                #return await message.reply("Play from audio file is available only if Video Mode if turned off.\nUse /settings to configure ypur player.")
            await msg.edit("⚡️ **Checking Telegram Media...**")
            type='audio'
            m_video = message.reply_to_message.audio       
        else:
            if message.reply_to_message and message.reply_to_message.text:
                query=message.reply_to_message.text
            elif " " in message.text:
                text = message.text.split(" ", 1)
                query = text[1]
            else:
                await msg.edit("You Didn't gave me anything to play.Reply to a video or a youtube link or a direct link.")
                await delete_messages([message, msg])
                return
            regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
            match = re.match(regex,query)
            if match:
                type="youtube"
                yturl=query
            elif query.startswith("http"):
                """if Config.IS_VIDEO:
                    try:
                        width, height = get_height_and_width(query)
                    except:
                        width, height = None, None
                        LOGGER.error("Unable to get video properties within time.")
                    if not width or \
                        not height:
                        await msg.edit("This is an invalid link, provide me a direct link or a youtube link.")
                        await delete_messages([message, msg])
                        return """
                #else:
                try:
                    has_audio_ = is_audio(query)
                except:
                    has_audio_ = False
                    LOGGER.error("Unable to get Audio properties within time.")
                if not has_audio_:
                    await msg.edit("This is an invalid link, provide me a direct link or a youtube link.")
                    await delete_messages([message, msg])
                    return
                try:
                    dur=get_duration(query)
                except:
                    dur=0
                if dur == 0:
                    await msg.edit("This is a live stream, Use /stream command.")
                    await delete_messages([message, msg])
                    return 
                type="direct"
                url=query
            else:
                type="query"
                ysearch=query
        if not message.from_user is None:
            user=f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            user_id = message.from_user.id
        else:
            user="Anonymous"
            user_id = "anonymous_admin"
        now = datetime.now()
        nyav = now.strftime("%d-%m-%Y-%H:%M:%S")
        if type in ["video", "audio"]:
            if type == "audio":
                title=m_video.title
            else:
                title=m_video.file_name
            data={1:title, 2:m_video.file_id, 3:"telegram", 4:user, 5:f"{nyav}_{m_video.file_size}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)        
            await msg.edit("Media added to playlist")
        elif type=="youtube" or type=="query":
            if type=="youtube":
                await msg.edit("⚡️ **Fetching Video From YouTube...**")
                url=yturl
            elif type=="query":
                try:
                    await msg.edit("⚡️ **Fetching Video From YouTube...**")
                    ytquery=ysearch
                    results = YoutubeSearch(ytquery, max_results=1).to_dict()
                    url = f"https://youtube.com{results[0]['url_suffix']}"
                    title = results[0]["title"][:40]
                except Exception as e:
                    await msg.edit(
                        "Song not found.\nTry inline mode.."
                    )
                    LOGGER.error(str(e))
                    await delete_messages([message, msg])
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
                await delete_messages([message, msg])
                return
            title = info["title"]
            data={1:title, 2:url, 3:"youtube", 4:user, 5:f"{nyav}_{user_id}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)
            await msg.edit(f"[{title}]({url}) added to playist", disable_web_page_preview=True)
        elif type == "direct":
            data={1:"Music", 2:url, 3:"url", 4:user, 5:f"{nyav}_{user_id}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)        
            await msg.edit("Link added to playlist")
        if not Config.CALL_STATUS \
            and len(Config.playlist) >= 1:
            await msg.edit("Downloading and Processing...")
            await download(Config.playlist[0], msg)
            await play()
        elif (len(Config.playlist) == 1 and Config.CALL_STATUS):
            await msg.edit("Downloading and Processing...")
            await download(Config.playlist[0], msg)  
            await play()
        elif message.command[0] == "fplay":
            await msg.edit("Downloading and Processing...")
            await download(Config.playlist[0], msg)  
            await play()
        else:
            await send_playlist()  
        await msg.delete()
        pl=await get_playlist_str()
        if message.chat.type == "private":
            await message.reply(pl, reply_markup=await get_buttons() ,disable_web_page_preview=True)       
        elif not Config.LOG_GROUP and message.chat.type == "supergroup":
            if Config.msg.get('playlist') is not None:
                await Config.msg['playlist'].delete()
            Config.msg['playlist']=await message.reply(pl, disable_web_page_preview=True, reply_markup=await get_buttons())    
            await delete_messages([message])  
        for track in Config.playlist[:2]:
            await download(track)


@Client.on_message(filters.command(["leave", f"leave@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def leave_voice_chat(_, m: Message):
    if not Config.CALL_STATUS:        
        k=await m.reply("Not joined any voicechat.")
        await delete_messages([m, k])
        return
    await leave_call()
    k=await m.reply("Succesfully left videochat.")
    await delete_messages([m, k])



@Client.on_message(filters.command(["shuffle", f"shuffle@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def shuffle_play_list(client, m: Message):
    if not Config.CALL_STATUS:
        k = await m.reply("Not joined any voicechat.")
        await delete_messages([m, k])
        return
    else:
        if len(Config.playlist) > 2:
            k=await m.reply_text(f"Playlist Shuffled.")
            await shuffle_playlist()
            await delete_messages([m, k])            
        else:
            k=await m.reply_text(f"You cant shuffle playlist with less than 3 songs.")
            await delete_messages([m, k])


@Client.on_message(filters.command(["clearplaylist", f"clearplaylist@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def clear_play_list(client, m: Message):
    if not Config.playlist:
        k = await m.reply("Playlist is empty.")  
        await delete_messages([m, k])
        return
    Config.playlist.clear()
    k=await m.reply_text(f"Playlist Cleared.")
    await clear_db_playlist(all=True)
    if Config.IS_LOOP \
        and not Config.YPLAY:
        await start_stream()
    else:
        await leave_call()
    await delete_messages([m, k])


@Client.on_message(filters.command(["yplay", f"yplay@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def yt_play_list(client, m: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        if m.reply_to_message is not None and m.reply_to_message.document:
            if m.reply_to_message.document.file_name != "YouTube_PlayList.json":
                k=await m.reply("Invalid PlayList file given. Use @GetPlayListBot  or search for a playlist in @DumpPlaylist to get a playlist file.")
                await delete_messages([m, k])
                return
            ytplaylist=await m.reply_to_message.download()
            status=await m.reply("Trying to get details from playlist.")
            n=await import_play_list(ytplaylist)
            if not n:
                await status.edit("Errors Occured while importing playlist.")
                await delete_messages([m, status])
                return
            if Config.SHUFFLE:
                await shuffle_playlist()
            pl=await get_playlist_str()
            if m.chat.type == "private":
                await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())        
            elif not Config.LOG_GROUP and m.chat.type == "supergroup":
                if Config.msg.get("playlist") is not None:
                    await Config.msg['playlist'].delete()
                Config.msg['playlist']=await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())
                await delete_messages([m])
            else:
                await delete_messages([m, status])
        else:
            k=await m.reply("No playList file given. Use @GetPlayListBot  or search for a playlist in @DumpPlaylist to get a playlist file.")
            await delete_messages([m, k])


@Client.on_message(filters.command(["stream", f"stream@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def stream(client, m: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        msg=await m.reply("Checking the recived input.")
        if m.reply_to_message and m.reply_to_message.text:
            link=m.reply_to_message.text
        elif " " in m.text:
            text = m.text.split(" ", 1)
            link = text[1]
        else:
            k = await msg.edit("Provide a link to stream!")
            await delete_messages([m, k])
            return
        regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
        match = re.match(regex,link)
        if match:
            stream_link=await get_link(link)
            if not stream_link:
                k = await msg.edit("This is an invalid link.")
                await delete_messages([m, k])
                return
        else:
            stream_link=link
        """if Config.IS_VIDEO:
            try:
                width, height = get_height_and_width(stream_link)
            except:
                width, height = None, None
                LOGGER.error("Unable to get video properties within time.")
            if not width or \
                not height:
                k = await msg.edit("This is an invalid link, provide me a direct link or a youtube link.")
                await delete_messages([m, k])
                return"""
        #else:
        try:
            is_audio_ = is_audio(stream_link)
        except:
            is_audio_ = False
            LOGGER.error("Unable to get Audio properties within time.")
        if not is_audio_:
            k = await msg.edit("This is an invalid link, provide me a direct link or a youtube link.")
            await delete_messages([m, k])
            return
        try:
            dur=get_duration(stream_link)
        except:
            dur=0
        if dur != 0:
            k = await msg.edit("This is not a live stream, Use /play command.")
            await delete_messages([m, k])
            return
        k, msg_=await stream_from_link(stream_link)
        if k == False:
            k = await msg.edit(msg_)
            await delete_messages([m, k])
            return
        if Config.msg.get('player'):
            await Config.msg['player'].delete()
        Config.msg['player']=await msg.edit(f"[Streaming]({stream_link}) Started. ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ", disable_web_page_preview=True, reply_markup=await get_buttons())
        await delete_messages([m])
        


admincmds=["yplay", "leave", "pause", "resume", "skip", "restart", "volume", "shuffle", "clearplaylist", "export", "import", "update", 'replay', 'logs', 'stream', 'fplay', 'schedule', 'record', 'slist', 'cancel', 'cancelall', 'vcpromote', 'vcdemote', 'refresh', 'rtitle', 'seek', 'mute', 'unmute',
f'stream@{Config.BOT_USERNAME}', f'logs@{Config.BOT_USERNAME}', f"replay@{Config.BOT_USERNAME}", f"yplay@{Config.BOT_USERNAME}", f"leave@{Config.BOT_USERNAME}", f"pause@{Config.BOT_USERNAME}", f"resume@{Config.BOT_USERNAME}", f"skip@{Config.BOT_USERNAME}", 
f"restart@{Config.BOT_USERNAME}", f"volume@{Config.BOT_USERNAME}", f"shuffle@{Config.BOT_USERNAME}", f"clearplaylist@{Config.BOT_USERNAME}", f"export@{Config.BOT_USERNAME}", f"import@{Config.BOT_USERNAME}", f"update@{Config.BOT_USERNAME}",
f'play@{Config.BOT_USERNAME}', f'schedule@{Config.BOT_USERNAME}', f'record@{Config.BOT_USERNAME}', f'slist@{Config.BOT_USERNAME}', f'cancel@{Config.BOT_USERNAME}', f'cancelall@{Config.BOT_USERNAME}', f'vcpromote@{Config.BOT_USERNAME}', 
f'vcdemote@{Config.BOT_USERNAME}', f'refresh@{Config.BOT_USERNAME}', f'rtitle@{Config.BOT_USERNAME}', f'seek@{Config.BOT_USERNAME}', f'mute@{Config.BOT_USERNAME}', f'unmute@{Config.BOT_USERNAME}'
]

allcmd = ["play", "player", f"play@{Config.BOT_USERNAME}", f"player@{Config.BOT_USERNAME}"] + admincmds

@Client.on_message(filters.command(admincmds) & ~admin_filter & chat_filter)
async def notforu(_, m: Message):
    k = await _.send_cached_media(chat_id=m.chat.id, file_id="CAADBQADEgQAAtMJyFVJOe6-VqYVzAI", caption="You Are Not Authorized", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⚡️Join Here', url='https://t.me/subin_works')]]))
    await delete_messages([m, k])

@Client.on_message(filters.command(allcmd) & ~chat_filter & filters.group)
async def not_chat(_, m: Message):
    if m.from_user is not None and m.from_user.id in Config.SUDO:
        buttons = [
            [
                InlineKeyboardButton('⚡️Change CHAT', callback_data='set_new_chat'),
            ],
            [
                InlineKeyboardButton('No', callback_data='closesudo'),
            ]
            ]
        await m.reply("This is not the group which i have been configured to play, Do you want to set this group as default CHAT?", reply_markup=InlineKeyboardMarkup(buttons))
        await delete_messages([m])
    else:
        buttons = [
            [
                InlineKeyboardButton('⚡️Make Own Bot', url='https://github.com/subinps/VCPlayerBot'),
                InlineKeyboardButton('🧩 Join Here', url='https://t.me/subin_works'),
            ]
            ]
        await m.reply("<b>You can't use this bot in this group, for that you have to make your own bot from the [SOURCE CODE](https://github.com/subinps/VCPlayerBot) below.</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

