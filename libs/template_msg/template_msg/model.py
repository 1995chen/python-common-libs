# -*- coding: UTF-8 -*-


from typing import Optional, List
from dataclasses import dataclass

from .enum import IMessageType


@dataclass
class IResult:
    """
    结果
    """
    success: bool = False
    msg: str = ''


@dataclass
class ILarkMsgSender:
    """
    发送者，可以是用户或应用
    """
    # 发送者的id
    id: Optional[str] = None
    # 发送者的id类型
    id_type: Optional[str] = None
    # 发送者的类型
    sender_type: Optional[str] = None
    # 为租户在飞书上的唯一标识，用来换取对应的tenant_access_token，也可以用作租户在应用里面的唯一标识
    tenant_key: Optional[str] = None


@dataclass
class ILarkMsgBody:
    """
    消息内容
    """
    # 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型 包括：text、
    # post、image、file、audio、media、sticker、interactive、share_chat、share_user等
    content: Optional[str] = None


@dataclass
class ILarkMsgMention:
    """
    被@的用户或机器人的信息
    """
    # 被@的用户或机器人的序号。例如，第3个被@到的成员，值为“@_user_3”
    key: Optional[str] = None
    # 被@的用户或者机器人的open_id
    id: Optional[str] = None
    # 被@的用户或机器人 id 类型，目前仅支持 open_id
    id_type: Optional[str] = None
    # 被@的用户或机器人的姓名
    name: Optional[str] = None
    # 为租户在飞书上的唯一标识，用来换取对应的tenant_access_token，也可以用作租户在应用里面的唯一标识
    tenant_key: Optional[str] = None


@dataclass
class ILarkMsgData:
    """
    飞书消息发送
    """
    # 消息id
    message_id: Optional[str] = None
    # 根消息id
    root_id: Optional[str] = None
    # 父消息的id
    parent_id: Optional[str] = None
    # 消息类型 包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
    msg_type: Optional[IMessageType] = None
    # 消息生成的时间戳（毫秒）
    create_time: Optional[str] = None
    # 消息更新的时间戳（毫秒）
    update_time: Optional[str] = None
    # 消息是否被撤回
    deleted: Optional[bool] = None
    # 消息是否被更新
    updated: Optional[bool] = None
    # 所属的群
    chat_id: Optional[str] = None
    # 消息发送者
    sender: Optional[ILarkMsgSender] = None
    # 消息内容
    body: Optional[ILarkMsgBody] = None
    # 被@的用户或机器人的id列表
    mentions: Optional[List[ILarkMsgMention]] = None
    # 合并转发消息中，上一层级的消息id message_id
    upper_message_id: Optional[str] = None


@dataclass
class ILarkMsgResult(IResult):
    """
    飞书消息发送
    """
    code: Optional[int] = None
    data: Optional[ILarkMsgData] = None
