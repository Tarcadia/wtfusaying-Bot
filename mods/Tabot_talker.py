
import CONSTS;

import time;
import logging;

VERSION = 'v20210823';
CONFIG = './config/autosave.json';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(name)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot Talker Loaded');

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
# TB_Talker：Tabot组件，用于根据语境实现对话
""";

# 实现

def miraitxtmsg(mmk, msg):
    _t = '';
    if msg['type'] == 'FriendMessage':
        _t = 'p';
    elif msg['type'] == 'TempMessage':
        _t = 'p';
    elif msg['type'] == 'GroupMessage':
        _t = 'g';
    _src = {
        'mmk'       : mmk,
        'cid'       : _t + str(msg['sender']['id']),
        'uid'       : msg['sender']['id'],
        'mid'       : msg['messageChain'][0]['id'],
        'time'      : msg['messageChain'][0]['time']
    };
    _txtchain = [
        _t['text'] if _t['type'] == 'Plain' else
        _t['name'] if _t['type'] == 'Face' else ''
        for _t in msg['messageChain']
    ];
    _txt = ' '.join(_txtchain);
    return _src, _txt;

def tgtxtmsg(mmk, msg):
    _t = '';
    if msg['chat']['type'] == 'private':
        _t = 'p';
    elif msg['chat']['type'] == 'group':
        _t = 'g';
    elif msg['chat']['type'] == 'supergroup':
        _t = 'g'
    elif msg['chat']['type'] == 'channel':
        _t = 'c'
    _src = {
        'mmk'       : mmk,
        'cid'       : _t + str(msg['chat']['id']),
        'uid'       : msg['from']['id'],
        'mid'       : msg['message_id'],
        'time'      : msg['date']
    };
    _txt = msg['text'] if 'text' in msg else '';
    return _src, _txt;

def totxtmsg(mmk, txt):
    msg = {};
    return mmk, msg;

def sendtxtmsg(mmk, txt):
    mmk, msg = totxtmsg(mmk, txt);
    _botcontrol.send(mmk, msg);

def on_atme(src, txt):
    return;

# 回调接口

_tabot_cb_flt_atme_qqgroup = {'mmk':{'mirai'},'msg':{'data':{'type':'GroupMessage','messageChain':[{'type':'At','target':CONSTS.BOT_QQ}]}}};
_tabot_cb_flt_atme_tggroup = {'mmk':{'telegram'},'msg':{'message': {'text': '.*@%s.*' % CONSTS.BOT_TG, 'entities': [{'type': 'mention'}]}}};
def _tabot_cb_fnc_atme(mmk, msg):
    if mmk == 'mirai':
        _src, _txt = miraitxtmsg(mmk, msg['data']);
        on_atme(_src, _txt);
    elif mmk == 'telegram':
        _src, _txt = tgtxtmsg(mmk, msg['message']);
        on_atme(_src, _txt);
    return;

_mod_cbs.append({'fnc': _tabot_cb_fnc_atme,         'flt': _tabot_cb_flt_atme_qqgroup,      'key': '_tabot_talker_cb_atme_qqgroup'  });
_mod_cbs.append({'fnc': _tabot_cb_fnc_atme,         'flt': _tabot_cb_flt_atme_tggroup,      'key': '_tabot_talker_cb_atme_tggroup'  });



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Talker Stopped');
    return;
