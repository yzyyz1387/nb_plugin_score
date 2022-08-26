# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/8/14 13:17
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : utils.py
# @Software: PyCharm
import logging
import os
import sys
from typing import Optional

import aiofiles
import yaml
from nonebot import logger, get_driver
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, MessageSegment, PrivateMessageEvent
from playwright.async_api import async_playwright, Browser

from .path import *


def log():
    """
    日志
    :return:
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s-%(levelname)s: %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.formatter = formatter
    console_handler.setLevel(logging.INFO)
    logfile = 'nwafu.log'
    File_handler = logging.FileHandler(logfile, mode='a', encoding='utf-8')
    File_handler.setFormatter(formatter)
    File_handler.setLevel(logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(File_handler)
        logger.addHandler(console_handler)
        print(logger.handlers)
    return logger


async def async_w(file, content) -> None:
    """
    异步写入文件
    :param file: 文件
    :param content: 内容
    :return:
    """
    async with aiofiles.open(file, 'w', encoding='utf-8') as f:
        await f.write(content)
        await f.close()


async def async_r(file):
    """
    异步读取文件
    :param file: 文件
    :return: 内容
    """
    async with aiofiles.open(file, 'r', encoding='utf-8') as f:
        content = await f.read()
        await f.close()
        return content


async def init(**kwargs) -> Optional[Browser]:
    global _browser
    try:
        browser = await async_playwright().start()
        _browser = await browser.chromium.launch(**kwargs)
        return _browser
    except NotImplementedError:
        logger.warning("win环境下 初始化playwright失败，相关功能将被限制....")
    except Exception as e:
        logger.warning(f"启动chromium发生错误 {type(e)}：{e}")
        try:
            if _browser:
                await _browser.close()
        except NameError:
            logger.info("正在安装浏览器...")
            os.system("playwright install chromium")
    return None


async def cue_user(event: Event, qq: Optional[int]) -> MessageSegment:
    """
    根据不同事件返回不同的用户提醒方式
    :param event:
    :param qq:
    :return:
    """
    if isinstance(event, GroupMessageEvent):
        return MessageSegment.at(qq)
    elif isinstance(event, PrivateMessageEvent):
        return MessageSegment.text(f"To {qq}：")


async def plugin_init():
    """
    初始化插件
    :return:
    """
    Path.mkdir(LOCAL) if not Path.exists(LOCAL) else ...
    Path.mkdir(IMG_OUTPUT_PATH) if not Path.exists(IMG_OUTPUT_PATH) else ...
    Path.mkdir(OUTPUT_PATH) if not Path.exists(OUTPUT_PATH) else ...
    yaml.dump({1796000000: {"account": '2019010000', "password": 123456}},
              open(ACCOUNT_PATH, "w", encoding="utf-8")) if not Path.exists(ACCOUNT_PATH) else ...
    logger.success("西农教务插件初始化检测完成")

