# SCP-079-MANAGE - One ring to rule them all
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-MANAGE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from json import dumps, loads
from time import sleep
from typing import List, Optional, Union

from pyrogram import Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, general_link, get_text, message_link, thread, user_mention
from .file import crypt_file, delete_file, get_new_path
from .telegram import edit_message_text, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def edit_evidence(client: Client, message: Message, project: str, action: str, uid: str, level: str, rule: str,
                  name: str = None, more: str = None, reason: str = None) -> Optional[Union[bool, Message]]:
    # Edit the evidence's report message
    result = None
    try:
        cid = message.chat.id
        mid = message.message_id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"原始项目：{code(project)}\n"
                f"状态：{code(f'已{action}')}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")

        if name:
            text += f"用户昵称：{code(name)}\n"

        if more:
            text += f"附加信息：{code(more)}\n"

        if reason:
            text += f"原因：{code(reason)}\n"

        result = edit_message_text(client, cid, mid, text)
    except Exception as e:
        logger.warning(f"Edit evidence error: {e}", exc_info=True)

    return result


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        text = format_data(
            sender="EMERGENCY",
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )
        thread(send_message, (client, glovar.hide_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str, data=None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def send_error(client: Client, message: Message, project: str, aid: int, action: str,
               reason: str = None) -> Optional[Union[bool, Message]]:
    # Send the error record message
    result = None
    try:
        # Attention: project admin can make a fake operator name
        text = (f"原始项目：{code(project)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code(action)}\n")
        if reason:
            text += f"原因：{code(reason)}\n"

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(glovar.error_channel_id)
            except FloodWait as e:
                flood_wait = True
                sleep(e.x + 1)
            except Exception as e:
                logger.info(f"Forward error message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.error_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Send error: {e}", exc_info=True)

    return result


def send_debug(client: Client, aid: int, action: str, context: Union[int, str], time: str = None,
               uid: int = None, em: Message = None, err_m: Message = None, reason: str = None) -> bool:
    # Send the debug message
    try:
        # Attention: project admin can make a fake operator name
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code(action)}\n"
                f"操作内容：{code(context)}\n")

        if time:
            text += f"例外时效：{code(time)}\n"

        if uid:
            text += f"原用户 ID：{code(uid)}\n"

        if em:
            text += f"原始记录：{general_link(em.message_id, message_link(em))}\n"

        if err_m:
            text += f"错误存档：{general_link(err_m.message_id, message_link(err_m))}\n"

        if reason:
            text += f"原因：{code(reason)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return False


def share_bad_channel(client: Client, cid: int) -> bool:
    # Share a bad channel with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers_bad,
            action="add",
            action_type="bad",
            data={
                "id": cid,
                "type": "channel"
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Share bad channel error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[dict, int, str],
               file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            if encrypt:
                # Encrypt the file, save to the tmp directory
                file_path = get_new_path()
                crypt_file("encrypt", file, file_path)
            else:
                # Send directly
                file_path = file

            result = send_document(client, channel_id, file_path, text)
            # Delete the tmp file
            if result and "tmp/" in file_path:
                thread(delete_file, (file_path,))
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        # Sending failed due to channel issue
        if result is False:
            # Use hide channel instead
            exchange_to_hide(client)
            thread(share_data, (client, receivers, action, action_type, data, file))

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False
