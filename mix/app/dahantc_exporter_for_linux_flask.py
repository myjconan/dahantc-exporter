#!/usr/local/bin/python
import os
import sys
import pandas as pd
import prometheus_client
from prometheus_client import Gauge
from prometheus_client.core import CollectorRegistry
import time
import datetime
import threading
import logging
import configparser
import dmPython
import pymysql
from functools import wraps
from flask import Flask, redirect, url_for, make_response
from gevent import pywsgi
import subprocess

app = Flask(__name__)


def shell_etl(app_type,shell_name,log_file,since_seconds):
    current_time = datetime.datetime.now()
    last_time = current_time - datetime.timedelta(
        seconds=int(since_seconds))
    current_time_head=current_time.strftime("%Y-%m-%d")
    current_time_tail = current_time.strftime("%H:%M:%S")
    last_time_head = last_time.strftime("%Y-%m-%d")
    last_time_tail = last_time.strftime("%H:%M:%S")

    raw_shell_5gucp = {
                '获取时间区间日志': "cat {log_file} | awk '/{last_time_head}T{last_time_tail}/,/{current_time_head}T{current_time_tail}/'".format(log_file=log_file,last_time_head=last_time_head,last_time_tail=last_time_tail,current_time_head=current_time_head,current_time_tail=current_time_tail),
                '获取链路异常日志': '60',
                '一级调研员': '70',
                '二级调研员': '75',
                '三级调研员': '80',
                '四级调研员': '85',
                '一级主任科员': '90',
                '二级主任科员': '95',
                '三级主任科员': 'A0',
                '四级主任科员': 'A5',
                '一级科员': '110',
                '二级科员': '115',
                '其他': 'Z0'
            }


def set_server_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Server'] = 'DAHANTC_EXPORTER1.0'
        return response
    return decorated_function

def count_time(print_str=None):
    def outwrapper(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func(*args, **kwargs)
            spent_time = round(time.time() - start_time, 4)
            logger.info('{print_str} 共耗时{spent_time}秒'.format(print_str=print_str, spent_time=spent_time))

        return wrapper

    return outwrapper


# @app.before_request
# def set_server_header():
#     WSGIRequestHandler.server_version = 'DAHANTC_EXPORTER1.0'
#     WSGIRequestHandler.sys_version = ''


@app.route("/", methods=['GET'])
@set_server_headers
def InfoHandler():
    content = '<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>EMA_5GUCP Exporter--For Linux</title><style>body {font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,Noto Sans,Liberation Sans,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol,Noto Color Emoji;margin: 0;}header {background-color: #e6522c;color: #fff;font-size: 1rem;padding: 1rem;}main {padding: 1rem;}label {display: inline-block;width: 0.5em;}</style></head><body><header><h1>DAHANTC Exporter--For Linux</h1></header><main><h2>Prometheus DAHANTC Exporter--For Linux</h2><div>Version: (version=1.0.2, author=MaYinJian, inspired_by=Mr.Liao)</div><div><ul><li><a href="/metrics">Metrics</a></li></ul></div></main></body></html>'
    return content


@app.route("/\w*", methods=['GET'])
@set_server_headers
def ReMetricsHandler():
    return redirect(url_for('/metrics'))


@app.route("/metrics", methods=['GET'])
@set_server_headers
def MetricsHandler():
    resp = make_response(prometheus_client.generate_latest(prometheus_metrics_registry))
    resp.headers['Content-Type'] = 'text/plain; charset=UTF-8'
    return resp


class Dahantc_Exporter_Config(object):
    def __init__(self, dahantc_exporter_config_file, database_config_file,app_log_config_file):
        self.dahantc_exporter_config_file = dahantc_exporter_config_file
        self.database_config_file = database_config_file
        self.app_log_config_file=app_log_config_file
        # 采集配置
        self.update_config_interval_secend = int(60)
        self.loginfo_scrape_interval_secend = int(60)
        self.loginfo_alert_statistics_duration_minute = int(5)
        self.appinfo_scrape_interval_secend = int(60)
        self.appinfo_alert_statistics_duration_minute = int(5)
        # 数据库配置
        self.database = []
        # linux应用日志配置
        self.app_log_file=[]

    @count_time(print_str='更新Dahantc_Exporter配置成功！')
    def read_dahantc_exporter_config(self):
        rootDir = os.path.dirname(os.path.realpath(sys.argv[0]))
        configFilePath = os.path.join(rootDir, self.dahantc_exporter_config_file)
        config = configparser.ConfigParser()
        config.read(configFilePath, encoding="utf-8-sig")
        default_paras = [attr for attr in dir(self) if
                         not callable(getattr(self, attr)) and not attr.startswith("__")]
        sections = config.sections()
        for section in sections:
            options = config.options(section)
            for option in options:
                if option in default_paras:
                    self.__setattr__(option, config.get(section=section, option=option))
        config_list = ''
        for option in default_paras:
            config_list += ('\n%s=%s' % (option, self.__getattribute__(option)))
        return config_list

    @count_time(print_str='更新数据库配置成功！')
    def read_database_config(self):
        database_list = []
        some_data_ins = Database_For_Query()
        database_params = [attr for attr in dir(some_data_ins) if
                           not callable(getattr(some_data_ins, attr)) and not attr.startswith("__")]
        rootDir = os.path.dirname(os.path.realpath(sys.argv[0]))
        configFilePath = os.path.join(rootDir, self.database_config_file)
        config = configparser.ConfigParser()
        config.read(configFilePath, encoding="utf-8-sig")
        sections = config.sections()
        for section in sections:
            temp_database = Database_For_Query()
            temp_database.db_name = section
            options = config.options(section)
            for option in options:
                if option in database_params:
                    temp_database.__setattr__(option, config.get(section=section, option=option))
            database_list.append(temp_database)
        self.database = database_list
        return database_list


    @count_time(print_str='更新linux应用日志配置成功！')
    def read_app_log_file_config(self):
        app_log_file_list = []
        some_data_ins = App_log()
        app_log_params = [attr for attr in dir(some_data_ins) if
                           not callable(getattr(some_data_ins, attr)) and not attr.startswith("__")]
        rootDir = os.path.dirname(os.path.realpath(sys.argv[0]))
        configFilePath = os.path.join(rootDir, self.app_log_config_file)
        config = configparser.ConfigParser()
        config.read(configFilePath, encoding="utf-8-sig")
        sections = config.sections()
        for section in sections:
            temp_app_log = App_log()
            temp_app_log.app_name = section
            options = config.options(section)
            for option in options:
                if option in app_log_params:
                    temp_app_log.__setattr__(option, config.get(section=section, option=option))
            app_log_file_list.append(temp_app_log)
        self.database = app_log_file_list
        return app_log_file_list

class App_log(object):
    def __init__(self, app_log_file=None,app_name=None):
        self.app_log_file = app_log_file
        self.app_name = app_name


    def get_app_log(self,log_file,since_seconds):
    def get_all_app_log_statistics(self, namespace, since_seconds):
        pods = self.k8s.list_namespaced_pod(namespace=namespace).items
        data_total = pd.DataFrame()
        for pod in pods:
            temp = self.get_pod_log_statistics(namespace=namespace, pod_name=pod.metadata.name,
                                            since_seconds=since_seconds)
            if temp is not None:
                data_total = pd.concat([data_total, temp], axis=0, ignore_index=True)
        # logger.info(data_total)
        return data_total

    def get_app_log_statistics(self, log_file, since_seconds):
        log = ''
        try:
            # lasttime = time.time()
            log = self.get_app_log(log_file=log_file, since_seconds=since_seconds)
            # print('%s:%s' % (pod_name, time.time() - lasttime))
        except:
            logger.error(
                '获取日志失败：pod_name：%s，namespace：%s，since_seconds：%s' % (pod_name, namespace, since_seconds))
        if len(log) != 0 and pod_name.find('dahantc-exporter') == -1:
            log_sep = '#####'
            log_keyword = ['ERROR', 'INFO', 'WARN', 'DEBUG']
            lines = log.split('\n')
            for i in range(len(lines)):
                lines[i] = lines[i].strip()
                lines[i] = lines[i].replace(' - ', log_sep, 1)
                lines[i] = lines[i].replace('[', '', 1)
                lines[i] = lines[i].replace('] ', log_sep, 1)
                for keyword in log_keyword:
                    lines[i] = lines[i].replace(keyword + ' ', keyword + log_sep, 1)
            data_total = pd.DataFrame(lines)
            data_total = data_total[0].str.split(log_sep, expand=True)
            data_total = data_total.map(lambda x: x.strip() if type(x) == str else x)
            data_total.rename(columns={0: 'date', 1: 'level', 2: 'className', 3: 'message'}, inplace=True)
            data_warning = data_total[['className', 'level']].copy()
            data_warning['namespace'] = namespace
            data_warning['podName'] = pod_name
            data_statistics = data_warning.value_counts().to_frame().reset_index()
            data_statistics.rename(columns={0: 'count'}, inplace=True)
            data_statistics.drop(data_statistics[data_statistics['level'] == 'INFO'].index, inplace=True)
            # print('inner df:%s' % data_statistics)
            # logger.info(time.time()-lasttime)
            return data_statistics

    def get_raw_ent(self, table_for_query):
        pass
class Database_For_Query(object):
    def __init__(self, db_name=None, db_type=None, db_host=None, db_port=None, db_username=None, db_password=None,
                 db_schema=None):
        self.db_type = db_type
        self.db_host = db_host
        self.db_port = db_port
        self.db_username = db_username
        self.db_password = db_password
        self.db_schema = db_schema
        self.db_name = db_name

    def get_raw_ent(self, table_for_query):
        table_for_query = table_for_query
        correlation_table = ['ema_channel']
        result = []
        df_raw_ent = pd.DataFrame()
        conn = None
        schema_protect_symbol = None
        if self.db_type == 'dameng':
            conn = dmPython.connect(user=self.db_username, password=self.db_password, server=self.db_host,
                                    port=int(self.db_port))
            schema_protect_symbol = '\"'
            table_for_query = [item.upper() for item in table_for_query]
            self.db_schema = str(self.db_schema).upper()
        elif self.db_type == 'mysql':
            conn = pymysql.connect(user=self.db_username, password=self.db_password, host=self.db_host,
                                   port=int(self.db_port))
            schema_protect_symbol = '`'
            table_for_query = [item.lower() for item in table_for_query]
            self.db_schema = str(self.db_schema).lower()
        elif self.db_type == 'oracle':
            schema_protect_symbol = '\"'
            table_for_query = [item.upper() for item in table_for_query]
            self.db_schema = str(self.db_schema).upper()
        cursor = conn.cursor()
        current_time = datetime.datetime.now()
        last_time = current_time - datetime.timedelta(
            minutes=int(dahantc_exporter_config.appinfo_alert_statistics_duration_minute))
        for table in table_for_query:
            sql = (
                "select a.respcode,a.nstat,a.yystype,b.channelname from {schema_protect_symbol}{db_schema}{schema_protect_symbol}.{table} a inner join {schema_protect_symbol}{db_schema}{schema_protect_symbol}.ema_channel b on a.channelid=b.id where wtime between '{start_time}' and '{end_time}' ".format(
                    schema_protect_symbol=schema_protect_symbol, db_schema=self.db_schema, table=table,
                    start_time=last_time.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time=current_time.strftime("%Y-%m-%d %H:%M:%S")))
            # logger.info('数据库查询语句为：%s' %sql)
            cursor.execute(sql)
            values = cursor.fetchall()
            if len(values) > 0:
                temp_df = pd.DataFrame(values, columns=['respcode', 'nstat', 'yystype', 'channelname'])
                temp_df['table'] = table
                # temp_df['database'] = self.db_schema
                temp_df['database'] = self.db_name
                df_raw_ent = pd.concat([df_raw_ent, temp_df], axis=0, ignore_index=True)
                df_raw_ent = df_raw_ent.reindex(
                    columns=['database', 'table', 'respcode', 'nstat', 'yystype', 'channelname'])
        cursor.close()
        conn.close()
        return df_raw_ent

    def get_ent_info_detail(self):
        table_for_query = ['ema_sms_ent', 'ema_aim_ent', 'ema_rcs_ent']
        df = self.get_raw_ent(table_for_query=table_for_query)
        df_statistics = df.value_counts().to_frame().reset_index()
        if df_statistics.shape[0] > 0:
            df_statistics['database'] = df_statistics['database'].str.lower()
            df_statistics['table'] = df_statistics['table'].str.lower()
        # statistics_list=df_statistics.apply(lambda x: tuple(x), axis=1).values.tolist()
        statistics_dict = df_statistics.to_dict()
        return statistics_dict

    def get_ent_info_total(self):
        table_for_query = ['ema_sms_ent', 'ema_aim_ent', 'ema_rcs_ent']
        df = self.get_raw_ent(table_for_query=table_for_query)
        statistics_param_dict = {'nstat': (0, 'nstat_count'), 'respcode': ('success', 'respcode_count'),
                              'table': (None, 'send_quantity')}
        if df.shape[0] > 0:
            df_statistics = pd.DataFrame(columns=['database', 'table'])
            df['database'] = df['database'].str.lower()
            df['table'] = df['table'].str.lower()
            for param in statistics_param_dict.keys():
                if param == 'table':
                    df_statistics_temp = df[['database', 'table']].value_counts().to_frame().reset_index()
                else:
                    df_statistics_temp = df[['database', 'table', param]].value_counts().to_frame().reset_index()
                    df_statistics_temp.drop(df_statistics_temp[df_statistics_temp[param] != statistics_param_dict[param][0]].index,
                                         inplace=True)
                    df_statistics_temp.drop(param, axis=1, inplace=True)
                df_statistics_temp.rename(columns={'count': statistics_param_dict[param][1]}, inplace=True)
                df_tables = df_statistics_temp['table'].unique()
                for table in table_for_query:
                    if table not in df_tables:
                        temp_df = pd.DataFrame(
                            [{"database": self.db_name.lower(), "table": table, statistics_param_dict[param][1]: 0}])
                        df_statistics_temp = pd.concat([df_statistics_temp, temp_df], axis=0, ignore_index=True)
                df_statistics = pd.merge(df_statistics, df_statistics_temp, how='outer', on=['database', 'table'])
            df_statistics['send_success_rate'] = round(df_statistics['nstat_count'] / df_statistics['send_quantity'], 2) * 100
            df_statistics['respond_success_rate'] = round(df_statistics['respcode_count'] / df_statistics['send_quantity'],
                                                       2) * 100
            df_statistics.fillna(100, inplace=True)
            df_statistics.drop(['nstat_count', 'respcode_count'], axis=1, inplace=True)
            statistics_dict = df_statistics.to_dict()
            return statistics_dict
        else:
            df_statistics = pd.DataFrame()
            for table in table_for_query:
                temp_df = pd.DataFrame([{"database": self.db_name.lower(), "table": table, "send_quantity": 0,
                                         'send_success_rate': 100, 'respond_success_rate': 100}])
                df_statistics = pd.concat([df_statistics, temp_df], axis=0, ignore_index=True)
            statistics_dict = df_statistics.to_dict()
            return statistics_dict


class Prometheus_Metrics(object):
    def __init__(self, metrics_name=None, metrics_documentation=None, metrics_labelnames=None):
        if metrics_name is not None:
            self.metrics = Gauge(name=metrics_name, documentation=metrics_documentation,
                                 labelnames=metrics_labelnames, registry=prometheus_metrics_registry)
            self.name = metrics_name
            self.documentation = metrics_documentation
            self.labelnames = metrics_labelnames
            self.registry = prometheus_metrics_registry

    def update_metrics(self, *args, **kwargs):
        pass


class Linux_Prometheus_Metrics(Prometheus_Metrics):
    @count_time(print_str='更新应用日志统计成功！')
    def update_metrics(self):
        pass
        # data = k8s.get_namespace_log_statistics(namespace=k8s.chosen_namespace,
        #                                      since_seconds=int(
        #                                          dahantc_exporter_config.loginfo_alert_statistics_duration_minute) * 60)
        # # print(data)
        # for i in range(data.shape[0]):
        #     self.metrics.labels(namespace=k8s.chosen_namespace, podName=data['podName'][i],
        #                         className=data['className'][i],
        #                         level=data['level'][i]).set(int(data['count'][i]))


class AppInfo_Detail_Prometheus_Metrics(Prometheus_Metrics):
    @count_time(print_str='更新应用消息发送统计（详细）成功！')
    def update_metrics(self):
        database_list = dahantc_exporter_config.database
        for database in database_list:
            data = database.get_ent_info_detail()
            # print(data)
            data_len = len(data['count'])
            if data_len > 0:
                for i in range(data_len):
                    labelset = {}
                    for label in self.labelnames:
                        labelset[label] = data[label][i]
                    self.metrics.labels(**labelset).set(data['count'][i])


class AppInfo_Total_Prometheus_Metrics(Prometheus_Metrics):
    @count_time(print_str='更新应用消息发送统计（总计）成功！')
    def update_metrics(self):
        database_list = dahantc_exporter_config.database
        index_list = ['send_quantity', 'send_success_rate', 'respond_success_rate']
        for database in database_list:
            data = database.get_ent_info_total()
            # print(data)
            data_len = len(data['database'])
            for i in range(data_len):
                labelset = {}
                for label in data.keys():
                    if label in self.labelnames:
                        labelset[label] = data[label][i]
                for index in index_list:
                    labelset['index'] = index
                    self.metrics.labels(**labelset).set(data[index][i])


def update_mertrics_linux_log():
    logger.info('启动更新linux应用日志线程')
    metrics_labelnames = ['namespace', 'podName', 'className', 'level']
    metrics = Linux_Prometheus_Metrics(metrics_name='dahantc_log_info', metrics_documentation='应用日志统计',
                                     metrics_labelnames=metrics_labelnames)
    while True:
        try:
            metrics.update_metrics()
        except:
            logger.error('更新update_mertrics_linux_log数据失败')
        time.sleep(int(dahantc_exporter_config.loginfo_scrape_interval_secend))


def update_mertrics_database_appInfo_detail():
    logger.info('启动更新应用数据线程')
    metrics_labelnames = ['database', 'table', 'respcode', 'nstat', 'yystype', 'channelname']
    metrics = AppInfo_Detail_Prometheus_Metrics(metrics_name='dahantc_app_info_detail',
                                                metrics_documentation='应用消息发送统计（详细）',
                                                metrics_labelnames=metrics_labelnames)
    while True:
        try:
            metrics.update_metrics()
        except:
            logger.error('更新update_mertrics_database_appInfo_detail数据失败')
        time.sleep(int(dahantc_exporter_config.appinfo_scrape_interval_secend))


def update_mertrics_database_appInfo_total():
    logger.info('启动更新应用数据线程')
    metrics_labelnames = ['database', 'table', 'index']
    metrics = AppInfo_Total_Prometheus_Metrics(metrics_name='dahantc_app_info_total',
                                               metrics_documentation='应用消息发送统计（总计）',
                                               metrics_labelnames=metrics_labelnames)
    while True:
        try:
            metrics.update_metrics()
        except:
            logger.error('更新update_mertrics_database_appInfo_total数据失败')
        time.sleep(int(dahantc_exporter_config.appinfo_scrape_interval_secend))


def update_config():
    logger.info('启动更新dahantc_exporter线程')
    while True:
        try:
            dahantc_exporter_config.read_database_config()
        except:
            logger.error('%s-更新database配置失败' % str(time.strftime("%Y年%m月%d日 %H:%M:%S")))
        time.sleep(1)
        try:
            dahantc_exporter_config.read_dahantc_exporter_config()
        except:
            logger.error('%s-更新Dahantc_Exporter配置失败' % str(time.strftime("%Y年%m月%d日 %H:%M:%S")))
        time.sleep(int(dahantc_exporter_config.update_config_interval_secend))


def init():
    global dahantc_exporter_config
    global prometheus_metrics_registry
    global logger
    # 日志格式
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s:%(message)s')
    logger = logging.getLogger(__name__)
    # 配置文件
    dahantc_exporter_config_file = './dahantc_exporter_config.ini'
    database_config_file = './database_config.ini'
    app_log_config_file='./app_log_config.ini'
    # 读取配置文件
    dahantc_exporter_config = Dahantc_Exporter_Config(dahantc_exporter_config_file=dahantc_exporter_config_file,
                                                      database_config_file=database_config_file,app_log_config_file=app_log_config_file)
    dahantc_exporter_config.read_dahantc_exporter_config()
    dahantc_exporter_config.read_database_config()
    # 注册prometheus_metrics
    prometheus_metrics_registry = CollectorRegistry(auto_describe=False)

    pd.set_option("display.max_column", 30)
    pd.set_option('display.max_rows', None)
    pd.set_option('max_colwidth', 30)


if __name__ == '__main__':
    global logger
    init()

    threads = [
        threading.Thread(target=update_mertrics_linux_log),
        threading.Thread(target=update_mertrics_database_appInfo_detail),
        threading.Thread(target=update_mertrics_database_appInfo_total),
        threading.Thread(target=update_config),
    ]
    for t in threads:
        t.start()

    server = pywsgi.WSGIServer(('0.0.0.0', 80), app)
    server.serve_forever()
    logger.info('dahantc-exporter已启动')
