# -*- coding:utf -*-
"""
新浪微博评论爬虫-获取代理
written by kuing on 2018/11/14
"""
import re
import random
import requests
from bs4 import BeautifulSoup


class ProxyServerError(Exception):

	def __init__(self, msg=u"获取代理列表失败"):
		super(ProxyServerError, self).__init__(msg)


class RandomProxy(object):
	"""
	获取 www.gatherproxy.com 网站提供的代理
	"""

	def __init__(self):
		self.req = None
		self.pools = set()
		self.proxy_type = ["Elite", "Transparent", "Anonymous"]
		self.re1 = re.compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}")
		self.re2 = re.compile(r"(?<=(PROXY_PORT\":\"))[A-Za-z0-9]+(?=(\"))")
		self.re3 = re.compile(r"(?<=(PROXY_TYPE\":\"))[A-Za-z0-9]+(?=(\"))")

	def request_proxy_server(self, proxy_type=None):
		self.req = requests.get("http://www.gatherproxy.com/zh/proxylist/country/?c=China")
		# self.req = requests.get("http://www.gatherproxy.com/zh/")
		if self.req.status_code == 200:
			sup = BeautifulSoup(self.req.text, "lxml")
			tables = sup.find("table", attrs={"id": "tblproxy"})
			proxy_item = tables.find_all("script")
			for item in proxy_item:
				try:
					item = item.string
					if proxy_type and proxy_type in self.proxy_type:
						if self.re3.search(item).group() == proxy_type:
							ip_port = self.re1.search(item).group(), str(int(self.re2.search(item).group(), 16))
							# ip_port = self.re1.search(item).group(), self.re2.search(item).group()
							self.pools.add(ip_port)
					else:
						ip_port = self.re1.search(item).group(), str(int(self.re2.search(item).group(), 16))
						self.pools.add(ip_port)
				except Exception as ex:
					pass
					# print(traceback.format_exc())
		else:
			raise ProxyServerError

	def get_random_proxy(self, proxy_type=None):
		if self.pools:
			ret_proxy = random.choice(list(self.pools))
			self.pools.remove(ret_proxy)
			return ret_proxy
		else:
			print("代理地址池为空，正在获取请稍等..")
			self.request_proxy_server(proxy_type)
			return self.get_random_proxy()


def unit_test_function():
	test = RandomProxy()
	print(test.get_random_proxy(proxy_type="Elite"))


__name__ == "__main__" and unit_test_function()
