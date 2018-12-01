# coding=utf-8
from __future__ import absolute_import
import os
import sys
import six
import yaml
import random
import time
import traceback
import threading
import itertools
import requests
import itertools
from functools import wraps
from bs4 import BeautifulSoup
try:  import pymysql
except ImportError: pass
if six.PY2:  import Queue as queue
elif six.PY3: import queue
# from multiprocessing import Pool, cpu_count

from utils import *
from random_proxy import RandomProxy, ProxyServerError

MAX_SIZE = 1000
MAX_TIMEOUT = 600
q = queue.Queue(MAX_SIZE)
TOTAL_NUMS = 0  # 评论条数

############### 重要配置 ################
SYNC_WAIT_LOCK = configPools.SYNC_WAIT_LOCK  # 同步两个线程之间的状态-有一方退出则另一方也退出-此标志不可改动
IS_SURE_USE_PROXY = configPools.IS_SURE_USE_PROXY
PROXY_TIMEOUT_TIMER = configPools.PROXY_TIMEOUT_TIMER  # 判断代理是否请求超时
HOT_LOAD = configPools.HOT_LOAD
#######################################

# IP_FORBID = False  # IP是否被禁
PROXY_SERVER = RandomProxy()
STABLE_PROXY = None

user_agent = ["Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
              "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0",
              "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
              "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0",
              "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.21 (KHTML, like Gecko) Mwendo/1.1.5 Safari/537.21"]

cookies = "your cookie"

def get_proxy_request(url):
	proxies = {"http": None, "https": None}
	headers = {"user-agent": random.choice(user_agent),
	"host": "weibo.com",
	"referer": "https://weibo.com/1496852380/GCcaiqqZ8?filter=hot&root_comment_id=0&type=comment",
	"cookie": cookies}

	global STABLE_PROXY
	try:
		if not STABLE_PROXY and IS_SURE_USE_PROXY:
			proxy_ip = PROXY_SERVER.get_random_proxy(proxy_type="Elite")
			STABLE_PROXY = proxy_ip
			print("随机代理访问 -> %s" % (str(proxy_ip)))
		else:
			proxy_ip = STABLE_PROXY
		if proxy_ip and len(proxy_ip) == 2:
			if proxy_ip[0] and proxy_ip[1]:
				ip_port = ":".join(proxy_ip)
				proxies["http"], proxies["https"] = "http://" + ip_port, "https://" + ip_port
		response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
	except ProxyServerError as ex:
		STABLE_PROXY = None
		sleep = random.randint(2, 5)
		print("代理服务挂掉! %s 休息一会重试 (%s).." % (ex, sleep))
		time.sleep(sleep)
	except requests.exceptions.ProxyError as ex:
		STABLE_PROXY = None
		print("%s => %s" % ("无效的代理 (400)", ex))
		raise
	except Exception as ex:
		print("=> %s" %(ex))
		STABLE_PROXY = None
	else:
		return response


def get_comment_from_url(url):
	global STABLE_PROXY, PROXY_TIMEOUT_TIMER, IS_SURE_USE_PROXY
	try:
		response = get_proxy_request(url)
		if response.status_code == 200:
			if PROXY_TIMEOUT_TIMER:  PROXY_TIMEOUT_TIMER = None
			datas = response.json()
			if datas["code"] == "100000":
				print("URL: %s" % (url))
				html = datas["data"]["html"]
				try:
					comment_list = parse_html_to_content(html)
					writer_queue(comment_list)
				except:
					raise ValueError("解析失败 %s skip.." % (traceback.format_exc()))
				else:
					totalpage = datas["data"]["page"]["totalpage"]
					return len(comment_list), totalpage
			else:
				raise IOError("错误的响应码: %s cause: %s" % (datas["code"], datas["msg"]))
		elif response.status_code == 414:
			STABLE_PROXY = None
			print(requests.ConnectionError("请求失败 (414: IP被禁)-切换: %s" % (url)))
			IS_SURE_USE_PROXY = not IS_SURE_USE_PROXY
			PROXY_TIMEOUT_TIMER = time.time()
		elif response.status_code == 400:
			print(requests.ConnectionError("无效的代理 (400): %s" %(url)))
			STABLE_PROXY = None

			# 判断无效的代理是否超过5min, 微博5min内会解禁被封的IP-可以切回原来的IP
			swith_proxy()

	except AttributeError as ex:
		pass
	except requests.exceptions.ProxyError:
		swith_proxy()
	except BaseException as ex:
		pass


def swith_proxy():
	global STABLE_PROXY, PROXY_TIMEOUT_TIMER, IS_SURE_USE_PROXY
	# 判断无效的代理是否超过5min, 微博5min内会解禁被封的IP-可以切回原来的IP
	if PROXY_TIMEOUT_TIMER and time.time() - PROXY_TIMEOUT_TIMER > 5 * 60:
		IS_SURE_USE_PROXY = not IS_SURE_USE_PROXY
		PROXY_TIMEOUT_TIMER = None
		print("无效的代理——请求超时（>5min）尝试切回原IP..")


def writer_queue(comment_list):
	for item in comment_list:
		if item and isinstance(item, dict):
			q.put(item)


readerQ = lambda: q.get()


def parse_html_to_content(soup):
	try:
		ret_list = []
		sup = BeautifulSoup(soup, 'lxml')
		comment_list = sup.find_all("div", class_="list_li S_line1 clearfix")
		for comment in comment_list:
			single_comment = {}
			single_comment["comment_id"] = comment["comment_id"]
			items = comment.find("div", class_="list_con")
			single_details = items.find("div", class_="WB_text")

			single_comment["homepage"] = single_details.a["href"]

			_every = single_details.get_text().strip().split("：")
			if _every and len(_every) == 2:
				single_comment["nickname"] = _every[0]
				single_comment["comment"] = _every[1]
				single_comment["homepage"] = single_details.a["href"]
			# 获取时间
			single_timestamp = items.find("div", class_="WB_from S_txt2").get_text()
			single_comment["comment_time"] = single_timestamp.strip()
			ret_list.append(single_comment)
		else:
			return ret_list
	except:
		# print("解析失败 %s skip.." %(traceback.format_exc()))
		raise


def start_request():
	global TOTAL_NUMS, SYNC_WAIT_LOCK
	for current_page in itertools.count(2990):  # 46600 ~ 50970 | 56700 (入库失败居多) 63900
		if SYNC_WAIT_LOCK:
			current_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&id=4291032306300262&root_comment_max_id=714012517687086" \
			"&root_comment_max_id_type=0&root_comment_ext_param=&page={0}&filter=hot&sum_comment_number=17349" \
			"&filter_tips_before=1&from=singleWeiBo&__rnd={1}".format(
				current_page, int(time.time() * 1000))
			if not (current_page % 50):
				time.sleep(random.randint(2, 5))
			is_comment = None
			while not is_comment:
				if HOT_LOAD:
					current_url_data = hot_load(current_url)
					while not current_url_data:
						current_url_data = hot_load(current_url)
					current_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&from=singleWeiBo&" + current_url_data +"&__rnd={}".format(int(time.time() * 1000))
				is_comment = get_comment_from_url(current_url)
			if current_page >= is_comment[1] and not is_comment[0]:
				print("TASK DONE! 一共爬取记录 %s页\t%s条." % (current_page, TOTAL_NUMS))
				SYNC_WAIT_LOCK = False
				break
			else:
				TOTAL_NUMS += is_comment[0]
		else:
			break
	else:
		SYNC_WAIT_LOCK = False


def hot_load(fake_url):
	global STABLE_PROXY, PROXY_TIMEOUT_TIMER, IS_SURE_USE_PROXY
	try:
		response = get_proxy_request(fake_url)
		if response.status_code == 200:
			if PROXY_TIMEOUT_TIMER:  PROXY_TIMEOUT_TIMER = None
			datas = response.json()
			if datas["code"] == "100000":
				html = datas["data"]["html"]
				try:
					soup = BeautifulSoup(html, "lxml")
				except:
					raise ValueError("解析失败 %s skip.." % (traceback.format_exc()))
				else:
					return soup.find("a", {"action-type": "click_more_comment"})["action-data"]
			else:
				raise IOError("错误的响应码: %s cause: %s" % (datas["code"], datas["msg"]))
		elif response.status_code == 414:
			STABLE_PROXY = None
			print(requests.ConnectionError("请求失败 (414: IP被禁)-切换: %s" % (fake_url)))
			IS_SURE_USE_PROXY = not IS_SURE_USE_PROXY
			PROXY_TIMEOUT_TIMER = time.time()
		elif response.status_code == 400:
			print(requests.ConnectionError("无效的代理 (400): %s" %(fake_url)))
			STABLE_PROXY = None

			# 判断无效的代理是否超过5min, 微博5min内会解禁被封的IP-可以切回原来的IP
			swith_proxy()

	except AttributeError as ex:
		pass
	except requests.exceptions.ProxyError:
		swith_proxy()
	except BaseException as ex:
		pass


def reader():
	from .dbtools import MySQLEcho
	insert_list = []
	mysql = MySQLEcho.get_conn()
	global SYNC_WAIT_LOCK
	have_comment = True
	while have_comment and SYNC_WAIT_LOCK:
		try:
			insert_list.append(q.get(timeout=MAX_TIMEOUT))
			if len(insert_list) > 50:
				# insert db
				sql = """INSERT INTO cuiyongyuan_dahongzha (comment_id, homepage, nickname, comment, comment_time) VALUES """
				insert_list = rinse_data(insert_list)
				if insert_list:
					mysql.execute_batch(sql, insert_list)
					insert_list = []
		except queue.Empty as ex:
			have_comment = False
		except (pymysql.err.IntegrityError, pymysql.err.ProgrammingError) as ex:
			primary_error_handle(insert_list, mysql)
			insert_list = []
		except:
			print(insert_list)
			print("其他错误 %s" % (traceback.format_exc()))
	else:
		try:
			sql = """INSERT INTO cuiyongyuan_dahongzha (comment_id, homepage, nickname, comment, comment_time) VALUES """
			insert_list = rinse_data(insert_list)
			if insert_list:
				mysql.execute_batch(sql, insert_list)
		except:
			primary_error_handle(insert_list, mysql)
	mysql.close()
	# os._exit(0)
	SYNC_WAIT_LOCK = False


def data_home(is_save_db=False):
	"""
	@is_save_db: save to database if true else output screen.
	"""
	if not is_save_db:
		pprint = six.print_
		global SYNC_WAIT_LOCK
		have_comment = True
		while have_comment and SYNC_WAIT_LOCK:
			try:
				single_comment = q.get(timeout=MAX_TIMEOUT)
				pprint(single_comment)
			except queue.Empty:
				have_comment = False
			except Exception as err:
				pprint(ex)
		SYNC_WAIT_LOCK = False
	else:
		reader()	

			
def primary_error_handle(insert_list, mysql):
	sql = "INSERT INTO cuiyongyuan_dahongzha (comment_id, homepage, nickname, comment, comment_time) VALUES (%s, %s, %s, %s, %s)"
	for item in insert_list:
		params = None
		try:
			mysql.execute(sql, item)
		except pymysql.err.IntegrityError as ex:
			print("主键冲突 skip.. %s" % (str(item)))
		except pymysql.err.ProgrammingError as ex:
			if isinstance(item, dict) and item.get("comment_id") and item.get("comment"):
				params = (item["comment_id"], item.get("homepage", "-"), item.get('nickname', '-'), item['comment'],
				item.get("comment_time", "-"))
				mysql.execute(sql, params)
		except Exception as ex:
			if params:
				print("入库错误: %s 错误参数: %s" % (ex, str(params)))
			else:
				print("入库失败: %s Caused by %s" % (ex, str(item)))


def rinse_data(datas):
	if datas:
		for index, d in enumerate(datas):
			try:
				if isinstance(d, tuple):
					pass
				elif isinstance(d, dict):
					if d.get("comment_id") and d.get("comment"):
						datas[index] = (d["comment_id"], d.get("homepage", "-"), d.get('nickname', '-'), d['comment'],
						d.get("comment_time", "-"))
			except Exception as ex:
				print("清洗数据错误 %s" % (ex))
		else:
			return datas
	else:
		return []


def timer(msg=None):
	def wrapper(func):
		@wraps(func)
		def inner(*args, **kwargs):
			start = time.time()
			results = func(*args, **kwargs)
			print("%s COST: %s's" %(msg, time.time() - start))
			return results
		return inner
	return wrapper


@timer("入库完毕!")
def launch_weibo_spider():
	funcs = [start_request, data_home]
	loops = len(funcs)

	threads = []
	for thread in range(loops):
		threads.append(threading.Thread(target=funcs[thread]))

	for launch in threads:
		launch.start()

	for launch in threads:
		launch.join()


if __name__ == "__main__":
	# pools = Pool(cpu_count())
	# for page in range(1, 5):
	# 	url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&id=3424883176420210&page={}".format(page)
	# 	print("当前页: %s" %(url))
	# 	try:
	# 		pools.apply_async(get_comment_from_url, args=(url,))
	# 	except BaseException as ex:
	# 		print(traceback.format_exc())
	# pools.close()
	# pools.join()

	# for i in range(1, 3):
	# 	url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&id=3424883176420210&page={}".format(i)
	# 	get_comment_from_url(url)
	# else:
	# 	print(q.qsize())
	launch_weibo_spider()

