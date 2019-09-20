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

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .channel import send_debug, share_data
from .etc import button_data, code, get_int, get_now, get_subject, italic, user_mention
from .file import save
from .telegram import resolve_username

# Enable logging
logger = logging.getLogger(__name__)


def add_channel(client: Client, the_type: str, the_id: int, aid: int, reason: str = None,
                force: bool = False) -> str:
    # Add channel
    result = ""
    try:
        if the_type == "bad":
            action_text = "添加频道黑名单"
        else:
            action_text = "添加频道白名单"

        result += (f"执行操作：{code(action_text)}\n"
                   f"频道 ID：{code(the_id)}\n")
        if the_id not in eval(f"glovar.{the_type}_ids")["channels"] or force:
            # Local
            eval(f"glovar.{the_type}_ids")["channels"].add(the_id)
            save(f"{the_type}_ids")

            if the_type == "bad":
                if the_id in glovar.except_ids["channels"]:
                    glovar.except_ids["channels"].discard(the_id)
                    save("except_ids")
            else:
                if the_id in glovar.except_ids["channels"]:
                    glovar.bad_ids["channels"].discard(the_id)
                    save("bad_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers[the_type],
                action="add",
                action_type=the_type,
                data={
                    "id": the_id,
                    "type": "channel"
                }
            )
            result += f"结果：{code('操作成功')}\n"
            send_debug(client, aid, action_text, None, the_id, None, None, reason)
        else:
            if the_type == "bad":
                reason = "频道已在黑名单中"
            else:
                reason = "频道已在白名单中"

            result += (f"结果：{code('未操作')}\n"
                       f"原因：{code(reason)}\n")
    except Exception as e:
        logger.warning(f"Add channel error: {e}", exc_info=True)

    return result


def check_subject(client: Client, message: Message) -> (str, InlineKeyboardMarkup):
    # Check the subject's status
    text = ""
    markup = None
    try:
        aid = message.from_user.id
        the_id = 0
        id_text, _, _ = get_subject(message)
        if id_text:
            the_id = get_int(id_text)
            if not the_id:
                _, the_id = resolve_username(client, id_text)
        elif message.forward_from:
            the_id = message.forward_from.id
        elif message.forward_from_chat:
            the_id = message.forward_from_chat.id

        if the_id and the_id != glovar.debug_channel_id:
            if the_id > 0:
                now = get_now()
                is_bad = the_id in glovar.bad_ids["users"]
                is_watch_ban = glovar.watch_ids["ban"].get(the_id, 0) > now
                is_watch_delete = glovar.watch_ids["delete"].get(the_id, 0) > now
                text = (f"管理员：{user_mention(aid)}\n"
                        f"用户 ID：{code(the_id)}\n"
                        f"黑名单：{code(is_bad)}\n"
                        f"封禁追踪：{code(is_watch_ban)}\n"
                        f"删除追踪：{code(is_watch_delete)}\n")
                total_score = sum(glovar.user_ids.get(the_id, glovar.default_user_status).values())
                text += f"总分：{code(f'{total_score:.1f}')}\n\n"
                for project in glovar.default_user_status:
                    project_score = glovar.user_ids.get(the_id, glovar.default_user_status)[project]
                    if project_score:
                        text += "\t" * 4
                        text += (f"{italic(project.upper())}    "
                                 f"{code(f'{project_score:.1f}')}\n")

                bad_data = button_data("check", "bad", the_id)
                score_data = button_data("check", "score", the_id)
                watch_data = button_data("check", "watch", the_id)
                cancel_data = button_data("check", "cancel", the_id)
                if is_bad or total_score or is_watch_ban or is_watch_delete:
                    markup_list = [
                        [],
                        [
                            InlineKeyboardButton(
                                text="取消",
                                callback_data=cancel_data
                            )
                        ]
                    ]
                    if is_bad:
                        markup_list[0].append(
                            InlineKeyboardButton(
                                text="解禁用户",
                                callback_data=bad_data
                            )
                        )

                    if total_score:
                        markup_list[0].append(
                            InlineKeyboardButton(
                                text="清空评分",
                                callback_data=score_data
                            )
                        )

                    if is_watch_delete or is_watch_ban:
                        markup_list[0].append(
                            InlineKeyboardButton(
                                text="移除追踪",
                                callback_data=watch_data
                            )
                        )

                    markup = InlineKeyboardMarkup(markup_list)
            else:
                is_bad = the_id in glovar.bad_ids["channels"]
                is_except = the_id in glovar.except_ids["channels"]
                text = (f"管理员：{user_mention(aid)}\n"
                        f"频道 ID：{code(the_id)}\n"
                        f"受限频道：{code(bool(message.forward_from_chat.restrictions))}\n"
                        f"黑名单：{code(is_bad)}\n"
                        f"白名单：{code(is_except)}\n")
                bad_data = button_data("check", "bad", the_id)
                except_data = button_data("check", "except", the_id)
                cancel_data = button_data("check", "cancel", the_id)
                if is_bad:
                    bad_text = "移除黑名单"
                else:
                    bad_text = "添加黑名单"

                if is_except:
                    except_text = "移除白名单"
                else:
                    except_text = "添加白名单"

                markup_list = [
                    [
                        InlineKeyboardButton(
                            text=bad_text,
                            callback_data=bad_data
                        ),
                        InlineKeyboardButton(
                            text=except_text,
                            callback_data=except_data
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="取消",
                            callback_data=cancel_data
                        )
                    ]
                ]
                markup = InlineKeyboardMarkup(markup_list)
        elif not (message.forward_from or message.forward_from_chat or message.forward_sender_name):
            text = (f"管理员：{user_mention(aid)}\n"
                    f"结果：{code('无法显示')}\n"
                    f"原因：{code('格式有误')}\n")
    except Exception as e:
        logger.warning(f"Check subject error: {e}", exc_info=True)

    return text, markup


def remove_bad_user(client: Client, the_id: int, aid: int, debug: bool = False, reason: str = None,
                    force: bool = False) -> str:
    # Remove bad user
    result = ""
    try:
        action_text = "解禁用户"
        result += (f"执行操作：{code(action_text)}\n"
                   f"用户 ID：{code(the_id)}\n")
        if the_id in glovar.bad_ids["users"] or force:
            # Local
            glovar.bad_ids["users"].discard(the_id)
            save("bad_ids")

            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)
            save("watch_ids")

            glovar.user_ids.pop(the_id, {})
            save("user_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["bad"],
                action="remove",
                action_type="bad",
                data={
                    "id": the_id,
                    "type": "user"
                }
            )
            result += f"结果：{code('操作成功')}\n"
            if debug:
                send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += (f"结果：{code('未操作')}\n"
                       f"原因：{code('用户不在黑名单中')}\n")
    except Exception as e:
        logger.warning(f"Remove bad object error: {e}", exc_info=True)

    return result


def remove_channel(client: Client, the_type: str, the_id: int, aid: int, reason: str = None,
                   force: bool = False) -> str:
    # Remove channel
    result = ""
    try:
        if the_type == "bad":
            action_text = "移除频道黑名单"
        else:
            action_text = "移除频道白名单"

        result += (f"执行操作：{code(action_text)}\n"
                   f"频道 ID：{code(the_id)}\n")
        if the_id in eval(f"glovar.{the_type}_ids")["channels"] or force:
            # Local
            eval(f"glovar.{the_type}_ids")["channels"].discard(the_id)
            save(f"{the_type}_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers[the_type],
                action="remove",
                action_type=the_type,
                data={
                    "id": the_id,
                    "type": "channel"
                }
            )
            result += f"结果：{code('操作成功')}\n"
            send_debug(client, aid, action_text, None, the_id, None, None, reason)
        else:
            if the_type == "bad":
                reason = "频道不在黑名单中"
            else:
                reason = "频道不在白名单中"

            result += (f"结果：{code('未操作')}\n"
                       f"原因：{code(reason)}\n")
    except Exception as e:
        logger.warning(f"Remove channel error: {e}", exc_info=True)

    return result


def remove_score(client: Client, the_id: int, aid: int = None, reason: str = None,
                 force: bool = False) -> str:
    # Remove watched user
    result = ""
    try:
        action_text = "清空用户评分"
        result += (f"执行操作：{code(action_text)}\n"
                   f"用户 ID：{code(the_id)}\n")
        if (glovar.user_ids.get(the_id, {}) and sum(glovar.user_ids[the_id].values())) or force:
            # Local
            glovar.user_ids.pop(the_id, {})
            save("user_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["score"],
                action="remove",
                action_type="score",
                data=the_id
            )
            result += f"结果：{code('操作成功')}\n"
            send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += (f"结果：{code('未操作')}\n"
                       f"原因：{code('用户未获得评分')}\n")
    except Exception as e:
        logger.warning(f"Remove score error: {e}", exc_info=True)

    return result


def remove_watch_user(client: Client, the_id: int, debug: bool = False, aid: int = None, reason: str = None,
                      force: bool = False) -> str:
    # Remove watched user
    result = ""
    try:
        action_text = "移除用户追踪状态"
        result += (f"执行操作：{code(action_text)}\n"
                   f"用户 ID：{code(the_id)}\n")
        if glovar.watch_ids["ban"].get(the_id, 0) or glovar.watch_ids["delete"].get(the_id, 0) or force:
            # Local
            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)
            save("watch_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["watch"],
                action="remove",
                action_type="watch",
                data={
                    "id": the_id,
                    "type": "all"
                }
            )
            result += f"结果：{code('操作成功')}\n"
            if debug:
                send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += (f"结果：{code('未操作')}\n"
                       f"原因：{code('用户不在追踪名单中')}\n")
    except Exception as e:
        logger.warning(f"Remove watch user error: {e}", exc_info=True)

    return result
