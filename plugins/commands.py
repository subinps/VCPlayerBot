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

import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaDocument
from utils import is_admin
from pyrogram import Client, filters
from utils import update, is_admin
from config import Config
from logger import LOGGER
import os

HOME_TEXT = "<b>Hey  [{}](tg://user?id={}) 🙋‍♂️\n\nIam A Bot Built To Play or Stream Videos In Telegram VoiceChats.\nI Can Stream Any YouTube Video Or A Telegram File Or Even A YouTube Live.</b>"
admin_filter=filters.create(is_admin) 

@Client.on_message(filters.command(['start', f"start@{Config.BOT_USERNAME}"]))
async def start(client, message):
    buttons = [
        [
            InlineKeyboardButton('⚙️ Update Channel', url='https://t.me/subin_works'),
            InlineKeyboardButton('🧩 Source', url='https://github.com/subinps/VCPlayerBot')
        ],
        [
            InlineKeyboardButton('👨🏼‍🦯 Help', callback_data='help'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(HOME_TEXT.format(message.from_user.first_name, message.from_user.id), reply_markup=reply_markup)



@Client.on_message(filters.command(["help", f"help@{Config.BOT_USERNAME}"]))
async def show_help(client, message):
    buttons = [
        [
            InlineKeyboardButton('⚙️ Update Channel', url='https://t.me/subin_works'),
            InlineKeyboardButton('🧩 Source', url='https://github.com/subinps/VCPlayerBot'),
        ]
        ]
    reply_markup = InlineKeyboardMarkup(buttons)
    if Config.msg.get('help') is not None:
        await Config.msg['help'].delete()
    Config.msg['help'] = await message.reply_text(
        Config.HELP,
        reply_markup=reply_markup
        )
@Client.on_message(filters.command(['repo', f"repo@{Config.BOT_USERNAME}"]))
async def repo_(client, message):
    buttons = [
        [
            InlineKeyboardButton('🧩 Repository', url='https://github.com/subinps/VCPlayerBot'),
            InlineKeyboardButton('⚙️ Update Channel', url='https://t.me/subin_works'),
            
        ],
    ]
    await message.reply("<b>The source code of this bot is public and can be found at <a href=https://github.com/subinps/VCPlayerBot>VCPlayerBot.</a>\nYou can deploy your own bot and use in your group.\n\nFeel free to star☀️ the repo if you liked it 🙃.</b>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command(['restart', 'update', f"restart@{Config.BOT_USERNAME}", f"update@{Config.BOT_USERNAME}"]) & admin_filter)
async def update_handler(client, message):
    if Config.HEROKU_APP:
        await message.reply("Heroku APP found, Restarting app to update.")
    else:
        await message.reply("No Heroku APP found, Trying to restart.")
    await update()

@Client.on_message(filters.command(['logs', f"logs@{Config.BOT_USERNAME}"]) & admin_filter)
async def get_logs(client, message):
    logs=[]
    if os.path.exists("ffmpeg.txt"):
        logs.append(InputMediaDocument("ffmpeg.txt", caption="FFMPEG Logs"))
    if os.path.exists("ffmpeg.txt"):
        logs.append(InputMediaDocument("botlog.txt", caption="Bot Logs"))
    if logs:
        try:
            await message.reply_media_group(logs)
        except:
            await message.reply("Errors occured while uploading log file.")
            pass
        logs.clear()
    else:
        await message.reply("No log files found.")

@Client.on_message(filters.command(['env', f"env@{Config.BOT_USERNAME}"]) & filters.user(Config.SUDO))
async def set_heroku_var(client, message):
    if not Config.HEROKU_APP:
        buttons = [[InlineKeyboardButton('Heroku API_KEY', url='https://dashboard.heroku.com/account/applications/authorizations/new')]]
        await message.reply(
            text="No heroku app found, this command needs the following heroku vars to be set.\n\n1. <code>HEROKU_API_KEY</code>: Your heroku account api key.\n2. <code>HEROKU_APP_NAME</code>: Your heroku app name.", 
            reply_markup=InlineKeyboardMarkup(buttons)) 
        return     
    if " " in message.text:
        cmd, env = message.text.split(" ", 1)
        if  not "=" in env:
            return await message.reply("You should specify the value for env.\nExample: /env CHAT=-100213658211")
        var, value = env.split("=", 2)
        config = Config.HEROKU_APP.config()
        if not value:
            m=await message.reply(f"No value for env specified. Trying to delete env {var}.")
            await asyncio.sleep(2)
            if var in config:
                del config[var]
                await m.edit(f"Sucessfully deleted {var}")
                config[var] = None               
            else:
                await m.edit(f"No env named {var} found. Nothing was changed.")
            return
        if var in config:
            m=await message.reply(f"Variable already found. Now edited to {value}")
        else:
            m=await message.reply(f"Variable not found, Now setting as new var.")
        await asyncio.sleep(2)
        await m.edit(f"Succesfully set {var} with value {value}, Now Restarting to take effect of changes...")
        config[var] = str(value)
    else:
        await message.reply("You haven't provided any value for env, you should follow the correct format.\nExample: <code>/env CHAT=-1020202020202</code> to change or set CHAT var.\n<code>/env REPLY_MESSAGE= <code>To delete REPLY_MESSAGE.")