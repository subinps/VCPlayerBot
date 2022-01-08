# VCPlayerBot

![GitHub Repo stars](https://img.shields.io/github/stars/subinps/VCPlayerBot?color=blue&style=flat)
![GitHub issues](https://img.shields.io/github/issues/subinps/VCPlayerBot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/subinps/VCPlayerBot)
![GitHub contributors](https://img.shields.io/github/contributors/subinps/VCPlayerBot?style=flat)
![GitHub forks](https://img.shields.io/github/forks/subinps/VCPlayerBot?style=flat)

Telegram bot to stream videos in telegram voicechat for both groups and channels. Supports live streams, YouTube videos and telegram media. With record stream support, Schedule streams, and many more.

## Config Vars:
### Mandatory Vars
1. `API_ID` : Get From [my.telegram.org](https://my.telegram.org/)
2. `API_HASH` : Get from [my.telegram.org](https://my.telegram.org)
3. `BOT_TOKEN` : [@Botfather](https://telegram.dog/BotFather)
4. `SESSION_STRING` : Generate From here [![GenerateStringName](https://img.shields.io/badge/repl.it-generateStringName-yellowgreen)](https://repl.it/@subinps/getStringName)
5. `CHAT` : ID of Channel/Group where the bot plays Music.

## Recommended Optional Vars

1. `DATABASE_URI`: MongoDB database Url, get from [mongodb](https://cloud.mongodb.com). This is an optional var, but it is recomonded to use this to experiance the full features.
2. `HEROKU_API_KEY`: Your heroku api key. Get one from [here](https://dashboard.heroku.com/account/applications/authorizations/new)
3. `HEROKU_APP_NAME`: Your heroku apps name.
4. `FILTERS`: Filter the search for channel play. Channel play means you can play all the files in a purticular channel using /cplay command. Current filters are `video document` . For searching audio files use `video document audio` . for video only search , use `video` and so on.

### Optional Vars
1. `LOG_GROUP` : Group to send Playlist, if CHAT is a Group()
2. `ADMINS` : ID of users who can use admin commands.
3. `STARTUP_STREAM` : This will be streamed on startups and restarts of bot. You can use either any STREAM_URL or a direct link of any video or a Youtube Live link. You can also use YouTube Playlist.Find a Telegram Link for your playlist from [PlayList Dumb](https://telegram.dog/DumpPlaylist) or get a PlayList from [PlayList Extract](https://telegram.dog/GetAPlaylistbot). The PlayList link should in form `https://t.me/DumpPlaylist/xxx`.
4. `REPLY_MESSAGE` : A reply to those who message the USER account in PM. Leave it blank if you do not need this feature. (Configurable through bot if mongodb added.)
5. `ADMIN_ONLY` : Pass `True` If you want to make /play command only for admins of `CHAT`. By default /play is available for all.(Configurable through bot if mongodb added.)
6. `DATABASE_NAME`: Database name for your mongodb database.
7. `SHUFFLE` : Make it `False` if you dont want to shuffle playlists. (Configurable through bot if mongodb added.)
8. `EDIT_TITLE` : Make it `False` if you do not want the bot to edit video chat title according to playing song. (Configurable through bot if mongodb added.)
9. `RECORDING_DUMP` : A Channel ID with the USER account as admin, to dump video chat recordings.
10. `RECORDING_TITLE`: A custom title for your videochat recordings.
11. `TIME_ZONE` : Time Zone of your country, by default IST
12. `IS_VIDEO_RECORD` : Make it `False` if you do not want to record video, and only audio will be recorded.(Configurable through bot if mongodb added.)
13. `IS_LOOP` ; Make it `False` if you do not want 24 / 7 Video Chat. (Configurable through bot if mongodb added.)
14. `IS_VIDEO` : Make it `False` if you want to use the player as a musicplayer without video. (Configurable through bot if mongodb added.)
15. `PORTRAIT`: Make it `True` if you want the video recording in portrait mode. (Configurable through bot if mongodb added.)
16. `DELAY` : Choose the time limit for commands deletion. 10 sec by default.
18. `QUALITY` : Customize the quality of video chat, use one of `high`, `medium`, `low` . 
19. `BITRATE` : Bitrate of audio (Not recommended to change).
20. `FPS` : Fps of video to be played (Not recommended to change.)



## Requirements
- Python 3.8 or Higher.
- [FFMpeg](https://www.ffmpeg.org/).



## Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://telegram.dog/XTZ_HerokuBot?start=c3ViaW5wcy9WQ1BsYXllckJvdCBtYWlu)

## Deploy to Railway
<p><a href=https://github.com/subinps/VCPlayerBot/issues/7> <img src="https://img.shields.io/badge/Deploy%20To%20Railway-blueviolet?style=for-the-badge&logo=railway" width="200""/></a></p>

 
## Deploy to VPS

```sh
git clone https://github.com/subinps/VCPlayerBot
cd VCPlayerBot
pip3 install -r requirements.txt
# install node js
sudo bash install_node.sh
# <Create Variables appropriately (.env [optional])>
python3 main.py
```

## Features

- Playlist, queue.
- Zero downtime in playing.
- Supports Video Recording.
- Supports Scheduling voicechats.
- Cool UI for controling the player.
- Customizabe to audio or video.
- Custom quality for video chats.
- Supports Play from Youtube Playlist.
- Change VoiceChat title to current playing song name.
- Supports Live streaming from youtube
- Play from telegram file supported.
- Starts Radio after if no songs in playlist.
- Automatic restart even if heroku restarts. (Configurable)
- Support exporting and importing playlist.

### Note

[Note To A So Called Dev](https://telegram.dog/subin_works/203): 

Kanging this codes and and editing a few lines and releasing a V.x  or an [alpha](https://telegram.dog/subin_works/204), beta , gama branches of your repo wont make you a Developer.
Fork the repo and edit as per your needs.

## LICENSE

- [GNU General Public License](./LICENSE)


## CREDITS

- [Laky-64](https://github.com/Laky-64) for [py-tgcalls](https://github.com/pytgcalls/pytgcalls)
- [Dan](https://github.com/delivrance) for [Pyrogram](https://github.com/pyrogram/pyrogram)


