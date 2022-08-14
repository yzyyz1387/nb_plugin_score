# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/8/15 0:55
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py
# @Software: PyCharm
import re
from os.path import dirname

from jinja2 import Environment, FileSystemLoader
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State

from . import score, utils, path
from .path import *
from .score import *

Path.mkdir(local) if not Path.exists(local) else ...
Path.mkdir(img_output_path) if not Path.exists(img_output_path) else ...
Path.mkdir(output_path) if not Path.exists(output_path) else ...
yaml.dump({1796000000: {"account": '2019010000', "password": 123456}},
          open(account, "w", encoding="utf-8")) if not Path.exists(account) else ...
score_checker = on_command("查成绩", aliases={"我的成绩", "成绩查询"}, priority=2, block=True)


@score_checker.handle()
async def score_checker_(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    qq = event.sender.user_id
    with open(account, "r", encoding="utf-8") as f:
        accounts = yaml.load(f, Loader=yaml.FullLoader)
    try:
        if qq not in accounts:
            await score_checker.finish(f"To  {qq}:\n你还没有绑定账号哦，私聊我进行绑定：\n命令：绑定账号2019010000 123456\n账号密码用空格隔开")
        else:
            await score_checker.send(f"正在拉取数据，这可能需要15s以上，请稍后..."+MessageSegment.at(qq))
            if args and re.findall(r"\d{4}-\d{4}-\d",str(args)):
                await score_checker.send(f"正在查询自定义学期{str(args)}的成绩"+MessageSegment.at(qq))
                result = await data_processor(accounts[qq]["account"], accounts[qq]["password"], str(args))
            else:
                result = await data_processor(accounts[qq]["account"], accounts[qq]["password"])
            if result[0]:
                total = result[1]
                score_list = result[0]
                env = Environment(loader=FileSystemLoader(str(dirname(__file__))))
                template = env.get_template('/template/index.html')
                html = template.render(score_list=score_list)
                with open(output_path / f"index_{qq}.html", 'w', encoding='utf-8') as f:
                    f.write(html)
                    f.close()
                browser = await init()
                context = await browser.new_context(locale="zh-CN")
                page = await context.new_page()
                temp_out = output_path / f"index_{qq}.html"
                await page.goto(f"file:///{Path(temp_out).resolve()}")
                await page.locator('.mdui-table').screenshot(path = img_output_path / f"index_{qq}.png")
                msg_text = f"GPA：{total[1]}\n学分成绩：{total[2]}\n班级排名:{total[3]}\n专业排名：{total[0]}\n"
                await score_checker.send(f"To  {qq}:\n获取成功，正在尝试将成绩通过私聊发送给你")
                try:
                    await bot.call_api("send_private_msg", user_id=qq, message=msg_text+MessageSegment.image(f"file:///{Path(img_output_path / f'index_{qq}.png').resolve()}"))
                except ActionFailed:
                    await score_checker.finish(f"To  {qq}:\n请先添加机器人为好友捏")
                # await score_checker.finish(msg_text + MessageSegment.image(f"file:///{Path(img_output_path / f'index_{qq}.png').resolve()}"))
            elif result[1] == 1:
                await score_checker.finish(f"To  {qq}:\n你的账号或密码错误，请重新绑定\n命令：换绑2019010000 123456\n账号密码用空格隔开")
            elif result[1] == 0:
                await score_checker.finish(f"To  {qq}:\n超时了诶~~~网络貌似不给力...")
    except TypeError:
        yaml.dump({1796000000: {"account": '2019010000', "password": 123456}},
                  open(account, "w", encoding="utf-8"))
        await score_checker.finish(
            f"To: {qq}:\n你还没有绑定账号哦，私聊我进行绑定：\n命令：绑定账号2019010000 123456\n更换绑定：\n换绑201901000 123456\n【账号密码用空格隔开】")


bind_account = on_command("绑定账号", priority=2, block=True)


@bind_account.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    qq = event.sender.user_id
    if " " in str(args):
        raw = str(args).split(" ")
        account_num = raw[0]
        pass_w = raw[1]
        account_num_ = account_num.replace("F","")
        account_num_ = account_num_.replace("f","")
        if account_num.isdigit() or account_num_.isdigit():
            with open(account, "r", encoding="utf-8") as f:
                accounts = yaml.load(f, Loader=yaml.FullLoader)
            if qq in accounts:
                await bind_account.finish("你已经绑定过账号了，请不要重复绑定")
            else:
                accounts[qq] = {"account":account_num , "password": pass_w}
                with open(account, "w", encoding="utf-8") as f:
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
            with open(account, "r", encoding="utf-8") as f:
                accounts = yaml.load(f, Loader=yaml.FullLoader)
            if qq in accounts:
                accounts[qq] = {"account":account_num , "password": pass_w}
                with open(account, "w", encoding="utf-8") as f:
                    yaml.dump(accounts, f)
                await bind_change.finish("换绑成功")
            else:
                await bind_change.finish("你还没有绑定账号哦，请先绑定")
    else:
        await bind_change.finish("请使用空格分隔你的账号和密码")


check_help = on_command("查分帮助", priority=2, block=True)


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