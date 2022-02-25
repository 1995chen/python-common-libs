# -*- coding: utf-8 -*-


from enum import Enum


class IReceiveIDType(Enum):
    """
    消息接收ID类型
    """
    OPEN_ID = "open_id"
    USER_ID = "user_id"
    UNION_ID = "union_id"
    EMAIL = "email"
    CHAT_ID = "chat_id"


class IMessageType(Enum):
    """
    消息类型
    """
    # 文本
    TEXT = 'text'
    # 富文本
    POST = 'post'
    # 图片
    IMAGE = 'image'
    # 文件
    FILE = 'file'
    # 语音
    AUDIO = 'audio'
    # 视频
    MEDIA = 'media'
    # 表情包
    STICKER = 'sticker'
    # 消息卡片
    INTERACTIVE = 'interactive'
    # 分享群名片
    SHARE_CHAT = 'share_chat'
    # 分享个人名片
    SHARE_USER = 'share_user'


class ICacheKey(Enum):
    """
    缓存键枚举
    """
    # 飞书应用的tenant_access_token
    TENANT_ACCESS_TOKEN = 'tenant_access_token'
    # 飞书邮箱与open_id的映射表
    EMAIL_OPEN_ID_MAPPING = 'email_open_id_mapping'
