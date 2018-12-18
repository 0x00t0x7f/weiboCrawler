import os
import re
import json
import pprint
import shutil
import threading
from PIL import Image


# ocr directory.
ocr_basicAccurate = r"F:\gitproject\weiboCrawler\download\5269725317\ocr-basicAccurate"

# ocr translation error directory.
ocr_error_path = r"F:\gitproject\weiboCrawler\download\5269725317\images"

# ocr diff directory.
ocr_diff_main = r"F:\gitproject\weiboCrawler\download\5269725317\ocr-right"


def open_image(ocr_right):
	fp = open(ocr_right, "rb")
	imageStream = Image.open(fp)
	tmp_handle = threading.Thread(target=imageStream.show)
	tmp_handle.daemon = True
	tmp_handle.start()
	return fp, imageStream


def diff_text_and_image():
	for index, imageName in enumerate(os.listdir(ocr_diff_main)[:3]):
		print("正在比对第 %s 张图片（%s）.." %(index, imageName))
		json_file = imageName.replace(".jpg", ".json")
		flag = 1

		try:
			json_text = json.load(open(os.path.join(ocr_basicAccurate, json_file)))
			pprint.pprint(json_text, indent=4)
		except:
			print("在目录（%s）中查找JSON文件(%s)失败.." % (ocr_basicAccurate, json_file))
			flag = 0

		if flag:
			try:
				ocr_right = os.path.join(ocr_diff_main, imageName)
				fp, imageStream = open_image(ocr_right)
				result = input(r"请对比图片和JSON文件内容是否大致相同 [YES|NO|Y|N|](不区分大小写)#")
				if not result:
					result = "y"
				if result.strip().lower() in ["yes", "y", "1", 'True']:
					pass
				else:
					shutil.move(ocr_right, ocr_error_path)
				imageStream.close()
				fp.close()
			except:
				print("在目录（%s）中查找图片(%s)失败.." %(ocr_diff_main, imageName))
		print("-" * 30)


def write_to_txt_file():
	base_txt = r"F:\gitproject\weiboCrawler\download\5269725317\ocr-txt"
	for index, file in enumerate(os.listdir(ocr_basicAccurate)):
		abs_path = os.path.join(ocr_basicAccurate, file)
		data = json.load(open(abs_path))
		if data and data.get("words_result"):
			words = data["words_result"]
			words_list = filter(word_filter, [w.get("words", "") for w in words])
			words_string = "".join(words_list)
			print("第 %s 个文件（%s）正在被处理.." %(index, file))
			txt_name = file.replace(".json", ".txt")
			abs_txt_name = os.path.join(base_txt, txt_name)
			with open(abs_txt_name, "wt", encoding="utf-8") as fp:
				fp.write(words_string)
	else:
		print("task done!")


def word_filter(word):
	strip_list = [
		"应用推荐",
		"@",
		"正在保存屏幕截图",
		"中国移动令",
		"文件（F）编辑",
		"文件(F)编辑",
		"中国联通令",
		"\\+",
		"设置",
		"昨天[0-9]{2}:[0-9]{2}",
		"weibo",
		"旦帮",
		"返回",
		"[0-9]+%",
	]
	for item in strip_list:
		if re.search(item, word):
			return False
	else:
		return True


write_to_txt_file()
