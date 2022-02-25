FROM python:3.6.8
MAINTAINER liang.chen

# 拷贝源
COPY docker/sources.list /etc/apt/sources.list
RUN cat /etc/apt/sources.list

# 安装oracle客户端
WORKDIR /opt/oracle
RUN apt-get update -y && apt-get install -y vim libaio1 logrotate syslog-ng \
    poppler-utils poppler-data xfonts-utils fontconfig && \
    ldconfig && \
    # 清理
    apt-get clean && apt-get autoclean && rm -rf /var/lib/apt/lists/*

COPY docker/syslog-ng-extra.conf /etc/syslog-ng/conf.d/syslog-ng-extra.conf
ADD docker/instantclient_21_1.tgz /opt/oracle/
RUN echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

# 安装字体
COPY docker/fonts/* /usr/share/fonts/
RUN mkfontscale && mkfontdir && fc-cache -fv
# 升级pip
RUN pip install --upgrade pip
# 安装python访问oracle的包cx_Oracle
RUN pip install cx_Oracle -i  https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/
# 安装supervisor
RUN pip3 install supervisor
# 拷贝配置文件
COPY docker/supervisord.conf /etc/supervisor/

# 默认的环境变量
ENV ORACLE_HOME=/opt/oracle/instantclient_21_1
ENV PATH=$ORACLE_HOME:$PATH
ENV TNS_ADMIN=$ORACLE_HOME/network/admin
ENV LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
ENV NLS_LANG='SIMPLIFIED CHINESE_CHINA.UTF8'
ENV LANG C.UTF-8
ENV TZ=Asia/Shanghai
# celery worker root运行
ENV C_FORCE_ROOT=true

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN chmod 777 -R $ORACLE_HOME
RUN mkdir $ORACLE_HOME/network/log
COPY docker/sqlnet.ora $ORACLE_HOME/network/admin/

# 安装自定义依赖[CI会将dist目录移动到docker目录下]
COPY docker/dist /tmp/library
# 安装自定义库
RUN pip3 install /tmp/library/* && rm -rf /tmp/library
