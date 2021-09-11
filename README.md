# VCPlayerBot

![GitHub Repo stars](https://img.shields.io/github/stars/subinps/VCPlayerBot?color=blue&style=flat)
![GitHub issues](https://img.shields.io/github/issues/subinps/VCPlayerBot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/subinps/VCPlayerBot)
![GitHub contributors](https://img.shields.io/github/contributors/subinps/VCPlayerBot?style=flat)
![GitHub forks](https://img.shields.io/github/forks/subinps/VCPlayerBot?style=flat)

Telegram bot to stream videos in telegram voicechat for both groups and channels. Supports live strams, YouTube videos and telegram media.

## Config Vars:
### Mandatory Vars
1. `API_ID` : Get From [my.telegram.org](https://my.telegram.org/)
2. `API_HASH` : Get from [my.telegram.org](https://my.telegram.org)
3. `BOT_TOKEN` : [@Botfather](https://telegram.dog/BotFather)
4. `SESSION_STRING` : Generate From here [![GenerateStringName](https://img.shields.io/badge/repl.it-generateStringName-yellowgreen)](https://repl.it/@subinps/getStringName)
5. `CHAT` : ID of Channel/Group where the bot plays Music.
### Optional Vars
1. `LOG_GROUP` : Group to send Playlist, if CHAT is a Group()
2. `ADMINS` : ID of users who can use admin commands.
3. `STARTUP_STREAM` : This will be streamed on startups and restarts of bot. You can use either any STREAM_URL or a direct link of any video or a Youtube Live link. You can also use YouTube Playlist.Find a Telegram Link for your playlist from [PlayList Dumb](https://telegram.dog/DumpPlaylist) or get a PlayList from [PlayList Extract](https://telegram.dog/GetAPlaylistbot). The PlayList link should in form `https://t.me/DumpPlaylist/xxx`.
4. `REPLY_MESSAGE` : A reply to those who message the USER account in PM. Leave it blank if you do not need this feature. 
5. `ADMIN_ONLY` : Pass `Y` If you want to make /play command only for admins of `CHAT`. By default /play is available for all.



## Requirements
- Python 3.8 or Higher.
- [FFMpeg](https://www.ffmpeg.org/).



## Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/subinps/VCPlayerBot)

## Deploy to Railway
<p><a href=https://railway.app/new/template?template=https%3A%2F%2Fgithub.com%2Fsubinps%2FVCPlayerBot&envs=API_ID%2CAPI_HASH%2CBOT_TOKEN%2CCHAT%2CSESSION_STRING%2CLOG_GROUP%2CADMINS%2CSTARTUP_STREAM%2CREPLY_MESSAGE%2CADMIN_ONLY&optionalEnvs=LOG_GROUP%2CADMINS%2CSTARTUP_STREAM%2CREPLY_MESSAGE%2CADMIN_ONLY&API_IDDesc=Get+From+my.telegram.org&API_HASHDesc=Get+from+my.telegram.org&BOT_TOKENDesc=Get+from%40Botfather&CHATDesc=ID+of+Channel%2FGroup+where+the+bot+plays+Music.&SESSION_STRINGDesc=Pyrogram+string+session+of+a+user+account&LOG_GROUPDesc=Group+to+send+Playlist%2C+if+CHAT+is+a+Group%28%29&ADMINSDesc=+ID+of+users+who+can+use+admin+commands.&STARTUP_STREAMDesc=This+will+be+streamed+on+startups+and+restarts+of+bot.+You+can+use+either+any+STREAM_URL+or+a+direct+link+of+any+video+or+a+Youtube+Live+link.+You+can+also+use+YouTube+Playlist.Find+a+Telegram+Link+for+your+playlist+from+%40DumpPlaylist+or+get+a+PlayList+from++%40GetPlaylistBot.+&REPLY_MESSAGEDesc=A+reply+to+those+who+message+the+USER+account+in+PM.+Leave+it+blank+if+you+do+not+need+this+feature.&ADMIN_ONLYDesc=Pass+Y+If+you+want+to+make+%2Fplay+command+only+for+admins+of+CHAT.+By+default+%2Fplay+is+available+for+all&referralCode=subinps> <img src="https://img.shields.io/badge/Deploy%20To%20Railway-blueviolet?style=for-the-badge&logo=railway" width="200""/></a></p>

⚠️ Warning:

Railway.app may ban your railway account if you tried to play DMCA contents. Its is hereby forewarned that we wont be responsible for any loss caused to you. Proceed at your own risk.
 
## Deploy to VPS

```sh
git clone https://github.com/subinps/VCPlayerBot
cd VCPlayerBot
pip3 install -r requirements.txt
# <Create Variables appropriately>
python3 main.py
```

## Features

- Playlist, queue.
- Supports Play from Youtube Playlist.
- Change VoiceChat title to current playing song name.
- Supports Live streaming from youtube
- Play from telegram file supported.
- Starts Radio after if no songs in playlist.
- Automatically downloads audio for the first two tracks in the playlist to ensure smooth playing
- Automatic restart even if heroku restarts.
- Support exporting and importing playlist.

### Note

[Note To A So Called Dev](https://telegram.dog/GetTGLink/802):  

Kanging this codes and and editing a few lines and releasing a V.x of your repo wont make you a Developer.
Fork the repo and edit as per your needs.

## LICENSE

- [GNU General Public License](./LICENSE)


## CREDITS

- [py-tgcalls](https://github.com/pytgcalls/pytgcalls)
- [Dan](https://github.com/delivrance) for [Pyrogram](https://github.com/pyrogram/pyrogram)


