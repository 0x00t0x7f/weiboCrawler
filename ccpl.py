import random
import time
import queue
from bs4 import BeautifulSoup
import requests
from functools import wraps

from proj1.dbtools import MySQLEcho
from proj1.random_proxy import RandomProxy, ProxyServerError

MAX_SIZE = 1000
MAX_TIMEOUT = 600
q = queue.Queue(MAX_SIZE)
TOTAL_NUMS = 0  # 评论条数

SYNC_WAIT_LOCK = True  # 同步两个线程之间的状态-有一方退出则另一方也退出
IS_SURE_USE_PROXY = False

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
	"host": "ccpl.psych.ac.cn",
	"referer": "http://ccpl.psych.ac.cn/suicide/",
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
	except Exception as ex:
		print("=> %s" %(ex))
		STABLE_PROXY = None
	else:
		return response


def request_target():
	"""
	<li>
		<h3>
			<span class="label label-info">【新浪微博】 2013.12.02 14:56<em>，3651074281886710</em>: </br></span>
			<div class="alert alert-info" role="alert">河口，再见，再也不见。</div>
		</h3>
	</li>
	"""
	while True:
		url = "http://ccpl.psych.ac.cn/suicide/update?_="+str(int(time.time() * 1000))
		results = get_proxy_request(url)
		try:
			if results and results.status_code == 200:
				soup = BeautifulSoup(results.text, 'lxml')
				platform_name_and_date = soup.h3.span.get_text()
				comment = soup.h3.find('div', {'class': 'alert alert-info'}).get_text()
				platform_name_and_date = platform_name_and_date.replace('，', '')
				platform_name_and_date = platform_name_and_date.replace('\n', '')
				# platform_name_and_date = platform_name_and_date.replace(':', '')
				if platform_name_and_date and len(platform_name_and_date.split()) == 4:
					platform, postday, posttime, postid = platform_name_and_date.split()
					if postid.endswith(":"):
						postid = postid[:-1]
					comment = comment.strip()
					postdate = " ".join([postday, posttime])
					params = [platform, postdate, postid, comment]
					insert_db(params)
		except Exception as ex:
			print("请求失败: (%s)" %(ex))
			pass
		time.sleep(5)


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


def insert_db(item):
	mysql = None
	try:
		if item and isinstance(item, list):
			sql = "INSERT INTO ccpl (platform, posttime, postid, comment) VALUES (%s, %s, %s, %s)"
			mysql = MySQLEcho.get_conn()
			mysql.execute(sql, item)
			print("入库: %s" %(str(item)))
	except Exception as ex:
		print("入库报错: %s, item:(%s)" %(ex, str(item)))
	finally:
		if mysql:
			mysql.close()


if __name__ == "__main__":
	request_target()
