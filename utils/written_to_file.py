#!/usr/bin/env python
# -*- coding:utf-8 -*-

from datetime import datetime
import datetime as dt
from utils.dbtools import MySQLEcho


def patch_insert(datas, patch_nums=500):
    before_index = 0
    for index, item in enumerate(datas):
        if index and index % patch_nums == 0:
            yield datas[before_index:index]
            before_index = index
    else:
        yield datas[before_index:]


def written_to_file(datas, index):
	filename = "./weibo/weibo_%s.txt" % (index)
	print("writting %s" % (filename))
	f = open(filename, "wt")
	for item in datas:
		item = list(item)
		try:
			datetime.strptime(item[-2], "%Y-%m-%d %H:%M:%S")
		except:

			item[-2] = real_time(str(item[-2]), str(item[-1]))
		description = "昵称：%s  主页：%s  时间：%s<br/>" % (item[2], item[1], item[-2])
		comment = item[3]
		message = description + comment
		f.write(message + "\n")
	f.close()


def save_date_file():
	"""
    分割大文本文件到小文件-还原真实日期（微博中的 20分钟前、40秒前、今天 08:20、11月19日等格式）
    comment_time 和 real_timestamp 比对还原真实评论时间
	"""
	mysql = MySQLEcho.get_conn()
	sql = "select * from user_comment"
	datas = mysql.select(sql, dict_ret=False)
	mysql.close()
	print("查询完毕..准备写入文件..")

	for index, patch in enumerate(patch_insert(datas)):
		written_to_file(patch, index)
	else:
		print("written to file finish!")
  
       
def real_time(item, realt):
    datet = str(item)
    if "月" in datet:
        datet = datet.replace("月", "-")
        datet = datet.replace("日", "")
        datet = str(datetime.now().year) + "-" + datet
    elif "今天" in datet:
        datet = str(datetime.strptime(realt, "%Y-%m-%d %H:%M:%S").date()) + " " + datet.split()[1]
        # datet = datet.replace("今天", str(datetime.now().date()))
    elif "分钟" in datet:
        minutes = int(datet[:datet.index("分钟")])
        datet = str(datetime.strptime(realt, "%Y-%m-%d %H:%M:%S") - dt.timedelta(minutes=minutes))
    elif "秒" in datet:
        second = int(datet[:datet.index("秒")])
        datet = str(datetime.strptime(realt, "%Y-%m-%d %H:%M:%S") - dt.timedelta(seconds=second))
    return datet
    

#__name__ == "__main__" and save_date_file()
