import os
import json

import nonebot
import yaml
import httpx
import asyncio

from .utils_net import get_main_cookies
from .path import *
from .utils import *
from functools import wraps
from nonebot import logger
from prettytable import PrettyTable
from .login_check.login_check import login_check
from typing import Optional, Dict, List, Tuple, Any, Union
from playwright._impl._api_types import TimeoutError


@time_log
async def run(account: str, password: str, dm=None) -> Optional[List]:
    """
    获取所有成绩、总分情况、当前学期
    :param account: 账号
    :param password: 密码
    :param dm: 学期代码
    :return: 当前学期查询结果
    """
    logger.info("开始运行，将在1min内完成...")

    main_list = await get_main_cookies(account, password)
    if main_list:
        name = main_list[0]
        page = main_list[2]
        page1 = main_list[3]
        context = main_list[4]
        browser = main_list[5]
        main_cookies = main_list[1]
        _WEU = main_cookies["_WEU"]
        MOD_AUTH_CAS = main_cookies["MOD_AUTH_CAS"]
        students_score = SCORE_PATH / f'{account}.json'
        students_score_total = SCORE_PATH / f'{account}_total.json'
        at_present = LOCAL / 'present.json'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': '',
        }
        data = {
            'querySetting': '[{"name":"SFYX","caption":"是否有效","linkOpt":"AND","builderList":"cbl_m_List",'
                            '"builder":"m_value_equal","value":"1","value_display":"是"},{"name":"SHOWMAXCJ",'
                            '"caption":"显示最高成绩","linkOpt":"AND","builderList":"cbl_String","builder":"equal","value":0,'
                            '"value_display":"否"}]',
            '*order': '-XNXQDM,-KCH,-KXH',
            'pageSize': 100,
            'pageNumber': 1
        }

        if _WEU and MOD_AUTH_CAS:
            headers['Cookie'] = '_WEU=' + _WEU + '; MOD_AUTH_CAS=' + MOD_AUTH_CAS + ';'
            async with httpx.AsyncClient() as client:
                logger.debug(f"正将成绩储存到 {students_score} ")
                score = (await client.post('https://newehall.nwafu.edu.cn/jwapp/sys/cjcx/modules/cjcx/xscjcx.do',
                                           headers=headers, data=data)).read().decode('utf-8')
                Path.mkdir(LOCAL) if not Path.exists(LOCAL) else ...
                Path.mkdir(SCORE_PATH) if not Path.exists(SCORE_PATH) else ...
                # logger.info(f"正在储存{account}的成绩到") if Path.exists(SCORE_PATH) else Path.mkdir(SCORE_PATH)
                await async_w(students_score, score)
                logger.success(f"{account} 的成绩储存完成")
                logger.info("正在查询当前学期")
                semester = json.loads(
                    (await client.post('https://newehall.nwafu.edu.cn/jwapp/sys/cjcx/modules/cjcx/cxdqxnxq.do',
                                       headers=headers)).read().decode('utf-8')
                )
                await async_w(at_present, json.dumps(semester))
                logger.debug(f"当前学期查询结果{semester}")
                logger.info(f'当前学期为{semester["datas"]["cxdqxnxq"]["rows"][0]["MC"]}')
                if dm:
                    semester_DM = dm
                else:
                    semester_DM = semester["datas"]["cxdqxnxq"]["rows"][0]["DM"]
            logger.info(f"获取{account}的总体成绩...")
            await page1.goto('https://newehall.nwafu.edu.cn/jwapp/sys/cjcx/modules/cjcx/cxxscjpm.do')
            await page1.wait_for_url("https://newehall.nwafu.edu.cn/jwapp/sys/cjcx/modules/cjcx/cxxscjpm.do")
            selector = await page1.query_selector('//html/body/pre')
            total_score = (await selector.inner_text())
            logger.success(f"获取完成，正在储存{account}的总体成绩")
            logger.debug(f"获取到的总体成绩：{total_score}")
            await async_w(students_score_total, total_score)
            logger.info(f"{account} 的总体成绩储存完成")
            await context.close()
            await browser.close()
            return [name, semester_DM, json.loads(total_score), json.loads(score)]
    else:
        return None


async def data_processor(account: str, password: str, dm: str = None) -> Optional[List[Any]]:
    try:
        if dm:
            student_data = await run(account, password, dm)
        else:
            student_data = await run(account, password)
    except TimeoutError:
        return [None, 0]
    if not student_data:
        logger.warning("登陆失败")
        return [None, 1]
    else:
        name, semester_DM, total_score, score = student_data[0], student_data[1], student_data[2], student_data[3]
        row = score["datas"]["xscjcx"]["rows"]
        if row:
            row_total = total_score["datas"]["cxxscjpm"]["rows"][0]
            last_semester_DM = row[0]["XNXQDM"]
            output_score = []
            juan_score = []  # 卷
            for juan in row_total:
                juan_score.append(str(row_total[juan]))
            if not dm:
                if last_semester_DM != semester_DM:
                    logger.info("查询的学期还没有成绩，将查询最上学期的成绩")
                    semester_DM = last_semester_DM
                elif last_semester_DM == semester_DM:
                    logger.info(f"查询{semester_DM}学期的成绩")
                    pass
            else:
                semester_DM = dm
            for details in row:
                if details["XNXQDM"] == semester_DM:
                    detail: list = [details["XSKCM"],  # 课程名
                                    details["ZCJ"],  # 成绩
                                    details["PSCJ"],  # 平时成绩
                                    details["QMCJ"],  # 期末成绩
                                    details["KCXZDM_DISPLAY"],  # 课程性质
                                    details["XF"],  # 学分
                                    details["XFJD"]]  # 学分绩点
                    for i_ in range(len(detail)):
                        detail[i_] = str(detail[i_])

                    output_score.append(detail)
                    # logger.info(f"{}")
            juan_score.pop(3)
            tb = PrettyTable()
            tb2 = PrettyTable()
            logger.success(name)
            tb.field_names = ["专业排名", "GPA", "学分成绩", "班级排名"]
            tb.add_row(juan_score)
            tb2.field_names = ["课程", "成绩", "平时成绩", "期末成绩", "课程性质", "学分", "学分绩点"]
            tb2.add_rows(output_score)
            logger.success('\n' + str(tb))
            # print("")
            logger.success('\n' + str(tb2))
            return [output_score, juan_score]
        else:
            return []


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for i in data:
            loop.run_until_complete(data_processor(str(i), data[i]))
