# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/8/14 13:15
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : path.py
# @Software: PyCharm
from pathlib import Path

LOCAL = Path() / "教务工具"
SCORE_PATH = LOCAL / "score"
CONFIG_PATH = Path() / 'config.yml'
ACCOUNT_PATH = LOCAL / 'account.yml'
OUTPUT_PATH = LOCAL / 'output'
IMG_OUTPUT_PATH = LOCAL / 'img_output'
