# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/8/15 0:55
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py
# @Software: PyCharm
import re
from os.path import dirname
from typing import Union, List, Any, Optional

from jinja2 import Environment, FileSystemLoader
from nonebot import on_command, logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.typing import T_State

from . import score, utils, path, login_check, elective
from .elective import check_elective
from .path import *
from .score import *

driver = get_driver()
global_config = driver.config


@driver.on_bot_connect
async def _():
    await utils.plugin_init()


score_checker = on_command("查成绩", aliases={"我的成绩", "成绩查询"}, priority=2, block=True)


@score_checker.handle()
async def score_checker_(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    qq = event.user_id
    cue = await cue_user(event, qq)
    user_info = await who_am_i(qq, cue, matcher)
    if user_info:
        account = user_info[0]
        password = user_info[1]
        await score_checker.send(cue + f"正在拉取数据，这可能需要15s以上，请稍后...")
        if args:
            if re.findall(r"\b\d{4}-\d{4}-\d\b", str(args)):
                await score_checker.send(cue + f"正在查询自定义学期{str(args)}的成绩")
                result = await data_processor(account, password, str(args))
            else:
                await score_checker.send(cue + f"自定义学期格式误，正为你查询本学期数据")
                result = await data_processor(account, password)
        else:
            result = await data_processor(account, password)
        logger.info(result)
        if result:
            if result[0]:
                total = result[1]
                score_list = result[0]
                temp_file = str(Path('/template/index.html').resolve())
                await render_and_shoot(temp_file, score_list, OUTPUT_PATH / f"index_{qq}.html",
                                       IMG_OUTPUT_PATH / f"index_{qq}.png")
                msg_text = f"GPA：{total[1]}\n学分成绩：{total[2]}\n班级排名:{total[3]}\n专业排名：{total[0]}\n"
                await score_checker.send(cue + f"\n获取成功，正在尝试将成绩通过私聊发送给你")
                try:
                    await bot.call_api("send_private_msg", user_id=qq, message=msg_text + MessageSegment.image(
                        f"file:///{Path(IMG_OUTPUT_PATH / f'index_{qq}.png').resolve()}"))
                except ActionFailed:
                    await score_checker.finish(f"To  {qq}:\n请先添加机器人为好友捏")
                # await score_checker.finish(msg_text + MessageSegment.image(f"file:///{Path(IMG_OUTPUT_PATH / f'index_{qq}.png').resolve()}"))
            elif result[1] == 1:
                await score_checker.finish(
                    f"To  {qq}:\n你的账号或密码错误，请重新绑定\n命令：换绑2019010000 123456\n账号密码用空格隔开")
            elif result[1] == 0:
                await score_checker.finish(cue + f"\n超时了诶~~~网络貌似不给力...")
            elif not result[0]:
                await score_checker.finish(cue + f"\n没有查询到{args}的成绩哦，可能是官网出了点问题，请自行查看...")
        else:
            logger.error("登陆成功但查询为空，可手动打开官网查询，不出意外也查不到")
            await score_checker.finish("登陆成功但查询为空，可手动打开官网查询，不出意外也查不到")


bind_account = on_command("绑定账号", priority=2, block=True)


@bind_account.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    qq = event.sender.user_id
    if " " in str(args):
        raw = str(args).split(" ")
        account_num = raw[0]
        pass_w = raw[1]
        account_num_ = account_num.replace("F", "")
        account_num_ = account_num_.replace("f", "")
        if account_num.isdigit() or account_num_.isdigit():
            with open(ACCOUNT_PATH, "r", encoding="utf-8") as f:
                accounts = yaml.load(f, Loader=yaml.FullLoader)
            if qq in accounts:
                await bind_account.finish("你已经绑定过账号了，请不要重复绑定")
            else:
                accounts[qq] = {"ACCOUNT_PATH": account_num, "password": pass_w}
                with open(ACCOUNT_PATH, "w", encoding="utf-8") as f:
                    yaml.dump(accounts, f)
                await bind_account.finish("绑定成功")
    else:
        await bind_account.finish("请使用空格分隔你的账号和密码")


bind_change = on_command("换绑", priority=2, block=True)


@bind_change.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    qq = event.sender.user_id
    if " " in str(args):
        raw = str(args).split(" ")
        account_num = raw[0]
        pass_w = raw[1]
        account_num_ = account_num.replace("F", "")
        account_num_ = account_num_.replace("f", "")
        if account_num.isdigit() or account_num_.isdigit():
            with open(ACCOUNT_PATH, "r", encoding="utf-8") as f:
                accounts = yaml.load(f, Loader=yaml.FullLoader)
            if qq in accounts:
                accounts[qq] = {"ACCOUNT_PATH": account_num, "password": pass_w}
                with open(ACCOUNT_PATH, "w", encoding="utf-8") as f:
                    yaml.dump(accounts, f)
                await bind_change.finish("换绑成功")
            else:
                await bind_change.finish("你还没有绑定账号哦，请先绑定")
    else:
        await bind_change.finish("请使用空格分隔你的账号和密码")


check_help = on_command("查分帮助", priority=2, block=True)

ele_checker = on_command("查选修", aliases={"查通识", "我的选修"}, priority=2, block=True)


@ele_checker.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    qq = event.user_id
    cue = await cue_user(event, qq)
    user_info = await who_am_i(qq, cue, matcher)
    await ele_checker.send(cue + "正在查询你的选修课情况...")
    if user_info:
        account = user_info[0]
        password = user_info[1]
        score_list = await check_elective(account, password)
        if score_list:
            temp_file = str(Path('/template/ele.html').resolve())
            await render_and_shoot(temp_file, score_list, OUTPUT_PATH / f"ele_{qq}.html",
                                   IMG_OUTPUT_PATH / f"ele_{qq}.png")
            await ele_checker.finish(cue+":你的选修课情况如下\n"+MessageSegment.image(f"file:///{Path(IMG_OUTPUT_PATH / f'ele_{qq}.png').resolve()}"))


async def who_am_i(qq: int, cue: MessageSegment, matcher: Matcher) -> Optional[list[Any]]:
    with open(ACCOUNT_PATH, "r", encoding="utf-8") as f:
        accounts = yaml.load(f, Loader=yaml.FullLoader)
    try:
        if qq in accounts:
            account_num = accounts[qq]["account"]
            pass_w = accounts[qq]["password"]
            return [account_num, pass_w]
        else:
            await matcher.finish(
                cue + f":\n你还没有绑定账号哦，私聊我进行绑定：\n命令：绑定账号2019010000 123456\n账号密码用空格隔开")
            return None
    except TypeError:
        yaml.dump({1796000000: {"ACCOUNT_PATH": '2019010000', "password": 123456}},
                  open(ACCOUNT_PATH, "w", encoding="utf-8"))
        await score_checker.finish(
            cue + f"\n你还没有绑定账号哦，私聊我进行绑定：\n命令：绑定账号2019010000 123456\n更换绑定：\n换绑201901000 123456\n【账号密码用空格隔开】")
        return None


@check_help.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    help_list = """
绑定：
    绑定账号2019010000 123456
    【请私聊我以免信息泄露】
换绑(私聊)：
    换绑2019010000 123456
    【请私聊以免信息泄露】
查分：
    查成绩
    【总是私聊返回结果】
查指定学期：
    查成绩 2021-2022-1
    【总是私聊返回结果】
    """
    await check_help.finish(help_list)
