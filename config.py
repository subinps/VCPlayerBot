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

import os
import re
from logger import LOGGER

Y_PLAY=False
YSTREAM=False
STREAM=os.environ.get("STARTUP_STREAM", "https://www.youtube.com/watch?v=zcrUCvBD16k")
regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
match = re.match(regex,STREAM)
if match:
    YSTREAM=True
    finalurl=STREAM
    LOGGER.warning("YouTube Stream is set as STARTUP STREAM")
elif STREAM.startswith("https://t.me/DumpPlaylist"):
    try:
        msg_id=STREAM.split("/", 4)[4]
        finalurl=int(msg_id)
        Y_PLAY=True
        LOGGER.warning("YouTube Playlist is set as STARTUP STREAM")
    except:
        finalurl="http://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/playlist.m3u8"
        LOGGER.error("Unable to fetch youtube playlist, starting Safari TV")
        pass
else:
    finalurl=STREAM

class Config:
    #Telegram API Stuffs
    ADMIN = os.environ.get("ADMINS", '')
    ADMINS = [int(admin) for admin in (ADMIN).split()]
    API_ID = int(os.environ.get("API_ID", ''))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")     
    SESSION = os.environ.get("SESSION_STRING", "")
    BOT_USERNAME=None

    #Stream Chat and Log Group
    CHAT = int(os.environ.get("CHAT", ""))
    LOG_GROUP=os.environ.get("LOG_GROUP", "")
    if LOG_GROUP:
        LOG_GROUP=int(LOG_GROUP)
    else:
        LOG_GROUP=None

    #Stream 
    STREAM_URL=finalurl
    YPLAY=Y_PLAY
    YSTREAM=YSTREAM

    #Optional Configuration
    SHUFFLE=bool(os.environ.get("SHUFFLE", True))
    ADMIN_ONLY=os.environ.get("ADMIN_ONLY", "N")
    REPLY_MESSAGE=os.environ.get("REPLY_MESSAGE", None)
    if REPLY_MESSAGE:
        REPLY_MESSAGE=REPLY_MESSAGE
        LOGGER.warning("Reply Message Found, Enabled PM MSG")
    else:
        REPLY_MESSAGE=None
    EDIT_TITLE = os.environ.get("EDIT_TITLE", True)
    if EDIT_TITLE == "NO":
        EDIT_TITLE=None
        LOGGER.warning("Title Editing turned off")
    

    #others
    ADMIN_CACHE=False
    playlist=[]
    msg = {}
    CONV = {}
    FFMPEG_PROCESSES={}
    GET_FILE={}
    STREAM_END={}
    CALL_STATUS=False
    PAUSE=False
    STREAM_LINK=False
    HELP="""
<b>How Can I Play Video?</b>

You have file options.
 1. Play a video from a YouTube link.
    Command: <b>/play</b>
    <i>You can use this as a reply to a youtube link or pass link along command.</i>
 2. Play from a telegram file.
    Command: <b>/play</b>
    <i>Reply to a supported media(video and documents).</i>
 3. Play from a YouTube playlist
    Command: <b>/yplay</b>
    <i>First get a playlist file from @GetPlaylistBot or @DumpPlaylist and reply to playlist file.</i>
 4. Live Stream
    Command: <b>/stream</b>
    <i>Pass a live stream url or any direct url to play it as stream.</i>
 5. Import an old playlist.
    Command: <b>/import</b>
    <i>Reply to a previously exported plaulist file. </i>

<b>How Can I Control Player?</b>
These are commands to control player.
 1. Skip a song.
    Command: <b>/skip</b>
    <i>You can pass a number greater than 2 to skip the song in that position.</i>
 2. Pause the player.
    Command: <b>/pause</b>
 3. Resume the player.
    Command: <b>/resume</b>
 4. Change Volume.
    Command: <b>/volume</b>
    <i>Pass the volume in between 1-200.</i>
 5. Leave the VC.
    Command: <b>/leave</b>
 6. Shuffle the playlist.
    Command: <b>/shuffle</b>
 7. Clear the current playlist queue.
    Command: <b>/clearplaylist</b>

<b>How Can I Export My Current Playlist?</b>
 1. Command: <b>/export</b>
    <i>To export current playlist for future use.</i>

<b>Other Commands</b>
 1. Update and restert the bot.
    Command: <b>/update</b> or <b>/restart</b>
 2. Get Logs
    Command: <b>/logs</b>

<b>How Can I Stream In My Group</b>
  <i>The source code of this bot is public and can be found at <a href=https://github.com/subinps/VCPlayerBot>VCPlayerBot.</a>\nYou can deploy your own bot and use in your group.</i>

"""

