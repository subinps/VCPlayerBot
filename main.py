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
    sync_from_db,
    check_changes
)
from user import group_call, USER
from utils import LOGGER
from config import Config
from pyrogram import idle
from bot import bot
import asyncio
import os

if Config.DATABASE_URI:
    from utils import db


async def main():
    await bot.start()
    Config.BOT_USERNAME = (await bot.get_me()).username
    LOGGER.info(f"{Config.BOT_USERNAME} Started.")
    if Config.DATABASE_URI:
        try:
            if await db.is_saved("RESTART"):
                msg=await db.get_config("RESTART")
                if msg:
                    try:
                        k=await bot.edit_message_text(msg['chat_id'], msg['msg_id'], text="Succesfully restarted.")
                        await db.del_config("RESTART")
                    except:
                        pass
            await check_changes()
            await sync_from_db()
        except Exception as e:
            LOGGER.error(f"Errors occured while setting up database for VCPlayerBot, check the value of DATABASE_URI. Full error - {str(e)}", exc_info=True)
            Config.STARTUP_ERROR="Errors occured while setting up database for VCPlayerBot, check the value of DATABASE_URI. Full error - {str(e)}"
            LOGGER.info("Activating debug mode, you can reconfigure your bot with /env command.")
            await bot.stop()
            from utils import debug
            await debug.start()
            await idle()
            return

    if Config.DEBUG:
        LOGGER.info("Debugging enabled by user, Now in debug mode.")
        Config.STARTUP_ERROR="Debugging enabled by user, Now in debug mode."
        from utils import debug
        await bot.stop()
        await debug.start()
        await idle()
        return

    try:
        await group_call.start()
        Config.USER_ID = (await USER.get_me()).id
        k=await startup_check()
        if k == False:
            LOGGER.error("Startup checks not passed , bot is quiting")
            await bot.stop()
            LOGGER.info("Activating debug mode, you can reconfigure your bot with /env command.")
            from utils import debug
            await debug.start()
            await idle()
            return

        if Config.IS_LOOP:
            if Config.playlist:
                await play()
                LOGGER.info("Loop play enabled and playlist is not empty, resuming playlist.")
            else:
                LOGGER.info("Loop play enabled , starting playing startup stream.")
                await start_stream()
    except Exception as e:
        LOGGER.error(f"Startup was unsuccesfull, Errors - {e}", exc_info=True)
        LOGGER.info("Activating debug mode, you can reconfigure your bot with /env command.")
        Config.STARTUP_ERROR=f"Startup was unsuccesfull, Errors - {e}"
        from utils import debug
        await bot.stop()
        await debug.start()
        await idle()
        return

    await idle()
    await bot.stop()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())



