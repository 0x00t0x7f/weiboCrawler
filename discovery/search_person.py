# -*- coding:utf-8 -*-
import json
import traceback
from bs4 import BeautifulSoup

from utils.exceptions import *
from utils.status_code import MsgStatus
from utils.base import compiled_re

from logger.logger import parser


def parse_content_html(html):
	try:
		ret_list = []
		sup = BeautifulSoup(html, 'lxml')
		comment_list = sup.find_all("div", class_="list_li S_line1 clearfix")
		for comment in comment_list:
			single_comment = dict()
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
		raise ParseError(MsgStatus.Parse_Error)


def parse_normal_fm_view(fm_view_script):
	try:
		if fm_view_script:
			sup = BeautifulSoup(fm_view_script, 'lxml')
			scripts = sup.find_all("script", type=False)
			temp_re = compiled_re(r"(?<=FM.view\().+(?=\))")
			valid_scripts = []
			for script in scripts:
				if script:
					search_string = script.string
					temp_script = temp_re.search(search_string)
					if temp_script:
						source_text = temp_script.group()
						valid_scripts.append(source_text)
				else:
					continue

			for index, item in enumerate(valid_scripts):
				valid_scripts[index] = json.loads(item)
			return valid_scripts
	except:
		parser.error(traceback.format_exc())
		raise


def parse_discovery_person(html):
	"""
	解析 发现-更多-找人 分类页面
	:param html: 找人页面HTML
	:type html: string object.
	:return: list of find person type.
	:rtype: list
	"""
	try:
		sup = BeautifulSoup(html, 'lxml')
		scripts = sup.find_all("script", type=False)
		temp_re = compiled_re(r"(?<=FM.view\().+(?=\))")
		valid_scripts = []
		for script in scripts:
			if script:
				search_string = script.string
				temp_script = temp_re.search(search_string)
				if temp_script:
					source_text = temp_script.group()
					valid_scripts.append(source_text)
			else:
				continue

		class_type_compiled = compiled_re("pl.content.textnewlist.index")
		other_class_list = [item for item in valid_scripts if _search_person_list_node(item, class_type_compiled)]
		main_class_list = json.loads(other_class_list[0])
		main_sup = BeautifulSoup(main_class_list.get('html'), 'lxml')
		discovery_list = main_sup.find_all("a", class_="item_link S_txt1")

		if discovery_list:
			ret_list = []
		for item in discovery_list:
			href = item.get('href')
			title_html = item.find("span", attrs={"class": "item_title S_txt1"})
			title = title_html.get_text()
			if href and title:
				ret_list.append((href, title))
		else:
			return ret_list
	except:
		raise ParseError(MsgStatus.Parse_Error)


def _search_person_list_node(node, re_compiled):
	try:
		return re_compiled.search(node)
	except:
		pass


def parse_result_ret_json(result, key=None):
	try:
		if result:
			result = json.loads(result)
			if key:
				return result[key]
	except:
		pass





