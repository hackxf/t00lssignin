#!/usr/bin/python
# -*- coding: utf8 -*-

import json
import os
import sys
import time
import requests


def output(args, time_f="%Y%m%d%H%M%S"):
    current_time = time.strftime(time_f, time.localtime())
    current_text = '[{}] <-> {}'.format(current_time, str(args))
    with open(LOG_OUTPUT, "a+") as f:
        f.write('{}\n'.format(current_text))
    print(current_text)


def record():
    with open(LOG_SUCCESS, "a+") as f:
        f.write('{}\n'.format(SUCCESS_MARK))


def check_success(file_name, mark_string):
    if os.path.isfile(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, "r") as f_open:
            if mark_string in f_open.read().strip():
                return True
    return False


def login_and_get_form_hash(req_session, user_info, retry_times=3):
    output("[*] login_and_get_form_hash -> retry_times={}".format(retry_times))

    form_hash = None
    try:
        login_url = 'https://www.t00ls.com/login.json'
        req_login_resp = req_session.post(login_url, data=user_info, timeout=GB_TIME_OUT)
        output("[+] login_and_get_form_hash -> resp_text {}".format(req_login_resp.text))

        # 响应是Json格式,转为字典获取其中的 form hash
        req_login_json = json.loads(req_login_resp.text)

        if req_login_json["status"] != "success":
            print("[-] Login failed. Please check login info")
        else:
            form_hash = req_login_json["formhash"]
            output("[+] Successful Get form_hash: {}".format(form_hash))
    except Exception as e:
        output("[-] Get form hash error in [{}]".format(str(e)))
        if retry_times > 0:
            time.sleep(1)
            output("[*] Get form hash Error !!! Try again ...")
            form_hash = login_and_get_form_hash(retry_times - 1)
        else:
            output("[-] Get form hash MAX Error !!!")
    return form_hash


def sign_in_t00ls(req_session, form_hash, retry_times=3):
    output("[*] sign_in_t00ls -> retry_times={}".format(retry_times))

    resp_text = None
    try:
        SIGNIN_URL = 'https://www.t00ls.com/ajax-sign.json'
        req_data = {'formhash': form_hash, 'signsubmit': 'true'}
        resp_sign = req_session.post(url=SIGNIN_URL, data=req_data, timeout=GB_TIME_OUT)
        output("[+] sign_in_t00ls -> resp_text {}".format(resp_sign.text))
        resp_sign_json = json.loads(resp_sign.text)

        if resp_sign_json["status"] == "success":
            record()
            output("[+] Signin T00ls Status is [Success]")
        elif resp_sign_json["message"] == "alreadysign":
            record()
            output("[+] Signin T00ls Status is [Already]")
        else:
            output("[-] Signin T00ls Status is [Failure] with [{}]".format(resp_sign_json))
    except Exception as error:
        output("[-] Signin T00ls Error [{}]".format(str(error)))
        if retry_times > 0:
            time.sleep(1)
            output("[-] Signin T00ls Error !!! Try again ...")
            resp_text = sign_in_t00ls(req_session, form_hash, retry_times - 3)
        else:
            output("[-] Signin T00ls Error !!! Stop Max !!!")
    return resp_text


def login_and_signin(user_info):
    req_session = requests.session()

    # login and get form_hash
    form_hash = login_and_get_form_hash(req_session, user_info)

    # SignIn
    if form_hash:
        sign_in_t00ls(req_session, form_hash)
    else:
        output("[+] Failure Get form_hash: {}".format(form_hash))


if __name__ == '__main__':
    # Gets the Real path where the Script Resides
    CUR_PATH = os.path.split(os.path.realpath(sys.argv[0]))[0]
    CUR_TIME = time.strftime("%Y%m%d", time.localtime())

    # LOG FILE
    LOG_OUTPUT = os.path.join(CUR_PATH, "log.output.txt".format(CUR_TIME))
    LOG_SUCCESS = os.path.join(CUR_PATH, "log.success.txt".format(CUR_TIME))

    # Requests
    GB_TIME_OUT = 20

    # 安全提问参考
    # 0 = 没有安全提问
    # 1 = 母亲的名字
    # 2 = 爷爷的名字
    # 3 = 父亲出生的城市
    # 4 = 您其中一位老师的名字
    # 5 = 您个人计算机的型号
    # 6 = 您最喜欢的餐馆名称
    # 7 = 驾驶执照的最后四位数字

    # 用户信息 列表
    USER_INFO_LIST = [
        {
            'action': 'login',
            'username': '1124920146',
            'password': 'd151e4182a24f98ab864f3832949180e',
            'password_hash': True,
            'questionid': 5,
            'answer': '联想'
        },
    ]

    for t00ls_user_info in USER_INFO_LIST:
        output("*" * 100)
        curr_user = t00ls_user_info['username']
        output("[+] Username: [{}]".format(curr_user))

        # AUTO Login And Signin
        SUCCESS_MARK = "[{}] [{}] SignIn SUCCESS".format(CUR_TIME, curr_user)
        if not check_success(LOG_SUCCESS, SUCCESS_MARK):
            # Login and signin
            login_and_signin(t00ls_user_info)
        else:
            # no need Login and signin
            output("[+] SIGNIN [{}] SUCCESS IN RECORD:{}".format(curr_user, LOG_SUCCESS))

            # When the file is too large, empty the file
            if os.stat(LOG_SUCCESS).st_size > 1 * 1024 * 1024:
                log_success_bak = "{}.{}.bak".format(LOG_SUCCESS, CUR_TIME)
                os.rename(LOG_SUCCESS, log_success_bak)
                output("[*] The success log file is too large. Rename the file {} to {}".format(LOG_SUCCESS, log_success_bak))

            if os.stat(LOG_OUTPUT).st_size > 5 * 1024 * 1024:
                log_output_bak = "{}.{}.bak".format(LOG_OUTPUT, CUR_TIME)
                os.rename(LOG_OUTPUT, log_output_bak)
                output("[*] The output log file is too large. Rename the file {} to {}".format(LOG_OUTPUT, log_output_bak))
        output("*" * 100)
