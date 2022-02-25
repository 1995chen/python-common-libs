# -*- coding: UTF-8 -*-


import os
import re
import tarfile
import time
import datetime
from logging.handlers import BaseRotatingHandler


class TemplateTimedRotatingFileHandler(BaseRotatingHandler):
    def __init__(self, filename, backup_count=0, encoding=None, delay=False, utc=False):
        self.utc = utc
        self.suffix = "%Y-%m-%d"
        self.baseFilename = os.path.abspath(filename)
        self.currentFileName = self._compute_fn()
        self.backup_count = backup_count
        self.ext_match = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
        super(BaseRotatingHandler, self).__init__(filename, 'a', encoding, delay)

    def shouldRollover(self, _record):
        if self.currentFileName != self._compute_fn():
            return True
        return False

    def _compute_fn(self):
        if self.utc:
            t = time.gmtime()
        else:
            t = time.localtime()
        return self.baseFilename + "." + time.strftime(self.suffix, t)

    def get_files_to_backup(self):
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        result = []
        prefix = base_name + "."
        plen = len(prefix)
        for fileName in file_names:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                if self.ext_match.match(suffix):
                    result.append(os.path.join(dir_name, fileName))
        if len(result) < self.backup_count:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backup_count]
        return result

    def clean_log_zip(self):
        """
        清理3个月前的日志
        :return:
        """
        # 获得3个月以前的时间
        clean_date = datetime.datetime.strptime(
            datetime.datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d') - datetime.timedelta(days=60)
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        for fileName in file_names:
            if fileName.endswith('.gz'):
                _result = re.match(r'.*log.(.*)_.*', fileName)
                if _result is None:
                    continue
                _zip_date = datetime.datetime.strptime(_result.group(1).strip(), '%Y-%m-%d')
                if clean_date > _zip_date:
                    os.remove(os.path.join(dir_name, fileName))

    def doRollover(self):
        # 清理日志压缩包
        self.clean_log_zip()
        if self.stream:
            self.stream.close()
            self.stream = None

        self.currentFileName = self._compute_fn()

        if self.backup_count > 0:
            files_to_backup = self.get_files_to_backup()

            if len(files_to_backup) >= self.backup_count:
                file_dir_name = os.path.dirname(files_to_backup[0])
                filename = os.path.basename(self.baseFilename)

                tar_file_name = (
                        filename + '.' +
                        files_to_backup[0].split('.')[-1] +
                        '_' +
                        files_to_backup[self.backup_count - 1].split('.')[-1] +
                        '.tar.gz'
                )

                tar_file_path = os.path.join(file_dir_name, tar_file_name)

                with tarfile.open(tar_file_path, 'w') as tar:
                    for log_file in files_to_backup[0:self.backup_count]:
                        tar.add(log_file, arcname=os.path.basename(log_file))

                for log_file in files_to_backup[0:self.backup_count]:
                    os.remove(log_file)

    def _open(self):
        stream = open(self.currentFileName, self.mode, encoding=self.encoding)

        if os.path.exists(self.baseFilename):
            try:
                os.remove(self.baseFilename)
            except OSError:
                pass
        try:
            os.symlink(os.path.basename(self.currentFileName), self.baseFilename)
        except OSError:
            pass
        return stream
