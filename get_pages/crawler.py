import time
import random
import urllib.parse as Purl
import requests
import traceback
from bs4 import BeautifulSoup
from itertools import count

from utils.dbtools import MySQLEcho
from utils.random_proxy import RandomProxy
from utils.base import (get_random_headers, global_config, rinse_data,
                        secure_insert_db, proxy_scheme, image_downloader, project_home, sys_sep)
from logger.logger import netio, parser
from discovery.search_person import parse_normal_fm_view, parse_result_ret_json

PROXY_SERVER = RandomProxy()


def get_request_result(url, headers=None, **kwargs):
	"""
	__ref	/1087030002_2975_2003_0
	ajaxpagelet	1
	page	2
	pids	Pl_Core_F4RightUserList__4
	"""
	try:
		if headers and isinstance(headers, dict):
			h_params = {"cookie": headers.get("cookie"), "host": headers.get("host"), "referer": headers.get("referer")}
		else:
			h_params = dict()
		headers = get_random_headers(**h_params)

		if global_config["IS_SURE_USE_PROXY"]:
			if global_config["GLOBAL_PROXY"]:
				proxy = global_config["GLOBAL_PROXY"]
			else:
				ip_port = PROXY_SERVER.get_random_proxy("Elite")
				proxy = proxy_scheme(ip_port)
				global_config["GLOBAL_PROXY"] = proxy
			netio.info("当前代理: %s" % (proxy))
			resp = requests.get(url, headers=headers, params=kwargs, proxies=proxy, timeout=10)
		else:
			resp = requests.get(url, headers=headers, params=kwargs, timeout=10)

		netio.info(resp.url)
		if resp.status_code == 200:
			return resp.text
		else:
			raise Exception("响应错误 错误代码: %s" % (resp.status_code))
	except Exception as ex:
		netio.error(ex)
		raise


def parse_user_info_by_soup(container, from_url):
	if container and isinstance(container, dict):
		html = container.get("html")
		soup = BeautifulSoup(html, 'lxml')
		user_info = soup.find_all("dd", class_="mod_info S_line1")
		ret_user_list = []
		for item in user_info:
			user_nav_info = item.find("a", usercard=True)
			user_href = user_nav_info["href"]
			user_name = user_nav_info["title"]
			user_id_temp = user_nav_info["usercard"].split("&")
			user_id_temp = [ids for ids in user_id_temp if ids.startswith("id=")]
			user_id = user_id_temp[0][3:] if user_id_temp else ''
			user_info_mess = item.get_text()
			user_info_list = [item for item in user_info_mess.split("\n") if item.strip()]
			personal_info = {}
			for index, value in enumerate(user_info_list):
				if value.startswith(u"关注"):
					personal_info["follows"] = value[2:]
				elif value.startswith(u"粉丝"):
					personal_info["fans"] = value[2:]
				elif value.startswith(u"微博"):
					personal_info["weibo_count"] = value[2:]
				elif value.startswith(u"地址"):
					personal_info["address"] = value[2:]
				elif value.startswith(u"简介"):
					personal_info["brief"] = value[2:]
				elif value.startswith(u"标签"):
					personal_info["label"] = value[3:]
			else:
				personal_info["user_id"] = user_id
				personal_info["homepage"] = user_href
				personal_info["user_name"] = user_name
				personal_info["referer"] = from_url
				ret_user_list.append(personal_info)
		return ret_user_list
	return list()


def parse_user_blog_by_soup(container, user_id=None, is_parse_image=False):
	if container and isinstance(container, dict):
		html = container.get("html")
		if not html:
			return list()
		soup = BeautifulSoup(html, "lxml")
		blog_block_list = soup.find_all("div", attrs={"class": "WB_feed_detail clearfix", "node-type": "feed_content"})
		blog_comment_list = []
		for blog in blog_block_list:
			try:
				temp_user_id = blog.find("div", class_="WB_info").a["usercard"] or user_id
				for item in temp_user_id.split("&"):
					if item:
						key, value = item.split("=")
						if key == "id":
							user_id = value
							break
					else:
						pass
				post_date_client = blog.find("div", class_="WB_from S_txt2")
				post_date = post_date_client.a["date"] or post_date_client.a["title"]
				post_from_client = post_date_client.find("a", class_="S_txt2", title=False, date=False)
				if post_from_client:
					post_from_client = post_from_client.get_text() or None
				else:
					post_from_client = None
				post_comment = blog.find("div", class_="WB_text W_f14",
				                         attrs={"node-type": "feed_list_content"}).get_text()
				post_comment = post_comment.strip()

				if is_parse_image:
					try:
						mediaArea = blog.find("div", class_="WB_media_wrap clearfix",
						                      attrs={"node-type": "feed_list_media_prev"})
						ulArea = mediaArea.find("ul")
						action_data = ulArea["action-data"]
						if action_data:
							for item in action_data.split("&"):
								k, v = item.split("=")
								if k == "clear_picSrc":
									for imageUrl in v.split(","):
										request_url = "https:{url}".format(url=Purl.unquote(imageUrl))
										imageName = request_url.rsplit("/")[-1]
										download_path = sys_sep.join([project_home, "download", str(user_id), "images"])
										imageResp = requests.get(request_url)
										image_downloader(download_path, imageResp.content, imageName)
									else:
										netio.info("user id: %s images(%s) download done!" % (user_id, imageName))
									break
					except:
						parser.error(traceback.format_exc())
				else:
					# 不启动图片下载器
					pass
			except:
				parser.error(traceback.format_exc())
				continue
			else:
				temp_blog_info = {
					"user_id": user_id,
					"post_time": post_date,
					"from_client": post_from_client,
					"weibo_comment": post_comment
				}
				blog_comment_list.append(temp_blog_info)
		else:
			return blog_comment_list
	else:
		return list()


def get_class_user_info():
	mysql = MySQLEcho.get_conn()
	discovery = mysql.select("select * from weibo_discovery_person")

	single_class_user_count = 100

	cookie = global_config["COOKIE"]
	host = "d.weibo.com"
	referer = ""
	params = {
		"__ref": "",
		"ajaxpagelet": "1",
		"page": 1,
		"pids": "Pl_Core_F4RightUserList__4",
		"_t": ""
	}

	for _class in discovery:
		current_url = _class["url"]
		try:
			go_url = current_url.rsplit("/")[-1][:-1]
		except:
			parser.error(traceback.format_exc())
			continue
		else:
			request_url = "https://d.weibo.com/{go_url}".format(go_url=go_url)
			params["__ref"] = go_url
			flag_class_count = 0
			totals_page_user_parsed_list = []
			for page in count(1):
				if flag_class_count >= single_class_user_count:
					break
				params["page"] = page
				params["_t"] = "FM_%d" % (int(time.time() * 1000))
				referer = request_url + "?page={page}".format(page=page)
				retry_request_times = 20
				user_list_page = ""
				while retry_request_times:
					try:
						user_list_page = get_request_result(request_url, headers={"cookie": cookie, "host": host,
						                                                          "referer": referer}, **params)
						netio.info("请求成功，当前页: %d, URL: %s" % (page, request_url))
					except:
						retry_request_times -= 1
						netio.info("响应错误, 重试次数: %d, 请求url: %s" % (retry_request_times, request_url))
						if global_config["IS_SURE_USE_PROXY"]:
							ip_port = PROXY_SERVER.get_random_proxy("Elite")
							proxy = proxy_scheme(ip_port)
							global_config["GLOBAL_PROXY"] = proxy
					else:
						break

				if not user_list_page:
					netio.info("请求成功，但没有数据")
					break

				user_info_list_page = parse_normal_fm_view(user_list_page)
				for script in user_info_list_page:
					multi_user_list = parse_user_info_by_soup(script, from_url=current_url)
					parser.info(str(multi_user_list))
					if not multi_user_list: break

					for index, item in enumerate(multi_user_list):
						try:
							user_id = item["user_id"]
							user_name = item["user_name"]
							follows = item.get("follows")
							fans = item.get("fans")
							weibo_count = item.get("weibo_count")
							address = item.get("address")
							brief = item.get("brief")
							label = item.get("label")
							homepage = item['homepage']
							referer = item.get("referer")
							multi_user_list[index] = [user_id, user_name, follows, fans, weibo_count, address, brief,
							                          label, homepage, referer]
						except:
							multi_user_list[index] = []
							parser.error("键错误: %s" % (item))

					totals_page_user_parsed_list.extend(multi_user_list)

				if not user_info_list_page or not len(multi_user_list):
					break
				flag_class_count += len(multi_user_list)

			totals_page_user_parsed_list = rinse_data(totals_page_user_parsed_list)
			total_page_user_list = totals_page_user_parsed_list[:single_class_user_count]
			netio.info("[%s] 分类下 一共获取到 %d 条用户数据，准备入库.." % (_class["classify"], len(totals_page_user_parsed_list)))
			sql = "insert into weibo_user values"
			secure_insert_db(total_page_user_list, sql, mysql)
	else:
		print("task finished!")
		mysql.close()


def crawler_every_blog_by_homeUrl(homeUrl, sql, mysql, user_id=None):
	"""
	crawler all popular blogs on each weibo specific user's homepage.
	"""
	single_user_blog_count = 1000
	single_user_totals_blog = []

	cookie = global_config["COOKIE_BLOG"]
	host = "weibo.com"
	referer = homeUrl
	headers = {"cookie": cookie, "host": host}
	__ref = "&".join(["is_search=0", "visible=2", "is_hot=3", "is_tag=4", "profile_ftype=1", "page={page}#feedtop"])
	params = {
		"__ref": __ref,
		"ajaxpagelet": "1",
		"ajaxpagelet_v6": "1",
		"is_hot": "1",  # 3
		"is_search": "0",  # 1
		"is_tag": "0",  # 4
		"page": 1,  # 6
		"pids": "Pl_Official_MyProfileFeed__20",  # Pl_Official_MyProfileFeed__20
		"_t": "",
		"profile_ftype": "1",  # 5
		"visible": "0",  # 2
		"is_all": "1"
	}

	request_url = homeUrl.split("?")[0]

	# user global variables
	page_id = ""
	domain = ""
	domain_op = ""
	pids = ""

	for page in count(1):
		body_params = params
		if page > 1:
			headers["referer"] = referer + __ref[:-8]
			body_params["__ref"] = body_params["__ref"].format(page=page - 1)
			body_params["pids"] = pids
		else:
			body_params = {"is_hot": 1}
		body_params["page"] = page
		body_params["_t"] = "FM_%d" % (int(time.time() * 1000))

		retry_request_times = 100
		user_blog_page = ""
		while retry_request_times:
			try:
				user_blog_page = get_request_result(request_url, headers=headers, **body_params)
			except:
				retry_request_times -= 1
				netio.info("响应错误, 重试次数: %d, 请求url: %s" % (retry_request_times, request_url))
				if global_config["IS_SURE_USE_PROXY"]:
					ip_port = PROXY_SERVER.get_random_proxy("Elite")
					proxy = proxy_scheme(ip_port)
					global_config["GLOBAL_PROXY"] = proxy
			else:
				break

		if not user_blog_page:
			netio.info("请求成功，但没有数据")
			break

		# 如果启动热加载机制 那么必须解析 head 中的 config 内容 得到 page_id, domain
		if global_config["HOT_LOAD"] and page == 1:
			try:
				if user_blog_page:
					user_base_info = BeautifulSoup(user_blog_page, "lxml")
					for base in user_base_info.head.contents[-4].get_text().split("\n"):
						if base.strip():
							k, v = base.split("=")
							if "page_id" in k:
								page_id = v.strip()[1:-2]
							elif "domain" in k:
								domain = v.strip()[1:-2]
								domain_op = domain
			except:
				parser.error(traceback.format_exc())

		single_page_blog_list = parse_normal_fm_view(user_blog_page)

		# single_page_blog_list 可能包含了两个 homeFeed 节点
		single_page_blog_list = [item for item in single_page_blog_list
		                         if item.get("ns") == "pl.content.homeFeed.index" and
		                         item.get("domid", "").startswith("Pl_Official_MyProfileFeed")]
		pids = single_page_blog_list[0]["domid"]

		if global_config["HOT_LOAD"]:
			if domain and page_id and single_page_blog_list:
				for hot_load_page in range(2):
					base_uri = "https://weibo.com/p/aj/v6/mblog/mbloglist"
					base_params = {
						"domain": domain,
						"is_all": 1,
						"pagebar": hot_load_page,
						"pl_name": pids,
						"id": page_id,
						"script_uri": homeUrl,
						"feed_type": 0,
						"pre_page": page,
						"domain_op": domain_op,
						"__rnd": int(time.time() * 1000),
						"page": page
					}
					netio.info("base uri: %s, params: %s" % (base_uri, base_params))
					base_response = get_request_result(base_uri, headers, **base_params)
					base_data = parse_result_ret_json(base_response, key="data")
					single_page_blog_list.append({"html": base_data})

		for script in single_page_blog_list:
			blog_page_list = parse_user_blog_by_soup(script, user_id)
			single_user_totals_blog.extend(blog_page_list)

			# 入库
			if blog_page_list:
				patch_datas = [[g["user_id"], g["post_time"], g["weibo_comment"], g["from_client"]] for g in blog_page_list]
				parser.info(patch_datas)
				secure_insert_db(patch_datas, sql, mysql)
			else:
				break
		if (len(single_user_totals_blog) > single_user_blog_count or
				not single_page_blog_list or
				not blog_page_list):
			break


# return single_user_totals_blog


def traverse_homeUrl():
	mysql = MySQLEcho.get_conn()
	sql = "insert into weibo_post (user_id, post_time, weibo_comment, from_client) values"
	select_sql = "select user_id, homepage from weibo.weibo_user"
	discovery = mysql.select(
		select_sql,
		dict_ret=False)
	for user_id, url in discovery:
		request_url = "https:" + url if url.startswith("//") else url
		crawler_every_blog_by_homeUrl(request_url, sql, mysql, user_id)
		time.sleep(random.randint(3, 6))
	else:
		mysql.close()


# 获取用户信息
# get_class_user_info()

# 获取用户博客信息
# traverse_homeUrl()
