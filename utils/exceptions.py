# -*- coding:utf-8 -*-


class ParseError(Exception):
	def __init__(self, code_msg):
		self._code = code_msg[0] or 9999
		self._msg = code_msg[1] or ''

	def __repr__(self):
		return "{}, {}".format(self._code, self._msg)
