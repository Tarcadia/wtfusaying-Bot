
import CONSTS;


import re;
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

# 接口级实现

# 一条 Tabot 里的 message 应该在接口处就被翻译成统一的形式，通过'<mmk>.<cid>'的形式实现唯一的对话场景的标识；
# 在内部处理时应当用统一的逻辑处理统一的 Tabot Message 形式，将一条消息视作一个对话场景里的一个上下文元素；
# 一条 Tabot 中的 message 应当是保护“来源”（src）或“去向”（tgt），和消息内容本体（msg）的；
# Tabot_talker中的miraitxtmsg，tgtxtmsg，totxtmsg接口应当是有高优先级的，作为Tabot中通用的txtmsg处理接口；

# src               : dict          // 一条Tabot里的message的来源的表示
# {
#   'mmk'           : mmk,          // 来源mmk，
#   'cid'           : id,           // 来源chatid，形如'p<xxxxx>'或'g<xxxxx>'
#                                   // p表示是私戳，g是群聊，c是channel，特别的，u表示未识别
#                                   // <xxxxx>是qq号、qq群号、tg的chatid
#   'uid'           : id,           // 来源userid，是qq号或者tg的user的id
#   'mid'           : id,           // 消息的id，qq和tg的id
#   'time'          : time          // 消息的时间
# }

# tgt               : dict          // 一条Tabot里的message的去向的表示
# {
#   'mmk'           : mmk,          // 去向mmk，
#   'cid'           : id,           // 去向chatid，
# }

# 将一个miraimessage翻译成tabotmessage，限于文本内容
def miraitxtmsg(mmk, msg):
    _t = '';
    if msg['type'] == 'FriendMessage':
        _t = 'p';
    elif msg['type'] == 'TempMessage':
        _t = 'p';
    elif msg['type'] == 'GroupMessage':
        _t = 'g';
    else:
        _t = 'u';
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

# 将一个tgmessage翻译成tabotmessage，限于文本内容
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
    else:
        _t = 'u';
    _src = {
        'mmk'       : mmk,
        'cid'       : _t + str(msg['chat']['id']),
        'uid'       : msg['from']['id'],
        'mid'       : msg['message_id'],
        'time'      : msg['date']
    };
    _txt = msg['text'] if 'text' in msg else '';
    return _src, _txt;

# 将一个tabotmessage翻译成mmk对应的message
def totxtmsg(mmk, cid, txt):
    msg = None;
    if re.match('mirai.*', mmk):
        if cid[0] == 'p':
            pass;
        elif cid[0] == 'g':
            pass;
        else:
            pass;
    elif re.match('telegram.*', mmk):
        msg = None;
        if cid[0] == 'p':
            msg = {
                'command'           : 'sendMessage',
                'type'              : 'application/json',
                'content': {
                    'chat_id'       : int(cid[1:]),
                    'text'          : txt
                }
            };
        elif cid[0] == 'g':
            msg = {
                'command'           : 'sendMessage',
                'type'              : 'application/json',
                'content': {
                    'chat_id'       : int(cid[1:]),
                    'text'          : txt
                }
            };
        elif cid[0] == 'c':
            msg = {
                'command'           : 'sendMessage',
                'type'              : 'application/json',
                'content': {
                    'chat_id'       : '@' + cid[1:],
                    'text'          : txt
                }
            };
        else:
            pass;
    return msg;

# 本地实现

def on_atme(src, txt):
    return;

# 回调接口

_tabot_cb_flt_atme_qqgroup = {
    'mmk':{'mirai.*'},
    'msg':{'data':{'type':'GroupMessage','messageChain':[{'type':'At','target':CONSTS.BOT_QQ}]}}
};
_tabot_cb_flt_atme_tggroup = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': '.*@%s.*' % CONSTS.BOT_TG, 'entities': [{'type': 'mention'}]}}
};
def _tabot_cb_fnc_atme(mmk, msg):
    if re.match('mirai.*', mmk):
        _src, _txt = miraitxtmsg(mmk, msg['data']);
        on_atme(_src, _txt);
    elif re.match('telegram.*', mmk):
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
