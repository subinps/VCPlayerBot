#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2021 Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.


#https://github.com/pyrogram/pyrogram/blob/4f585c156c1a2c6707793a8ad7f2f111515ca23b/pyrogram/client.py#L492-L518
#https://github.com/pyrogram/pyrogram/blob/4f585c156c1a2c6707793a8ad7f2f111515ca23b/pyrogram/client.py#L806-1044

#Pyrogram downloader modified to suit my needs. 
#Downloads the file from telegram servers and retures the path of the file without waiting for the whole download to finish.
#Copyright (C) @subinps


from .logger import LOGGER
import asyncio
import os
import re
import asyncio
import os
import time
from datetime import datetime
from hashlib import sha256
from bot import bot
import pyrogram
from pyrogram import raw
from pyrogram import utils
from pyrogram.crypto import aes
from pyrogram.errors import (
    VolumeLocNotFound,
    AuthBytesInvalid
)
from pyrogram.session import(
    Auth, 
    Session
)
from pyrogram.file_id import(
    FileId, 
    FileType, 
    ThumbnailSource
)
from pyrogram.file_id import (
    FileId, 
    FileType, 
    PHOTO_TYPES
)


DEFAULT_DOWNLOAD_DIR = "downloads/"

class Downloader():
    def __init__(
        self,
        ):
        super().__init__()
        self.client = bot

    async def pyro_dl(self, file_id):
        file_id_obj = FileId.decode(file_id)
        file_type = file_id_obj.file_type
        mime_type = ""
        date = 0
        file_name = ""

        directory, file_name = os.path.split(file_name)
        if not os.path.isabs(file_name):
            directory = self.client.PARENT_DIR / (directory or DEFAULT_DOWNLOAD_DIR)
        if not file_name:
            guessed_extension = self.client.guess_extension(mime_type)

            if file_type in PHOTO_TYPES:
                extension = ".jpg"
            elif file_type == FileType.VOICE:
                extension = guessed_extension or ".ogg"
            elif file_type in (FileType.VIDEO, FileType.ANIMATION, FileType.VIDEO_NOTE):
                extension = guessed_extension or ".mp4"
            elif file_type == FileType.DOCUMENT:
                extension = guessed_extension or ".zip"
            elif file_type == FileType.STICKER:
                extension = guessed_extension or ".webp"
            elif file_type == FileType.AUDIO:
                extension = guessed_extension or ".mp3"
            else:
                extension = ".unknown"

            file_name = "{}_{}_{}{}".format(
                FileType(file_id_obj.file_type).name.lower(),
                datetime.fromtimestamp(date or time.time()).strftime("%Y-%m-%d_%H-%M-%S"),
                self.client.rnd_id(),
                extension
            )
        final_file_path = os.path.abspath(re.sub("\\\\", "/", os.path.join(directory, file_name)))
        os.makedirs(directory, exist_ok=True)
        downloaderr = self.handle_download(file_id_obj, final_file_path)
        asyncio.get_event_loop().create_task(downloaderr)
        return final_file_path
    
    async def handle_download(self, file_id_obj, final_file_path):  
        try:
            await self.get_file(
                file_id=file_id_obj,
                filename=final_file_path
            )
        except Exception as e:
            LOGGER.error(str(e), exc_info=True)

            try:
                os.remove(final_file_path)
            except OSError:
                pass
        else:
            return final_file_path or None

    async def get_file(
        self,
        file_id: FileId,
        filename: str,
    ) -> str:
        dc_id = file_id.dc_id

        async with self.client.media_sessions_lock:
            session = self.client.media_sessions.get(dc_id, None)

            if session is None:
                if dc_id != await self.client.storage.dc_id():
                    session = Session(
                        self.client, dc_id, await Auth(self.client, dc_id, await self.client.storage.test_mode()).create(),
                        await self.client.storage.test_mode(), is_media=True
                    )
                    await session.start()

                    for _ in range(3):
                        exported_auth = await self.client.send(
                            raw.functions.auth.ExportAuthorization(
                                dc_id=dc_id
                            )
                        )

                        try:
                            await session.send(
                                raw.functions.auth.ImportAuthorization(
                                    id=exported_auth.id,
                                    bytes=exported_auth.bytes
                                )
                            )
                        except AuthBytesInvalid:
                            continue
                        else:
                            break
                    else:
                        await session.stop()
                        raise AuthBytesInvalid
                else:
                    session = Session(
                        self.client, dc_id, await self.client.storage.auth_key(),
                        await self.client.storage.test_mode(), is_media=True
                    )
                    await session.start()

                self.client.media_sessions[dc_id] = session

        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id,
                    access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(
                        chat_id=-file_id.chat_id
                    )
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash
                    )

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size
            )

        limit = 1024 * 1024
        offset = 0
        file_name = ""

        try:
            r = await session.send(
                raw.functions.upload.GetFile(
                    location=location,
                    offset=offset,
                    limit=limit
                ),
                sleep_threshold=30
            )

            if isinstance(r, raw.types.upload.File):
                #with tempfile.NamedTemporaryFile("wb", delete=False) as f:
                with open(filename, 'wb') as f:
                    file_name = filename
                    while True:
                        chunk = r.bytes

                        if not chunk:
                            break

                        f.write(chunk)

                        offset += limit
                        r = await session.send(
                            raw.functions.upload.GetFile(
                                location=location,
                                offset=offset,
                                limit=limit
                            ),
                            sleep_threshold=30
                        )

            elif isinstance(r, raw.types.upload.FileCdnRedirect):
                async with self.client.media_sessions_lock:
                    cdn_session = self.client.media_sessions.get(r.dc_id, None)

                    if cdn_session is None:
                        cdn_session = Session(
                            self.client, r.dc_id, await Auth(self.client, r.dc_id, await self.client.storage.test_mode()).create(),
                            await self.client.storage.test_mode(), is_media=True, is_cdn=True
                        )

                        await cdn_session.start()

                        self.client.media_sessions[r.dc_id] = cdn_session

                try:
                    with open(filename, 'wb') as f:
                        file_name = f
                        while True:
                            r2 = await cdn_session.send(
                                raw.functions.upload.GetCdnFile(
                                    file_token=r.file_token,
                                    offset=offset,
                                    limit=limit
                                )
                            )

                            if isinstance(r2, raw.types.upload.CdnFileReuploadNeeded):
                                try:
                                    await session.send(
                                        raw.functions.upload.ReuploadCdnFile(
                                            file_token=r.file_token,
                                            request_token=r2.request_token
                                        )
                                    )
                                except VolumeLocNotFound:
                                    break
                                else:
                                    continue

                            chunk = r2.bytes

                            # https://core.telegram.org/cdn#decrypting-files
                            decrypted_chunk = aes.ctr256_decrypt(
                                chunk,
                                r.encryption_key,
                                bytearray(
                                    r.encryption_iv[:-4]
                                    + (offset // 16).to_bytes(4, "big")
                                )
                            )

                            hashes = await session.send(
                                raw.functions.upload.GetCdnFileHashes(
                                    file_token=r.file_token,
                                    offset=offset
                                )
                            )

                            # https://core.telegram.org/cdn#verifying-files
                            for i, h in enumerate(hashes):
                                cdn_chunk = decrypted_chunk[h.limit * i: h.limit * (i + 1)]
                                assert h.hash == sha256(cdn_chunk).digest(), f"Invalid CDN hash part {i}"

                            f.write(decrypted_chunk)

                            offset += limit

                            if len(chunk) < limit:
                                break
                except Exception as e:
                    LOGGER.error(e, exc_info=True)
                    raise e
        except Exception as e:
            if not isinstance(e, pyrogram.StopTransmission):
                LOGGER.error(str(e), exc_info=True)
            try:
                os.remove(file_name)
            except OSError:
                pass

            return ""
        else:
            return file_name