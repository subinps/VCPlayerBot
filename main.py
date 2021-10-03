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
from utils import (
    play, 
    start_stream,
    startup_check, 
    sync_from_db
)
from user import group_call, USER
from logger import LOGGER
from config import Config
from pyrogram import idle
from bot import bot
import asyncio
import os
if Config.DATABASE_URI:
    from database import Database
    db = Database()

    
if not os.path.isdir("./downloads"):
    os.makedirs("./downloads")
else:
    for f in os.listdir("./downloads"):
        os.remove(f"./downloads/{f}")

async def main():
    await bot.start()
    Config.BOT_USERNAME = (await bot.get_me()).username
    LOGGER.info(f"{Config.BOT_USERNAME} Started.")
    try:
        await group_call.start()
        Config.USER_ID = (await USER.get_me()).id
        if Config.DATABASE_URI:
            if await db.is_saved("RESTART"):
                msg=await db.get_config("RESTART")
                if msg:
                    try:
                        k=await bot.edit_message_text(msg['chat_id'], msg['msg_id'], text="Succesfully restarted.")
                        await db.del_config("RESTART")
                    except:
                        pass
            await sync_from_db()
        k=await startup_check()
        if k == False:
            LOGGER.error("Startup checks not passed , bot is quiting")
            await bot.stop()
            await group_call.stop()
            return
        if Config.IS_LOOP:
            if Config.playlist:
                await play()
                LOGGER.info("Loop play enabled and playlist is not empty, resuming playlist.")
            else:
                LOGGER.info("Loop play enabled , starting playing startup stream.")
                await start_stream()
    except Exception as e:
        LOGGER.error(f"Startup was unsuccesfull, Errors - {e}")
        pass
    await idle()
    await bot.stop()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())



