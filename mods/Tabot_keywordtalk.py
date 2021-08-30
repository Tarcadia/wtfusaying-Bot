
import CONSTS;
import exs.tabot_msgproc as tmsgp;
import exs.tabot_totalk as ttalk;

import re;
import time;
import random;
import functools;
import logging;

VERSION = 'v20210826';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;35m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot Keyword Talk Loaded');

# 一个模块组件需要的定义实现：
# 为一个单独的module的py，放在./mods/下以供调用，在调用时应当实现如下的接口
# _mod_help_doc     : str,          // 形如_sys_help_doc，为模块组件的help内容
# _mod_cbs          : list,         // 形如_sys_cbs，为模块组件要注册的callback列表
# _botcontrol       : botcontrol    // 系统由此参数附回系统的botcontrol接口
# start()                           // 模块的合法启动，返回自己的线程列表，虽然没用，但是这是要求
# save()                            // 模块的保存操作
# stop()                            // 模块的合法结束

_botcontrol = None;
_mod_cbs = [];
_mod_help_doc = """
# Tabot Keyword Talk：Tabot组件，用于处理各类朴素整活消息
""";



# 回调接口
_tabot_cb_flt_kwt_talk_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': '.*'}]}}};
_tabot_cb_flt_kwt_talk_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'text': '.*'}}};
def _tabot_cb_fnc_kwt_talk(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _txt = tmsgp.msgtxt(mmk, msg);
    _talkcmds = ttalk.talkcmd(_txt);
    for _t in _talkcmds:
        _msg = tmsgp.tomsgtxt(_src, _t);
        _botcontrol.send(mmk, _msg);
        ttalk.oncalltalk(_src);
    if not _talkcmds:
        _talks = ttalk.talk(_txt);
        _t = random.choice(_talks);
        if ttalk.cantalk(_src):
            _msg = tmsgp.tomsgtxt(_src, _txt);
            _botcontrol.send(mmk, _msg);
            ttalk.ontalk(_src);
    return;

# 注册
_mod_cbs.append({'fnc': _tabot_cb_fnc_kwt_talk, 'flt': _tabot_cb_flt_kwt_talk_qq, 'key': '_tabot_kwt_cb_talks_qq'});
_mod_cbs.append({'fnc': _tabot_cb_fnc_kwt_talk, 'flt': _tabot_cb_flt_kwt_talk_tg, 'key': '_tabot_kwt_cb_talks_tg'});



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Keyword Talk Stopped');
    return;

