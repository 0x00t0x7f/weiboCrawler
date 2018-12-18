# -*- coding:utf-8 -*-

import os
import yaml
import re
import random
import pymysql

from config.user_agent import pools as user_agent

__all__ = ["conf", "compiled_re", "global_config"]
sys_sep = os.sep
project_home = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class conf(object):

	@classmethod
	def normal_config(cls, path):
		return yaml.load(open(path, "rt", encoding='utf-8'))

	@classmethod
	def normal(cls, name):
		config_file = os.path.join(project_home, "config", name)
		if os.path.exists(config_file):
			cls_variable = cls.normal_config(config_file)
			return cls_variable
		return ''


def compiled_re(express, flag=0):
	return re.compile(express, flags=flag)


def proxy_scheme(ip_port):
	if ip_port and len(ip_port) == 2:
		ip, port = ip_port
		ip_port = "{ip}:{port}".format(ip=ip, port=port)
		return {"https": "https://"+ip_port, "http": "http://"+ip_port}
	return dict()


def get_random_headers(**kwargs):
	headers = dict()
	headers["user-agent"] = random.choice(user_agent)
	if kwargs.get("host"):
		headers["host"] = kwargs["host"] or ''
	if kwargs.get("referer"):
		headers["referer"] = kwargs["referer"] or ''
	if kwargs.get("cookie"):
		headers['cookie'] = kwargs['cookie'] or ''
	return headers


global_config = conf.normal("normal.yaml")


def rinse_data(datas):
	if datas and isinstance(datas, list):
		if isinstance(datas[0], (list, tuple, dict)):
			return [item for item in datas if item]
	return datas


def secure_insert_db(datas, sql, mysql):
	try:
		mysql.execute_batch(sql, datas)
	except (pymysql.err.IntegrityError, pymysql.err.ProgrammingError) as ex:
		for item in datas:
			temp_sql = sql + " (%s)" %(",".join(["%s" for i in range(len(item))]))
			try:
				mysql.execute(temp_sql, item)
			except Exception as err:
				print("入库错误: %s - %s" %(err, item))


def image_downloader(path, imageStream, imageName):
	if not (os.path.exists(path) and os.path.isdir(path)):
		os.makedirs(path)
	download_path = os.path.join(path, imageName)
	with open(download_path, "wb") as image:
		image.write(imageStream)









