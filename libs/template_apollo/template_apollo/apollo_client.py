# -*- coding: utf-8 -*-


import json
import socket
import logging
import time
from threading import Thread
from typing import Callable, Optional

import requests
from template_exception import HandlerUnCallableException

logger = logging.getLogger(__name__)


class ApolloClient(object):
    def __init__(
            self, app_id, cluster='default', config_server_url='http://localhost:8080',
            timeout=80, ip=None, cycle_time: int = 5,
    ):
        self.config_server_url = config_server_url
        self.appId = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.stopped = False
        self.ip = self.init_ip(ip)

        self._stopping = False
        self._cache = {}
        self._notification_map = {'application': -1}
        self._cycle_time = cycle_time
        # 定义handler
        self.config_changed_handler: Optional[Callable] = None
        self.listener_thread: Optional[Thread] = None
        self.started = False

    def set_config_changed_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler会在配置变更时调用
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_logout_handler")
        self.config_changed_handler = handler

    @staticmethod
    def init_ip(ip: str) -> str:
        if ip:
            return ip
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 53))
            ip = s.getsockname()[0]
            return ip

    # Main method
    def get_value(self, key, default_val=None, namespace='application', auto_fetch_on_cache_miss=False):
        if namespace not in self._notification_map:
            self._notification_map[namespace] = -1
            logger.info("Add namespace '%s' to local notification map", namespace)

        if namespace not in self._cache:
            self._cache[namespace] = {}
            logger.info("Add namespace '%s' to local cache", namespace)
            # This is a new namespace, need to do a blocking fetch to populate the local cache
            self._long_poll()

        if key in self._cache[namespace]:
            return self._cache[namespace][key]
        else:
            if auto_fetch_on_cache_miss:
                return self._cached_http_get(key, default_val, namespace)
            else:
                return default_val

    # Start the long polling loop.
    # create a worker thread to do the loop. Call self.stop() to quit the loop
    def start(self):
        # started防止重复调用。
        if self.started:
            return
        self.started = True
        # 开线程监听配置变更
        self.listener_thread = Thread(target=self._listener)
        self.listener_thread.start()

    def stop(self):
        self._stopping = True
        logger.info("Stopping listener...")

    def _cached_http_get(self, key, default_val, namespace='application'):
        url = '{}/configfiles/json/{}/{}/{}?ip={}'.format(self.config_server_url, self.appId, self.cluster, namespace,
                                                          self.ip)
        r = requests.get(url)
        if r.ok:
            data = r.json()
            self._cache[namespace] = data
            logger.info('Updated local cache for namespace %s', namespace)
        else:
            data = self._cache[namespace]

        if key in data:
            return data[key]
        else:
            return default_val

    def _uncached_http_get(self, namespace='application'):
        url = '{}/configs/{}/{}/{}?ip={}'.format(self.config_server_url, self.appId, self.cluster, namespace, self.ip)
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self._cache[namespace] = data['configurations']
            logger.info('Updated local cache for namespace %s release key %s: %s',
                        namespace, data['releaseKey'],
                        repr(self._cache[namespace]))

    def _signal_handler(self, _signal, _frame):
        logger.info('You pressed Ctrl+C!')
        self._stopping = True

    def _long_poll(self):
        url = '{}/notifications/v2'.format(self.config_server_url)
        notifications = []
        for key in self._notification_map:
            notification_id = self._notification_map[key]
            notifications.append({
                'namespaceName': key,
                'notificationId': notification_id
            })
        # 获取最新的通知id
        latest_notification_id: int = notifications[-1]['notificationId']
        r = requests.get(url=url, params={
            'appId': self.appId,
            'cluster': self.cluster,
            'notifications': json.dumps(notifications, ensure_ascii=False)
        }, timeout=self.timeout)

        logger.debug('Long polling returns %d: url=%s', r.status_code, r.request.url)

        if r.status_code == 304:
            # no change, loop
            logger.debug('No change, loop...')
            return

        if r.status_code == 200:
            data = r.json()
            for entry in data:
                ns = entry['namespaceName']
                nid = entry['notificationId']
                logger.info("%s has changes: notificationId=%d", ns, nid)
                self._uncached_http_get(ns)
                self._notification_map[ns] = nid
                # 调用handler
                if (
                        latest_notification_id != -1 and
                        nid != latest_notification_id and
                        callable(self.config_changed_handler)
                ):
                    logger.info(f"pre call config_changed_handler(pay_load), entry: {entry}")
                    self.config_changed_handler(entry)
        else:
            logger.warning('Sleep...')
            time.sleep(self.timeout)

    def _listener(self):
        logger.info('Entering listener loop...')
        while not self._stopping:
            self._long_poll()
            time.sleep(self._cycle_time)

        logger.info("Listener stopped!")
        self.stopped = True
