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
try:
    from pyrogram.raw.types import InputChannel
    from wrapt_timeout_decorator import timeout
    from apscheduler.schedulers.asyncio import AsyncIOScheduler   
    from apscheduler.jobstores.mongodb import MongoDBJobStore
    from apscheduler.jobstores.base import ConflictingIdError
    from pyrogram.raw.functions.channels import GetFullChannel
    from pytgcalls import StreamType
    from youtube_dl import YoutubeDL
    from pyrogram import filters
    from pymongo import MongoClient
    from datetime import datetime
    from threading import Thread
    from config import Config
    from asyncio import sleep  
    from bot import bot
    import subprocess
    import asyncio
    import random
    import re
    import ffmpeg
    import json
    import time
    import sys
    import os
    import math
    from pyrogram.errors.exceptions.bad_request_400 import (
        BadRequest, 
        ScheduleDateInvalid,
        PeerIdInvalid,
        ChannelInvalid
    )
    from pytgcalls.types.input_stream import (
        AudioVideoPiped, 
        AudioPiped,
        AudioImagePiped
    )
    from pytgcalls.types.input_stream import (
        AudioParameters,
        VideoParameters
    )
    from pyrogram.types import (
        InlineKeyboardButton, 
        InlineKeyboardMarkup, 
        Message
    )
    from pyrogram.raw.functions.phone import (
        EditGroupCallTitle, 
        CreateGroupCall,
        ToggleGroupCallRecord,
        StartScheduledGroupCall 
    )
    from pytgcalls.exceptions import (
        GroupCallNotFound, 
        NoActiveGroupCall,
        InvalidVideoProportion
    )
    from PIL import (
        Image, 
        ImageFont, 
        ImageDraw 
    )

    from user import (
        group_call, 
        USER
    )
except ModuleNotFoundError:
    import os
    import sys
    import subprocess
    file=os.path.abspath("requirements.txt")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', file, '--upgrade'])
    os.execl(sys.executable, sys.executable, *sys.argv)

if Config.DATABASE_URI:
    from database import db
    monclient = MongoClient(Config.DATABASE_URI)
    jobstores = {
        'default': MongoDBJobStore(client=monclient, database=Config.DATABASE_NAME, collection='scheduler')
        }
    scheduler = AsyncIOScheduler(jobstores=jobstores)
else:
    scheduler = AsyncIOScheduler()
scheduler.start()


async def play():
    song=Config.playlist[0]    
    if song[3] == "telegram":
        file=Config.GET_FILE.get(song[5])
        if not file:
            await download(song)
        while not file:
            await sleep(1)
            file=Config.GET_FILE.get(song[5])
            LOGGER.info("Downloading the file from TG")
        while not os.path.exists(file):
            await sleep(1)
    elif song[3] == "url":
        file=song[2]
    else:
        file=await get_link(song[2])
    if not file:
        if Config.playlist or Config.STREAM_LINK:
            return await skip()     
        else:
            LOGGER.error("This stream is not supported , leaving VC.")
            return False   
    link, seek, pic, width, height = await chek_the_media(file, title=f"{song[1]}")
    if not link:
        LOGGER.warning("Unsupported link, Skiping from queue.")
        return
    await sleep(1)
    if Config.STREAM_LINK:
        Config.STREAM_LINK=False
    await join_call(link, seek, pic, width, height)

async def schedule_a_play(job_id, date):
    try:
        scheduler.add_job(run_schedule, "date", [job_id], id=job_id, run_date=date, max_instances=50, misfire_grace_time=None)
    except ConflictingIdError:
        LOGGER.warning("This already scheduled")
        return
    if not Config.CALL_STATUS or not Config.IS_ACTIVE:
        if Config.SCHEDULE_LIST[0]['job_id'] == job_id \
            and (date - datetime.now()).total_seconds() < 86400:
            song=Config.SCHEDULED_STREAM.get(job_id)
            if Config.IS_RECORDING:
                scheduler.add_job(start_record_stream, "date", id=str(Config.CHAT), run_date=date, max_instances=50, misfire_grace_time=None)
            try:
                await USER.send(CreateGroupCall(
                    peer=(await USER.resolve_peer(Config.CHAT)),
                    random_id=random.randint(10000, 999999999),
                    schedule_date=int(date.timestamp()),
                    title=song['1']
                    )
                )
                Config.HAS_SCHEDULE=True
            except ScheduleDateInvalid:
                LOGGER.error("Unable to schedule VideoChat, since date is invalid")
            except Exception as e:
                LOGGER.error(f"Error in scheduling voicechat- {e}")
    await sync_to_db()

async def run_schedule(job_id):
    data=Config.SCHEDULED_STREAM.get(job_id)
    if not data:
        LOGGER.error("The Scheduled stream was not played, since data is missing")
        old=filter(lambda k: k['job_id'] == job_id, Config.SCHEDULE_LIST)
        if old:
            Config.SCHEDULE_LIST.remove(old)
        await sync_to_db()
        pass
    else:
        if Config.HAS_SCHEDULE:
            if not await start_scheduled():
                LOGGER.error("Scheduled stream skipped, Reason - Unable to start a voice chat.")
                return
        data_ = [{1:data['1'], 2:data['2'], 3:data['3'], 4:data['4'], 5:data['5']}]
        Config.playlist = data_ + Config.playlist
        await play()
        LOGGER.info("Starting Scheduled Stream")
        del Config.SCHEDULED_STREAM[job_id]
        old=list(filter(lambda k: k['job_id'] == job_id, Config.SCHEDULE_LIST))
        if old:
            for old_ in old:
                Config.SCHEDULE_LIST.remove(old_)
        if not Config.SCHEDULE_LIST:
            Config.SCHEDULED_STREAM = {} #clear the unscheduled streams
        await sync_to_db()
        if len(Config.playlist) <= 1:
            return
        await download(Config.playlist[1])
      
async def cancel_all_schedules():
    for sch in Config.SCHEDULE_LIST:
        job=sch['job_id']
        k=scheduler.get_job(job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)
        if Config.SCHEDULED_STREAM.get(job):
            del Config.SCHEDULED_STREAM[job]      
    Config.SCHEDULE_LIST.clear()
    await sync_to_db()
    LOGGER.info("All the schedules are removed")

async def skip():
    if Config.STREAM_LINK and len(Config.playlist) == 0 and Config.IS_LOOP:
        await stream_from_link()
        return
    elif not Config.playlist \
        and Config.IS_LOOP:
        LOGGER.info("Loop Play enabled, switching to STARTUP_STREAM, since playlist is empty.")
        await start_stream()
        return
    elif not Config.playlist \
        and not Config.IS_LOOP:
        LOGGER.info("Loop Play is disabled, leaving call since playlist is empty.")
        await leave_call()
        return
    old_track = Config.playlist.pop(0)
    await clear_db_playlist(song=old_track)
    if old_track[3] == "telegram":
        file=Config.GET_FILE.get(old_track[5])
        try:
            os.remove(file)
        except:
            pass
        del Config.GET_FILE[old_track[5]]
    if not Config.playlist \
        and Config.IS_LOOP:
        LOGGER.info("Loop Play enabled, switching to STARTUP_STREAM, since playlist is empty.")
        await start_stream()
        return
    elif not Config.playlist \
        and not Config.IS_LOOP:
        LOGGER.info("Loop Play is disabled, leaving call since playlist is empty.")
        await leave_call()
        return
    LOGGER.info(f"START PLAYING: {Config.playlist[0][1]}")
    if Config.DUR.get('PAUSE'):
        del Config.DUR['PAUSE']
    await play()
    if len(Config.playlist) <= 1:
        return
    await download(Config.playlist[1])


async def check_vc():
    a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
    if a.full_chat.call is None:
        try:
            LOGGER.info("No active calls found, creating new")
            await USER.send(CreateGroupCall(
                peer=(await USER.resolve_peer(Config.CHAT)),
                random_id=random.randint(10000, 999999999)
                )
                )
            if Config.WAS_RECORDING:
                await start_record_stream()
            await sleep(2)
            return True
        except Exception as e:
            LOGGER.error(f"Unable to start new GroupCall :- {e}")
            return False
    else:
        if Config.HAS_SCHEDULE:
            await start_scheduled()
        return True
    

async def join_call(link, seek, pic, width, height):  
    if not await check_vc():
        LOGGER.error("No voice call found and was unable to create a new one. Exiting...")
        return
    if Config.HAS_SCHEDULE:
        await start_scheduled()
    if Config.CALL_STATUS:
        if Config.IS_ACTIVE == False:
            Config.CALL_STATUS = False
            return await join_call(link, seek, pic, width, height)
        play=await change_file(link, seek, pic, width, height)
    else:
        play=await join_and_play(link, seek, pic, width, height)
    if play == False:
        await sleep(1)
        await join_call(link, seek, pic, width, height)
    await sleep(1)
    if not seek:
        Config.DUR["TIME"]=time.time()
        if Config.EDIT_TITLE:
            await edit_title()
    old=Config.GET_FILE.get("old")
    if old:
        for file in old:
            os.remove(f"./downloads/{file}")
        try:
            del Config.GET_FILE["old"]
        except:
            LOGGER.error("Error in Deleting from dict")
            pass
    await send_playlist()

async def start_scheduled():
    try:
        await USER.send(
            StartScheduledGroupCall(
                call=(
                    await USER.send(
                        GetFullChannel(
                            channel=(
                                await USER.resolve_peer(
                                    Config.CHAT
                                    )
                                )
                            )
                        )
                    ).full_chat.call
                )
            )
        if Config.WAS_RECORDING:
            await start_record_stream()
        return True
    except Exception as e:
        if 'GROUPCALL_ALREADY_STARTED' in str(e):
            LOGGER.warning("Already Groupcall Exist")
            return True
        else:
            Config.HAS_SCHEDULE=False
            return await check_vc()

async def join_and_play(link, seek, pic, width, height):
    try:
        if seek:
            start=str(seek['start'])
            end=str(seek['end'])
            if not Config.IS_VIDEO:
                await group_call.join_group_call(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=Config.AUDIO_Q,
                        additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                        ),
                    stream_type=StreamType().pulse_stream,
                )
            else:
                if pic:
                    await group_call.join_group_call(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            audio_parameters=Config.AUDIO_Q,
                            video_parameters=Config.VIDEO_Q,
                            additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',                        ),
                        stream_type=StreamType().pulse_stream,
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("No Valid Video Found and hence removed from playlist.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("This stream is not supported , leaving VC.")
                            return 
                    if Config.BITRATE and Config.FPS: 
                        await group_call.join_group_call(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=VideoParameters(
                                    width,
                                    height,
                                    Config.FPS,
                                ),
                                audio_parameters=AudioParameters(
                                    Config.BITRATE
                                ),
                                additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                                ),
                            stream_type=StreamType().pulse_stream,
                        )
                    else:
                        await group_call.join_group_call(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=Config.VIDEO_Q,
                                audio_parameters=Config.AUDIO_Q,
                                additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                                ),
                            stream_type=StreamType().pulse_stream,
                        )
        else:
            if not Config.IS_VIDEO:
                await group_call.join_group_call(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=Config.AUDIO_Q,
                        ),
                    stream_type=StreamType().pulse_stream,
                )
            else:
                if pic:
                    await group_call.join_group_call(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            video_parameters=Config.VIDEO_Q,
                            audio_parameters=Config.AUDIO_Q,               
                            ),
                        stream_type=StreamType().pulse_stream,
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("No Valid Video Found and hence removed from playlist.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("This stream is not supported , leaving VC.")
                            return 
                    if Config.FPS and Config.BITRATE:
                        await group_call.join_group_call(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=VideoParameters(
                                    width,
                                    height,
                                    Config.FPS,
                                ),
                                audio_parameters=AudioParameters(
                                    Config.BITRATE
                                ),
                            ),
                            stream_type=StreamType().pulse_stream,
                        )
                    else:
                        await group_call.join_group_call(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=Config.VIDEO_Q,
                                audio_parameters=Config.AUDIO_Q
                            ),
                            stream_type=StreamType().pulse_stream,
                        )
        Config.CALL_STATUS=True
        return True
    except NoActiveGroupCall:
        try:
            LOGGER.info("No active calls found, creating new")
            await USER.send(CreateGroupCall(
                peer=(await USER.resolve_peer(Config.CHAT)),
                random_id=random.randint(10000, 999999999)
                )
                )
            if Config.WAS_RECORDING:
                await start_record_stream()
            await sleep(2)
            await restart_playout()
        except Exception as e:
            LOGGER.error(f"Unable to start new GroupCall :- {e}")
            pass
    except InvalidVideoProportion:
        if not Config.FPS and not Config.BITRATE:
            Config.FPS=20
            Config.BITRATE=48000
            await join_and_play(link, seek, pic, width, height)
            Config.FPS=False
            Config.BITRATE=False
            return True
        else:
            LOGGER.error("Invalid video")
            if Config.playlist or Config.STREAM_LINK:
                return await skip()     
            else:
                LOGGER.error("This stream is not supported , leaving VC.")
                return 
    except Exception as e:
        LOGGER.error(f"Errors Occured while joining, retrying Error- {e}")
        return False


async def change_file(link, seek, pic, width, height):
    try:
        if seek:
            start=str(seek['start'])
            end=str(seek['end'])
            if not Config.IS_VIDEO:
                await group_call.change_stream(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=Config.AUDIO_Q,
                        additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                        ),
                )
            else:
                if pic:
                    await group_call.change_stream(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            audio_parameters=Config.AUDIO_Q,
                            video_parameters=Config.VIDEO_Q,
                            additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',                        ),
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("No Valid Video Found and hence removed from playlist.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("This stream is not supported , leaving VC.")
                            return 
                    if Config.FPS and Config.BITRATE:
                        await group_call.change_stream(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=VideoParameters(
                                    width,
                                    height,
                                    Config.FPS,
                                ),
                                audio_parameters=AudioParameters(
                                    Config.BITRATE
                                ),
                                additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                            ),
                            )
                    else:
                        await group_call.change_stream(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=Config.VIDEO_Q,
                                audio_parameters=Config.AUDIO_Q,
                                additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                            ),
                            )
        else:
            if not Config.IS_VIDEO:
                await group_call.change_stream(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=Config.AUDIO_Q
                        ),
                )
            else:
                if pic:
                    await group_call.change_stream(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            audio_parameters=Config.AUDIO_Q,
                            video_parameters=Config.VIDEO_Q,
                        ),
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("No Valid Video Found and hence removed from playlist.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("This stream is not supported , leaving VC.")
                            return 
                    if Config.FPS and Config.BITRATE:
                        await group_call.change_stream(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=VideoParameters(
                                    width,
                                    height,
                                    Config.FPS,
                                ),
                                audio_parameters=AudioParameters(
                                    Config.BITRATE,
                                ),
                            ),
                            )
                    else:
                        await group_call.change_stream(
                            int(Config.CHAT),
                            AudioVideoPiped(
                                link,
                                video_parameters=Config.VIDEO_Q,
                                audio_parameters=Config.AUDIO_Q,
                            ),
                            )
    except InvalidVideoProportion:
        if not Config.FPS and not Config.BITRATE:
            Config.FPS=20
            Config.BITRATE=48000
            await join_and_play(link, seek, pic, width, height)
            Config.FPS=False
            Config.BITRATE=False
            return True
        else:
            LOGGER.error("Invalid video, skipped")
            if Config.playlist or Config.STREAM_LINK:
                return await skip()     
            else:
                LOGGER.error("This stream is not supported , leaving VC.")
                return 
    except Exception as e:
        LOGGER.error(f"Error in joining call - {e}")
        return False


async def seek_file(seektime):
    play_start=int(float(Config.DUR.get('TIME')))
    if not play_start:
        return False, "Player not yet started"
    else:
        data=Config.DATA.get("FILE_DATA")
        if not data:
            return False, "No Streams for seeking"        
        played=int(float(time.time())) - int(float(play_start))
        if data.get("dur", 0) == 0:
            return False, "Seems like live stream is playing, which cannot be seeked."
        total=int(float(data.get("dur", 0)))
        trimend = total - played - int(seektime)
        trimstart = played + int(seektime)
        if trimstart > total:
            return False, "Seeked duration exceeds maximum duration of file"
        new_play_start=int(play_start) - int(seektime)
        Config.DUR['TIME']=new_play_start
        link, seek, pic, width, height = await chek_the_media(data.get("file"), seek={"start":trimstart, "end":trimend})
        await join_call(link, seek, pic, width, height)
        return True, None
    


async def leave_call():
    try:
        await group_call.leave_group_call(Config.CHAT)
    except Exception as e:
        LOGGER.error(f"Errors while leaving call {e}")
    #Config.playlist.clear()
    if Config.STREAM_LINK:
        Config.STREAM_LINK=False
    Config.CALL_STATUS=False
    if Config.SCHEDULE_LIST:
        sch=Config.SCHEDULE_LIST[0]
        if (sch['date'] - datetime.now()).total_seconds() < 86400:
            song=Config.SCHEDULED_STREAM.get(sch['job_id'])
            if Config.IS_RECORDING:
                k=scheduler.get_job(str(Config.CHAT), jobstore=None)
                if k:
                    scheduler.remove_job(str(Config.CHAT), jobstore=None)
                scheduler.add_job(start_record_stream, "date", id=str(Config.CHAT), run_date=sch['date'], max_instances=50, misfire_grace_time=None)
            try:
                await USER.send(CreateGroupCall(
                    peer=(await USER.resolve_peer(Config.CHAT)),
                    random_id=random.randint(10000, 999999999),
                    schedule_date=int((sch['date']).timestamp()),
                    title=song['1']
                    )
                )
                Config.HAS_SCHEDULE=True
            except ScheduleDateInvalid:
                LOGGER.error("Unable to schedule VideoChat, since date is invalid")
            except Exception as e:
                LOGGER.error(f"Error in scheduling voicechat- {e}")
    await sync_to_db()
            
                


async def restart():
    try:
        await group_call.leave_group_call(Config.CHAT)
        await sleep(2)
    except Exception as e:
        LOGGER.error(e)
    if not Config.playlist:
        await start_stream()
        return
    LOGGER.info(f"- START PLAYING: {Config.playlist[0][1]}")
    await sleep(2)
    await play()
    LOGGER.info("Restarting Playout")
    if len(Config.playlist) <= 1:
        return
    await download(Config.playlist[1])


async def restart_playout():
    if not Config.playlist:
        await start_stream()
        return
    LOGGER.info(f"RESTART PLAYING: {Config.playlist[0][1]}")
    data=Config.DATA.get('FILE_DATA')
    if data:
        link, seek, pic, width, height = await chek_the_media(data['file'], title=f"{Config.playlist[0][1]}")
        if not link:
            LOGGER.warning("Unsupported Link")
            return
        await sleep(1)
        if Config.STREAM_LINK:
            Config.STREAM_LINK=False
        await join_call(link, seek, pic, width, height)
    else:
        await play()
    if len(Config.playlist) <= 1:
        return
    await download(Config.playlist[1])

async def set_up_startup():
    regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
    match = re.match(regex, Config.STREAM_URL)
    if match:
        Config.YSTREAM=True
        LOGGER.info("YouTube Stream is set as STARTUP STREAM")
    elif Config.STREAM_URL.startswith("https://t.me/DumpPlaylist"):
        try:
            msg_id=Config.STREAM_URL.split("/", 4)[4]
            Config.STREAM_URL=int(msg_id)
            Config.YPLAY=True
            LOGGER.info("YouTube Playlist is set as STARTUP STREAM")
        except:
            Config.STREAM_URL="http://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/playlist.m3u8"
            LOGGER.error("Unable to fetch youtube playlist, starting Safari TV")
            pass
    else:
        Config.STREAM_URL=Config.STREAM_URL
    Config.STREAM_SETUP=True
    
    

async def start_stream(): 
    if not Config.STREAM_SETUP:
        await set_up_startup()
    if Config.YPLAY:
        await y_play(Config.STREAM_URL)
        return
    if Config.YSTREAM:
        link=await get_link(Config.STREAM_URL)
    else:
        link=Config.STREAM_URL
    link, seek, pic, width, height = await chek_the_media(link, title="Startup Stream")
    if not link:
        LOGGER.warning("Unsupported link")
        return False
    if Config.IS_VIDEO:
        if not ((width and height) or pic):
            LOGGER.error("Stream Link is invalid")
            return 
    #if Config.playlist:
        #Config.playlist.clear()
    await join_call(link, seek, pic, width, height)


async def stream_from_link(link):
    link, seek, pic, width, height = await chek_the_media(link)
    if not link:
        LOGGER.error("Unable to obtain sufficient information from the given url")
        return False, "Unable to obtain sufficient information from the given url"
    #if Config.playlist:
        #Config.playlist.clear()
    Config.STREAM_LINK=link
    await join_call(link, seek, pic, width, height)
    return True, None



async def get_link(file):
    def_ydl_opts = {'quiet': True, 'prefer_insecure': False, "geo-bypass": True}
    with YoutubeDL(def_ydl_opts) as ydl:
        try:
            ydl_info = ydl.extract_info(file, download=False)
        except Exception as e:
            LOGGER.error(f"Errors occured while getting link from youtube video {e}")
            if Config.playlist or Config.STREAM_LINK:
                return await skip()     
            else:
                LOGGER.error("This stream is not supported , leaving VC.")
                return False
        url=None
        for each in ydl_info['formats']:
            if each['width'] == 640 \
                and each['acodec'] != 'none' \
                    and each['vcodec'] != 'none':
                    url=each['url']
                    break #prefer 640x360
            elif each['width'] \
                and each['width'] <= 1280 \
                    and each['acodec'] != 'none' \
                        and each['vcodec'] != 'none':
                        url=each['url']
                        continue # any other format less than 1280
            else:
                continue
        if url:
            return url
        else:
            LOGGER.error(f"Errors occured while getting link from youtube video - No Video Formats Found")
            if Config.playlist or Config.STREAM_LINK:
                return await skip()     
            else:
                LOGGER.error("This stream is not supported , leaving VC.")
                return False



async def download(song, msg=None):
    if song[3] == "telegram":
        if not Config.GET_FILE.get(song[5]):
            try: 
                original_file = await bot.download_media(song[2], progress=progress_bar, file_name=f'./tgdownloads/', progress_args=(int((song[5].split("_"))[1]), time.time(), msg))

                Config.GET_FILE[song[5]]=original_file
            except Exception as e:
                LOGGER.error(e)
                Config.playlist.remove(song)
                await clear_db_playlist(song=song)
                if len(Config.playlist) <= 1:
                    return
                await download(Config.playlist[1])
   


async def chek_the_media(link, seek=False, pic=False, title="Music"):
    if not Config.IS_VIDEO:
        width, height = None, None
        is_audio_=False
        try:
            is_audio_ = is_audio(link)
        except:
            is_audio_ = False
            LOGGER.error("Unable to get Audio properties within time.")
        if not is_audio_:
            Config.STREAM_LINK=False
            if Config.playlist or Config.STREAM_LINK:
                return await skip()     
            else:
                LOGGER.error("This stream is not supported , leaving VC.")
                return None, None, None, None, None
            
    else:
        try:
            width, height = get_height_and_width(link)
        except:
            width, height = None, None
            LOGGER.error("Unable to get video properties within time.")
        if not width or \
            not height:
            is_audio_=False
            try:
                is_audio_ = is_audio(link)
            except:
                is_audio_ = False
                LOGGER.error("Unable to get Audio properties within time.")
            if is_audio_:
                pic_=await bot.get_messages("DumpPlaylist", 30)
                photo = "./pic/photo"
                if not os.path.exists(photo):
                    photo = await pic_.download(file_name=photo)
                try:
                    dur_=get_duration(link)
                except:
                    dur_='None'
                pic = get_image(title, photo, dur_) 
            else:
                Config.STREAM_LINK=False
                if Config.playlist or Config.STREAM_LINK:
                    return await skip()     
                else:
                    LOGGER.error("This stream is not supported , leaving VC.")
                    return None, None, None, None, None
    try:
        dur=get_duration(link)
    except:
        dur=0
    Config.DATA['FILE_DATA']={"file":link, 'dur':dur}
    return link, seek, pic, width, height


async def edit_title():
    if Config.STREAM_LINK:
        title="Live Stream"
    elif Config.playlist:
        title = Config.playlist[0][1]   
    else:       
        title = "Live Stream"
    try:
        chat = await USER.resolve_peer(Config.CHAT)
        full_chat=await USER.send(
            GetFullChannel(
                channel=InputChannel(
                    channel_id=chat.channel_id,
                    access_hash=chat.access_hash,
                    ),
                ),
            )
        edit = EditGroupCallTitle(call=full_chat.full_chat.call, title=title)
        await USER.send(edit)
    except Exception as e:
        LOGGER.error(f"Errors Occured while editing title - {e}")
        pass

async def stop_recording():
    job=str(Config.CHAT)
    a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
    if a.full_chat.call is None:
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)
        Config.IS_RECORDING=False
        await sync_to_db()
        return False, "No GroupCall Found"
    try:
        await USER.send(
            ToggleGroupCallRecord(
                call=(
                    await USER.send(
                        GetFullChannel(
                            channel=(
                                await USER.resolve_peer(
                                    Config.CHAT
                                    )
                                )
                            )
                        )
                    ).full_chat.call,
                start=False,                 
                )
            )
        Config.IS_RECORDING=False
        Config.LISTEN=True
        await sync_to_db()
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)
        return True, "Succesfully Stoped Recording"
    except Exception as e:
        if 'GROUPCALL_NOT_MODIFIED' in str(e):
            LOGGER.warning("Already No recording Exist")
            Config.IS_RECORDING=False
            await sync_to_db()
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            return False, "No recording was started"
        else:
            LOGGER.error(str(e))
            Config.IS_RECORDING=False
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            await sync_to_db()
            return False, str(e)
    



async def start_record_stream():
    if Config.IS_RECORDING:
        await stop_recording()
    if Config.WAS_RECORDING:
        Config.WAS_RECORDING=False
    a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
    job=str(Config.CHAT)
    if a.full_chat.call is None:
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)      
        return False, "No GroupCall Found"
    try:
        if not Config.PORTRAIT:
            pt = False
        else:
            pt = True
        if not Config.RECORDING_TITLE:
            tt = None
        else:
            tt = Config.RECORDING_TITLE
        if Config.IS_VIDEO_RECORD:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,
                    video=True,
                    video_portrait=pt,                 
                    )
                )
            time=240
        else:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,                
                    )
                )
            time=86400
        Config.IS_RECORDING=True
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)   
        try:
            scheduler.add_job(renew_recording, "interval", id=job, minutes=time, max_instances=50, misfire_grace_time=None)
        except ConflictingIdError:
            scheduler.remove_job(job, jobstore=None)
            scheduler.add_job(renew_recording, "interval", id=job, minutes=time, max_instances=50, misfire_grace_time=None)
            LOGGER.warning("This already scheduled, rescheduling")
        await sync_to_db()
        LOGGER.info("Recording Started")
        return True, "Succesfully Started Recording"
    except Exception as e:
        if 'GROUPCALL_NOT_MODIFIED' in str(e):
            LOGGER.warning("Already Recording.., stoping and restarting")
            Config.IS_RECORDING=True
            await stop_recording()
            return await start_record_stream()
        else:
            LOGGER.error(str(e))
            Config.IS_RECORDING=False
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            await sync_to_db()
            return False, str(e)

async def renew_recording():
    try:
        job=str(Config.CHAT)
        a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
        if a.full_chat.call is None:
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)      
            LOGGER.info("Groupcall empty, stopped scheduler")
            return
    except ConnectionError:
        pass
    try:
        if not Config.PORTRAIT:
            pt = False
        else:
            pt = True
        if not Config.RECORDING_TITLE:
            tt = None
        else:
            tt = Config.RECORDING_TITLE
        if Config.IS_VIDEO_RECORD:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,
                    video=True,
                    video_portrait=pt,                 
                    )
                )
        else:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,                
                    )
                )
        Config.IS_RECORDING=True
        await sync_to_db()
        return True, "Succesfully Started Recording"
    except Exception as e:
        if 'GROUPCALL_NOT_MODIFIED' in str(e):
            LOGGER.warning("Already Recording.., stoping and restarting")
            Config.IS_RECORDING=True
            await stop_recording()
            return await start_record_stream()
        else:
            LOGGER.error(str(e))
            Config.IS_RECORDING=False
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            await sync_to_db()
            return False, str(e)

async def send_playlist():
    if Config.LOG_GROUP:
        pl = await get_playlist_str()
        if Config.msg.get('player') is not None:
            await Config.msg['player'].delete()
        Config.msg['player'] = await send_text(pl)


async def send_text(text):
    message = await bot.send_message(
        Config.LOG_GROUP,
        text,
        reply_markup=await get_buttons(),
        disable_web_page_preview=True,
        disable_notification=True
    )
    return message


async def shuffle_playlist():
    v = []
    p = [v.append(Config.playlist[c]) for c in range(2,len(Config.playlist))]
    random.shuffle(v)
    for c in range(2,len(Config.playlist)):
        Config.playlist.remove(Config.playlist[c]) 
        Config.playlist.insert(c,v[c-2])


async def import_play_list(file):
    file=open(file)
    try:
        f=json.loads(file.read(), object_hook=lambda d: {int(k): v for k, v in d.items()})
        for playf in f:
            Config.playlist.append(playf)
            await add_to_db_playlist(playf)
            if len(Config.playlist) >= 1 \
                and not Config.CALL_STATUS:
                LOGGER.info("Extracting link and Processing...")
                await download(Config.playlist[0])
                await play()   
            elif (len(Config.playlist) == 1 and Config.CALL_STATUS):
                LOGGER.info("Extracting link and Processing...")
                await download(Config.playlist[0])
                await play()               
        if not Config.playlist:
            file.close()
            try:
                os.remove(file)
            except:
                pass
            return False                      
        file.close()
        for track in Config.playlist[:2]:
            await download(track)   
        try:
            os.remove(file)
        except:
            pass
        return True
    except Exception as e:
        LOGGER.error(f"Errors while importing playlist {e}")
        return False



async def y_play(playlist):
    try:
        getplaylist=await bot.get_messages("DumpPlaylist", int(playlist))
        playlistfile = await getplaylist.download()
        LOGGER.warning("Trying to get details from playlist.")
        n=await import_play_list(playlistfile)
        if not n:
            LOGGER.error("Errors Occured While Importing Playlist")
            Config.YSTREAM=True
            Config.YPLAY=False
            if Config.IS_LOOP:
                Config.STREAM_URL="https://www.youtube.com/watch?v=zcrUCvBD16k"
                LOGGER.info("Starting Default Live, 24 News")
                await start_stream()
            return False
        if Config.SHUFFLE:
            await shuffle_playlist()
    except Exception as e:
        LOGGER.error("Errors Occured While Importing Playlist", e)
        Config.YSTREAM=True
        Config.YPLAY=False
        if Config.IS_LOOP:
            Config.STREAM_URL="https://www.youtube.com/watch?v=zcrUCvBD16k"
            LOGGER.info("Starting Default Live, 24 News")
            await start_stream()
        return False


async def pause():
    try:
        await group_call.pause_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Errors Occured while pausing -{e}")
        return False


async def resume():
    try:
        await group_call.resume_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Errors Occured while resuming -{e}")
        return False
    

async def volume(volume):
    try:
        await group_call.change_volume_call(Config.CHAT, volume)
        Config.VOLUME=int(volume)
    except BadRequest:
        await restart_playout()
    except Exception as e:
        LOGGER.error(f"Errors Occured while changing volume Error -{e}")
    
async def mute():
    try:
        await group_call.mute_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Errors Occured while muting -{e}")
        return False

async def unmute():
    try:
        await group_call.unmute_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Errors Occured while unmuting -{e}")
        return False


async def get_admins(chat):
    admins=Config.ADMINS
    if not Config.ADMIN_CACHE:
        if 626664225 not in admins:
            admins.append(626664225)
        try:
            grpadmins=await bot.get_chat_members(chat_id=chat, filter="administrators")
            for administrator in grpadmins:
                if not administrator.user.id in admins:
                    admins.append(administrator.user.id)
        except Exception as e:
            LOGGER.error(f"Errors occured while getting admin list - {e}")
            pass
        Config.ADMINS=admins
        Config.ADMIN_CACHE=True
        if Config.DATABASE_URI:
            await db.edit_config("ADMINS", Config.ADMINS)
    return admins


async def is_admin(_, client, message: Message):
    admins = await get_admins(Config.CHAT)
    if message.from_user is None and message.sender_chat:
        return True
    elif message.from_user.id in admins:
        return True
    else:
        return False

async def valid_chat(_, client, message: Message):
    if message.chat.type == "private":
        return True
    elif message.chat.id == Config.CHAT:
        return True
    elif Config.LOG_GROUP and message.chat.id == Config.LOG_GROUP:
        return True
    else:
        return False
    
chat_filter=filters.create(valid_chat) 

async def sudo_users(_, client, message: Message):
    if message.from_user is None and message.sender_chat:
        return False
    elif message.from_user.id in Config.SUDO:
        return True
    else:
        return False
    
sudo_filter=filters.create(sudo_users) 

async def get_playlist_str():
    if not Config.CALL_STATUS:
        pl="Player is idle and no song is playing.ㅤㅤㅤㅤ"
    if Config.STREAM_LINK:
        pl = f"🔈 Streaming [Live Stream]({Config.STREAM_LINK}) ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
    elif not Config.playlist:
        pl = f"🔈 Playlist is empty. Streaming [STARTUP_STREAM]({Config.STREAM_URL})ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
    else:
        if len(Config.playlist)>=25:
            tplaylist=Config.playlist[:25]
            pl=f"Listing first 25 songs of total {len(Config.playlist)} songs.\n"
            pl += f"▶️ **Playlist**: ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n" + "\n".join([
                f"**{i}**. **🎸{x[1]}**\n   👤**Requested by:** {x[4]}"
                for i, x in enumerate(tplaylist)
                ])
            tplaylist.clear()
        else:
            pl = f"▶️ **Playlist**: ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n" + "\n".join([
                f"**{i}**. **🎸{x[1]}**\n   👤**Requested by:** {x[4]}\n"
                for i, x in enumerate(Config.playlist)
            ])
    return pl



async def get_buttons():
    data=Config.DATA.get("FILE_DATA")
    if not Config.CALL_STATUS:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"🎸 Start the Player", callback_data="restart"),
                    InlineKeyboardButton('🗑 Close', callback_data='close'),
                ],
            ]
            )
    elif data.get('dur', 0) == 0:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{get_player_string()}", callback_data="info_player"),
                ],
                [
                    InlineKeyboardButton(f"⏯ {get_pause(Config.PAUSE)}", callback_data=f"{get_pause(Config.PAUSE)}"),
                    InlineKeyboardButton('🔊 Volume Control', callback_data='volume_main'),
                    InlineKeyboardButton('🗑 Close', callback_data='close'),
                ],
            ]
            )
    else:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{get_player_string()}", callback_data='info_player'),
                ],
                [
                    InlineKeyboardButton("⏮ Rewind", callback_data='rewind'),
                    InlineKeyboardButton(f"⏯ {get_pause(Config.PAUSE)}", callback_data=f"{get_pause(Config.PAUSE)}"),
                    InlineKeyboardButton(f"⏭ Seek", callback_data='seek'),
                ],
                [
                    InlineKeyboardButton("🔄 Shuffle", callback_data="shuffle"),
                    InlineKeyboardButton("⏩ Skip", callback_data="skip"),
                    InlineKeyboardButton("⏮ Replay", callback_data="replay"),
                ],
                [
                    InlineKeyboardButton('🔊 Volume Control', callback_data='volume_main'),
                    InlineKeyboardButton('🗑 Close', callback_data='close'),
                ]
            ]
            )
    return reply_markup


async def settings_panel():
    reply_markup=InlineKeyboardMarkup(
        [
            [
               InlineKeyboardButton(f"Player Mode", callback_data='info_mode'),
               InlineKeyboardButton(f"{'🔂 Non Stop Playback' if Config.IS_LOOP else '▶️ Play and Leave'}", callback_data='is_loop'),
            ],
            [
                InlineKeyboardButton("🎞 Video", callback_data=f"info_video"),
                InlineKeyboardButton(f"{'📺 Enabled' if Config.IS_VIDEO else '🎙 Disabled'}", callback_data='is_video'),
            ],
            [
                InlineKeyboardButton("🤴 Admin Only", callback_data=f"info_admin"),
                InlineKeyboardButton(f"{'🔒 Enabled' if Config.ADMIN_ONLY else '🔓 Disabled'}", callback_data='admin_only'),
            ],
            [
                InlineKeyboardButton("🪶 Edit Title", callback_data=f"info_title"),
                InlineKeyboardButton(f"{'✏️ Enabled' if Config.EDIT_TITLE else '🚫 Disabled'}", callback_data='edit_title'),
            ],
            [
                InlineKeyboardButton("🔀 Shuffle Mode", callback_data=f"info_shuffle"),
                InlineKeyboardButton(f"{'✅ Enabled' if Config.SHUFFLE else '🚫 Disabled'}", callback_data='set_shuffle'),
            ],
            [
                InlineKeyboardButton("👮 Auto Reply (PM Permit)", callback_data=f"info_reply"),
                InlineKeyboardButton(f"{'✅ Enabled' if Config.REPLY_PM else '🚫 Disabled'}", callback_data='reply_msg'),
            ],
            [
                InlineKeyboardButton('🗑 Close', callback_data='close'),
            ]
            
        ]
        )
    await sync_to_db()
    return reply_markup


async def recorder_settings():
    reply_markup=InlineKeyboardMarkup(
        [
        [
            InlineKeyboardButton(f"{'⏹ Stop Recording' if Config.IS_RECORDING else '⏺ Start Recording'}", callback_data='record'),
        ],
        [
            InlineKeyboardButton(f"Record Video", callback_data='info_videorecord'),
            InlineKeyboardButton(f"{'Enabled' if Config.IS_VIDEO_RECORD else 'Disabled'}", callback_data='record_video'),
        ],
        [
            InlineKeyboardButton(f"Video Dimension", callback_data='info_videodimension'),
            InlineKeyboardButton(f"{'Portrait' if Config.PORTRAIT else 'Landscape'}", callback_data='record_dim'),
        ],
        [
            InlineKeyboardButton(f"Custom Recording Title", callback_data='info_rectitle'),
            InlineKeyboardButton(f"{Config.RECORDING_TITLE if Config.RECORDING_TITLE else 'Default'}", callback_data='info_rectitle'),
        ],
        [
            InlineKeyboardButton(f"Recording Dump Channel", callback_data='info_recdumb'),
            InlineKeyboardButton(f"{Config.RECORDING_DUMP if Config.RECORDING_DUMP else 'Not Dumping'}", callback_data='info_recdumb'),
        ],
        [
            InlineKeyboardButton('🗑 Close', callback_data='close'),
        ]
        ]
    )
    await sync_to_db()
    return reply_markup

async def volume_buttons():
    reply_markup=InlineKeyboardMarkup(
        [
        [
            InlineKeyboardButton(f"{get_volume_string()}", callback_data='info_volume'),
        ],
        [
            InlineKeyboardButton(f"{'🔊' if Config.MUTED else '🔇'}", callback_data='mute'),
            InlineKeyboardButton(f"- 10", callback_data='volume_less'),
            InlineKeyboardButton(f"+ 10", callback_data='volume_add'),
        ],
        [
            InlineKeyboardButton(f"🔙 Back", callback_data='volume_back'),
            InlineKeyboardButton('🗑 Close', callback_data='close'),
        ]
        ]
    )
    return reply_markup


async def delete_messages(messages):
    await asyncio.sleep(Config.DELAY)
    for msg in messages:
        try:
            if msg.chat.type == "supergroup":
                await msg.delete()
        except:
            pass

#Database Config
async def sync_to_db():
    if Config.DATABASE_URI:
        await check_db() 
        await db.edit_config("ADMINS", Config.ADMINS)
        await db.edit_config("IS_VIDEO", Config.IS_VIDEO)
        await db.edit_config("IS_LOOP", Config.IS_LOOP)
        await db.edit_config("REPLY_PM", Config.REPLY_PM)
        await db.edit_config("ADMIN_ONLY", Config.ADMIN_ONLY)  
        await db.edit_config("SHUFFLE", Config.SHUFFLE)
        await db.edit_config("EDIT_TITLE", Config.EDIT_TITLE)
        await db.edit_config("CHAT", Config.CHAT)
        await db.edit_config("SUDO", Config.SUDO)
        await db.edit_config("REPLY_MESSAGE", Config.REPLY_MESSAGE)
        await db.edit_config("LOG_GROUP", Config.LOG_GROUP)
        await db.edit_config("STREAM_URL", Config.STREAM_URL)
        await db.edit_config("DELAY", Config.DELAY)
        await db.edit_config("SCHEDULED_STREAM", Config.SCHEDULED_STREAM)
        await db.edit_config("SCHEDULE_LIST", Config.SCHEDULE_LIST)
        await db.edit_config("IS_VIDEO_RECORD", Config.IS_VIDEO_RECORD)
        await db.edit_config("IS_RECORDING", Config.IS_RECORDING)
        await db.edit_config("WAS_RECORDING", Config.WAS_RECORDING)
        await db.edit_config("PORTRAIT", Config.PORTRAIT)
        await db.edit_config("RECORDING_DUMP", Config.RECORDING_DUMP)
        await db.edit_config("RECORDING_TITLE", Config.RECORDING_TITLE)
        await db.edit_config("HAS_SCHEDULE", Config.HAS_SCHEDULE)


async def sync_from_db():
    if Config.DATABASE_URI:  
        await check_db()     
        Config.ADMINS = await db.get_config("ADMINS") 
        Config.IS_VIDEO = await db.get_config("IS_VIDEO")
        Config.IS_LOOP = await db.get_config("IS_LOOP")
        Config.REPLY_PM = await db.get_config("REPLY_PM")
        Config.ADMIN_ONLY = await db.get_config("ADMIN_ONLY")
        Config.SHUFFLE = await db.get_config("SHUFFLE")
        Config.EDIT_TITLE = await db.get_config("EDIT_TITLE")
        Config.CHAT = int(await db.get_config("CHAT"))
        Config.playlist = await db.get_playlist()
        Config.LOG_GROUP = await db.get_config("LOG_GROUP")
        Config.SUDO = await db.get_config("SUDO") 
        Config.REPLY_MESSAGE = await db.get_config("REPLY_MESSAGE") 
        Config.DELAY = await db.get_config("DELAY") 
        Config.STREAM_URL = await db.get_config("STREAM_URL") 
        Config.SCHEDULED_STREAM = await db.get_config("SCHEDULED_STREAM") 
        Config.SCHEDULE_LIST = await db.get_config("SCHEDULE_LIST")
        Config.IS_VIDEO_RECORD = await db.get_config('IS_VIDEO_RECORD')
        Config.IS_RECORDING = await db.get_config("IS_RECORDING")
        Config.WAS_RECORDING = await db.get_config('WAS_RECORDING')
        Config.PORTRAIT = await db.get_config("PORTRAIT")
        Config.RECORDING_DUMP = await db.get_config("RECORDING_DUMP")
        Config.RECORDING_TITLE = await db.get_config("RECORDING_TITLE")
        Config.HAS_SCHEDULE = await db.get_config("HAS_SCHEDULE")

async def add_to_db_playlist(song):
    if Config.DATABASE_URI:
        song_={str(k):v for k,v in song.items()}
        db.add_to_playlist(song[5], song_)

async def clear_db_playlist(song=None, all=False):
    if Config.DATABASE_URI:
        if all:
            await db.clear_playlist()
        else:
            await db.del_song(song[5])

async def check_db():
    if not await db.is_saved("ADMINS"):
        db.add_config("ADMINS", Config.ADMINS)
    if not await db.is_saved("IS_VIDEO"):
        db.add_config("IS_VIDEO", Config.IS_VIDEO)
    if not await db.is_saved("IS_LOOP"):
        db.add_config("IS_LOOP", Config.IS_LOOP)
    if not await db.is_saved("REPLY_PM"):
        db.add_config("REPLY_PM", Config.REPLY_PM)
    if not await db.is_saved("ADMIN_ONLY"):
        db.add_config("ADMIN_ONLY", Config.ADMIN_ONLY)
    if not await db.is_saved("SHUFFLE"):
        db.add_config("SHUFFLE", Config.SHUFFLE)
    if not await db.is_saved("EDIT_TITLE"):
        db.add_config("EDIT_TITLE", Config.EDIT_TITLE)
    if not await db.is_saved("CHAT"):
        db.add_config("CHAT", Config.CHAT)
    if not await db.is_saved("SUDO"):
        db.add_config("SUDO", Config.SUDO)
    if not await db.is_saved("REPLY_MESSAGE"):
        db.add_config("REPLY_MESSAGE", Config.REPLY_MESSAGE)
    if not await db.is_saved("STREAM_URL"):
        db.add_config("STREAM_URL", Config.STREAM_URL)
    if not await db.is_saved("DELAY"):
        db.add_config("DELAY", Config.DELAY)
    if not await db.is_saved("LOG_GROUP"):
        db.add_config("LOG_GROUP", Config.LOG_GROUP)
    if not await db.is_saved("SCHEDULED_STREAM"):
        db.add_config("SCHEDULED_STREAM", Config.SCHEDULED_STREAM)
    if not await db.is_saved("SCHEDULE_LIST"):
        db.add_config("SCHEDULE_LIST", Config.SCHEDULE_LIST)
    if not await db.is_saved("IS_VIDEO_RECORD"):
        db.add_config("IS_VIDEO_RECORD", Config.IS_VIDEO_RECORD)
    if not await db.is_saved("PORTRAIT"):
        db.add_config("PORTRAIT", Config.PORTRAIT)  
    if not await db.is_saved("IS_RECORDING"):
        db.add_config("IS_RECORDING", Config.IS_RECORDING)
    if not await db.is_saved('WAS_RECORDING'):
        db.add_config('WAS_RECORDING', Config.WAS_RECORDING)
    if not await db.is_saved("RECORDING_DUMP"):
        db.add_config("RECORDING_DUMP", Config.RECORDING_DUMP)
    if not await db.is_saved("RECORDING_TITLE"):
        db.add_config("RECORDING_TITLE", Config.RECORDING_TITLE)
    if not await db.is_saved('HAS_SCHEDULE'):
        db.add_config("HAS_SCHEDULE", Config.HAS_SCHEDULE)
    

async def progress_bar(current, zero, total, start, msg):
    now = time.time()
    if total == 0:
        return
    if round((now - start) % 3) == 0 or current == total:
        speed = current / (now - start)
        percentage = current * 100 / total
        time_to_complete = round(((total - current) / speed)) * 1000
        time_to_complete = TimeFormatter(time_to_complete)
        progressbar = "[{0}{1}]".format(\
            ''.join(["▰" for i in range(math.floor(percentage / 5))]),
            ''.join(["▱" for i in range(20 - math.floor(percentage / 5))])
            )
        current_message = f"**Downloading** {round(percentage, 2)}% \n{progressbar}\n⚡️ **Speed**: {humanbytes(speed)}/s\n⬇️ **Downloaded**: {humanbytes(current)} / {humanbytes(total)}\n🕰 **Time Left**: {time_to_complete}"
        if msg:
            try:
                await msg.edit(text=current_message)
            except:
                pass
        LOGGER.info(f"Downloading {round(percentage, 2)}% ")



@timeout(10)
def is_audio(file):
    try:
        k=ffmpeg.probe(file)['streams']
        if k:
            return True
        else:
            return False
    except KeyError:
        return False
    except Exception as e:
        LOGGER.error(f"Stream Unsupported {e} ")
        return False
    

@timeout(10)#wait for maximum 10 sec, temp fix for ffprobe
def get_height_and_width(file):
    try:
        k=ffmpeg.probe(file)['streams']
        width=None
        height=None
        for f in k:
            try:
                width=int(f["width"])
                height=int(f["height"])
                if height >= 256:
                    break
            except KeyError:
                continue
    except:
        LOGGER.error("Error, This stream is not supported.")
        width, height = False, False
    return width, height


@timeout(10)
def get_duration(file):
    try:
        total=ffmpeg.probe(file)['format']['duration']
        return total
    except:
        return 0

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def get_player_string():
    now = time.time()
    data=Config.DATA.get('FILE_DATA')
    dur=int(float(data.get('dur', 0)))
    start = int(Config.DUR.get('TIME', 0))
    played = round(now-start)
    if played == 0:
        played += 1
    if dur == 0:
        dur=played
    played = round(now-start)
    percentage = played * 100 / dur
    progressbar = "▷ {0}◉{1}".format(\
            ''.join(["━" for i in range(math.floor(percentage / 5))]),
            ''.join(["─" for i in range(20 - math.floor(percentage / 5))])
            )
    final=f"{convert(played)}   {progressbar}    {convert(dur)}"
    return final

def get_volume_string():
    current = int(Config.VOLUME)
    if current == 0:
        current += 1
    if Config.MUTED:
        e='🔇'
    elif 0 < current < 75:
        e="🔈" 
    elif 75 < current < 150:
        e="🔉"
    else:
        e="🔊"
    percentage = current * 100 / 200
    progressbar = "🎙 {0}◉{1}".format(\
            ''.join(["━" for i in range(math.floor(percentage / 5))]),
            ''.join(["─" for i in range(20 - math.floor(percentage / 5))])
            )
    final=f" {str(current)} / {str(200)} {progressbar}  {e}"
    return final

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " days, ") if days else "") + \
        ((str(hours) + " hours, ") if hours else "") + \
        ((str(minutes) + " min, ") if minutes else "") + \
        ((str(seconds) + " sec, ") if seconds else "") + \
        ((str(milliseconds) + " millisec, ") if milliseconds else "")
    return tmp[:-2]

def set_config(value):
    if value:
        return False
    else:
        return True

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60      
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def get_pause(status):
    if status == True:
        return "Resume"
    else:
        return "Pause"


def stop_and_restart():
    os.system("git pull")
    time.sleep(10)
    os.execl(sys.executable, sys.executable, *sys.argv)


def get_image(title, pic, dur="Live"):
    newimage = "converted.jpg"
    image = Image.open(pic) 
    draw = ImageDraw.Draw(image) 
    font = ImageFont.truetype('font.ttf', 70)
    title = title[0:30]
    MAX_W = 1790
    dur=convert(int(float(dur)))
    if dur=="0:00:00":
        dur = "Live Stream"
    para=[f'Playing : {title}', f'Duration: {dur}']
    current_h, pad = 450, 20
    for line in para:
        w, h = draw.textsize(line, font=font)
        draw.text(((MAX_W - w) / 2, current_h), line, font=font, fill ="skyblue")
        current_h += h + pad
    image.save(newimage)
    return newimage

async def edit_config(var, value):
    if var == "STARTUP_STREAM":
        Config.STREAM_URL = value
    elif var == "CHAT":
        Config.CHAT = int(value)
    elif var == "LOG_GROUP":
        Config.LOG_GROUP = int(value)
    elif var == "DELAY":
        Config.DELAY = int(value)
    elif var == "REPLY_MESSAGE":
        Config.REPLY_MESSAGE = value
    elif var == "RECORDING_DUMP":
        Config.RECORDING_DUMP = value
    await sync_to_db()


async def update():
    await leave_call()
    if Config.HEROKU_APP:
        Config.HEROKU_APP.restart()
    else:
        Thread(
            target=stop_and_restart()
            ).start()


async def startup_check():
    if Config.LOG_GROUP:
        try:
            k=await bot.get_chat_member(Config.LOG_GROUP, Config.BOT_USERNAME)
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            LOGGER.error(f"LOG_GROUP var Found and @{Config.BOT_USERNAME} is not a member of the group.")
            Config.STARTUP_ERROR=f"LOG_GROUP var Found and @{Config.BOT_USERNAME} is not a member of the group."
            return False
    if Config.RECORDING_DUMP:
        try:
            k=await USER.get_chat_member(Config.RECORDING_DUMP, Config.USER_ID)
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            LOGGER.error(f"RECORDING_DUMP var Found and @{Config.USER_ID} is not a member of the group./ Channel")
            Config.STARTUP_ERROR=f"RECORDING_DUMP var Found and @{Config.USER_ID} is not a member of the group./ Channel"
            return False
        if not k.status in ["administrator", "creator"]:
            LOGGER.error(f"RECORDING_DUMP var Found and @{Config.USER_ID} is not a admin of the group./ Channel")
            Config.STARTUP_ERROR=f"RECORDING_DUMP var Found and @{Config.USER_ID} is not a admin of the group./ Channel"
            return False
    if Config.CHAT:
        try:
            k=await USER.get_chat_member(Config.CHAT, Config.USER_ID)
            if not k.status in ["administrator", "creator"]:
                LOGGER.warning(f"{Config.USER_ID} is not an admin in {Config.CHAT}, it is recommended to run the user as admin.")
            elif k.status in ["administrator", "creator"] and not k.can_manage_voice_chats:
                LOGGER.warning(f"{Config.USER_ID} is not having right to manage voicechat, it is recommended to promote with this right.")
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            Config.STARTUP_ERROR=f"The user account by which you generated the SESSION_STRING is not found on CHAT ({Config.CHAT})"
            LOGGER.error(f"The user account by which you generated the SESSION_STRING is not found on CHAT ({Config.CHAT})")
            return False
        try:
            k=await bot.get_chat_member(Config.CHAT, Config.BOT_USERNAME)
            if not k.status == "administrator":
                LOGGER.warning(f"{Config.BOT_USERNAME}, is not an admin in {Config.CHAT}, it is recommended to run the bot as admin.")
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            Config.STARTUP_ERROR=f"Bot Was Not Found on CHAT, it is recommended to add {Config.BOT_USERNAME} to {Config.CHAT}"
            LOGGER.warning(f"Bot Was Not Found on CHAT, it is recommended to add {Config.BOT_USERNAME} to {Config.CHAT}")
            pass
    if not Config.DATABASE_URI:
        LOGGER.warning("No DATABASE_URI , found. It is recommended to use a database.")
    return True
            

