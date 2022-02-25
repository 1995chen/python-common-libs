# -*- coding: UTF-8 -*-


import threading
import gettext

import inject

# 默认语言
DEFAULT_LANG = "zh_CN"


class TemplateBabel:

    def __init__(self, domain: str, location: str):
        self.domain = domain
        self.location = location
        # thread local 存储语言
        self.registry = threading.local()

    def set_lang(self, lang: str) -> None:
        """
        设置语言
        :param lang:
        :return:
        """
        if lang:
            self.registry.lang = lang

    def get_lang(self) -> str:
        """
        获得语言
        :return:
        """
        return getattr(self.registry, "lang", DEFAULT_LANG)

    def clear(self) -> None:
        """
        请求结束后可以调用改方法进行清理
        :return:
        """
        if hasattr(self.registry, 'lang'):
            del self.registry.lang


def get_text(v: str) -> str:
    # 获得配置
    translate_cfg = inject.instance(TemplateBabel)

    # 获得语言
    lang = translate_cfg.get_lang()
    # 默认中文
    t = gettext.translation(translate_cfg.domain, translate_cfg.location, languages=[lang, DEFAULT_LANG])
    return t.gettext(v)


class LazyString:
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return get_text(self.text)


def get_lazy_text(v: str) -> LazyString:
    return LazyString(v)
