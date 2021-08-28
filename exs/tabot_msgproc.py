
import CONSTS;

import re;
import time;
import logging;

VERSION = 'v20210823';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot Message Process - ex Loaded');



# src               : dict          // 一条Tabot里的message的来源的表示
# {
#   'mmk'           : mmk,          // 来源mmk，
#   'ctype'         : str,          // mm接口中对消息来源类型定义的封装，
#                                   // mirai的group、tg的group是'g'，mirai的grouptemp是'gt'，tg的supergroup是'gs'
#                                   // mirai的friend、tg的private是'p'，mirai的stranger是'pt'，mirai的otherplatform是'po'
#                                   // tg的channel是'c'，未知的是'u'
#   'rcid'          : id,           // mm接口中对对话id的定义的封装，mirai的qq号、群号、本号的其他platform名称，tg的chatid，tg的channelname（@xxx）
#   'cid'           : str,          // 对mmk, ctype, rcid的整体封装，为'<mmk>.<ctype[0]><rcid>'用于在对接口抽象后统一的标识所有接口下所有的对话
#   'uid'           : id,           // 来源userid，mirai的qq号，tg的userid
#   'mid'           : id,           // 消息的id，qq、tg的messageid
#   'time'          : time          // 消息的时间
# }

# tgt               : dict          // 一条Tabot里的message的去向的表示，内容应当是src的子集，可以隐式的将src作为tgt传入
# {
#   'mmk'           : mmk,          // 去向mmk
#   'ctype'         : str,          // 去向ctype
#   'rcid'          : id,           // 去向的对话的id
#   'cid'           : id,           // 去向的cid
# }



# 建立一个src
def src(mmk, ctype, rcid, uid = 0, mid = 0, t = None):
    if t == None:
        t = time.time();
    _src = {
        'mmk'       : mmk,
        'ctype'     : ctype,
        'rcid'      : rcid,
        'cid'       : mmk + '.' + ctype[0] + str(rcid),
        'uid'       : uid,
        'mid'       : mid,
        'time'      : t
    };
    return _src;

# 获得message的src
def msgsrc(mmk, msg):
    if re.match('mirai.*', mmk):
        if msg['data']['type'] == 'FriendMessage':
            _ctype = 'p';
            _rcid = msg['data']['sender']['id'];
            _uid = msg['data']['sender']['id'];
            _mid = msg['data']['messageChain'][0]['id'];
            _time = msg['data']['messageChain'][0]['time'];
        elif msg['data']['type'] == 'StrangerMessage':
            _ctype = 'pt';
            _rcid = msg['data']['sender']['id'];
            _uid = msg['data']['sender']['id'];
            _mid = msg['data']['messageChain'][0]['id'];
            _time = msg['data']['messageChain'][0]['time'];
        elif msg['data']['type'] == 'OtherClientMessage':
            _ctype = 'po';
            _rcid = msg['data']['sender']['id'];
            _uid = msg['data']['sender']['platform'];
            _mid = msg['data']['messageChain'][0]['id'];
            _time = msg['data']['messageChain'][0]['time'];
        elif msg['data']['type'] == 'TempMessage':
            _ctype = 'gt';
            _rcid = msg['data']['sender']['group']['id'];
            _uid = msg['data']['sender']['id'];
            _mid = msg['data']['messageChain'][0]['id'];
            _time = msg['data']['messageChain'][0]['time'];
        elif msg['data']['type'] == 'GroupMessage':
            _ctype = 'g';
            _rcid = msg['data']['sender']['group']['id'];
            _uid = msg['data']['sender']['id'];
            _mid = msg['data']['messageChain'][0]['id'];
            _time = msg['data']['messageChain'][0]['time'];
        else:
            _ctype = 'u';
            _rcid = msg['data']['sender']['id'] if 'sender' in msg['data'] else 0;
            _uid = msg['data']['sender']['id'] if 'sender' in msg['data'] else 0;
            _mid = msg['data']['messageChain'][0]['id'] if 'messageChain' in msg['data'] else 0;
            _time = msg['data']['messageChain'][0]['time'] if 'messageChain' in msg['data'] else 0;
    elif re.match('telegram.*', mmk):
        if msg['message']['chat']['type'] == 'private':
            _ctype = 'p';
            _rcid = msg['message']['chat']['id'];
            _uid = msg['message']['from']['id'];
            _mid = msg['message']['message_id'];
            _time = msg['message']['date'];
        elif msg['message']['chat']['type'] == 'group':
            _ctype = 'g';
            _rcid = msg['message']['chat']['id'];
            _uid = msg['message']['from']['id'];
            _mid = msg['message']['message_id'];
            _time = msg['message']['date'];
        elif msg['message']['chat']['type'] == 'supergroup':
            _ctype = 'gs'
            _rcid = msg['message']['chat']['id'];
            _uid = msg['message']['from']['id'];
            _mid = msg['message']['message_id'];
            _time = msg['message']['date'];
        elif msg['message']['chat']['type'] == 'channel':
            _ctype = 'c'
            _rcid = msg['message']['chat']['id'];
            _uid = msg['message']['from']['id'];
            _mid = msg['message']['message_id'];
            _time = msg['message']['date'];
        else:
            _ctype = 'u';
            _rcid = msg['message']['chat']['id'] if 'chat' in msg['message'] else 0;
            _uid = msg['message']['from']['id'] if 'from' in msg['message'] else 0;
            _mid = msg['message']['message_id'] if 'message_id' in msg['message'] else 0;
            _time = msg['message']['date'] if 'date' in msg['message'] else 0;
    else:
        _ctype = 'u';
        _rcid = 0;
        _uid = 0;
        _mid = 0;
        _time = 0;
    
    _src = src(mmk,
        ctype = _ctype,
        rcid = _rcid,
        uid = _uid,
        mid = _mid,
        t = _time
    );
    return _src;

# 获得message的txt，即message的文本内容，规则是只提取其中纯文本的消息
def msgtxt(mmk, msg):
    if re.match('mirai.*', mmk):
        _txtchain = [_t['text'] for _t in msg['data']['messageChain'] if _t['type'] == 'Plain'];
        _txt = '\n'.join(_txtchain);
    elif re.match('telegram.*', mmk):
        _txt = msg['message']['text'] if 'text' in msg else '';
    else:
        _txt = '';
    return _txt;

# 获得message的多媒体txt，即message的包含多媒体信息的文本形式，如包含转换[图片][表情]等
#######################################          还没实现
def msgmiltitxt(mmk, msg):
    if re.match('mirai.*', mmk):
        _txtchain = [_t['text'] for _t in msg['data']['messageChain'] if _t['type'] == 'Plain'];
        _txt = '\n'.join(_txtchain);
    elif re.match('telegram.*', mmk):
        _txt = msg['message']['text'] if 'text' in msg else '';
    else:
        _txt = '';
    return _txt;

# 将txt组织成发给tgt的msg，不包含除了引用的任何复杂元素
def tomsgtxt(tgt, txt, quote = None):
    if tgt:
        if re.match('mirai.*', tgt['mmk']):
            if tgt['ctype'] == 'p':
                _cmd = 'sendFriendMessage';
            elif tgt['ctype'] == 'pt':
                _cmd = 'sendFriendMessage';
            elif tgt['ctype'] == 'g':
                _cmd = 'sendFriendMessage';
            elif tgt['ctype'] == 'gt':
                _cmd = 'sendFriendMessage';
            else:
                _cmd = '';
            if _cmd:
                _msg = {'command': _cmd, 'content': {'target': tgt['rcid'], 'messageChain': [{'type': 'Plain', 'text': txt}]}};
                if quote == True:
                    _msg['command']['quote'] = tgt['mid'];
                elif quote:
                    _msg['command']['quote'] = quote;
            else:
                _msg = None;
        elif re.match('telegram.*', tgt['mmk']):
            _msg = {'command': 'sendMessage', 'type': 'application/json', 'content': {'chat_id': tgt['rcid'], 'text': txt}};
            if quote == True:
                _msg['command']['reply_to_message_id'] = tgt['mid'];
                _msg['command']['allow_sending_without_reply'] = True;
            elif quote:
                _msg['command']['reply_to_message_id'] = quote;
                _msg['command']['allow_sending_without_reply'] = True;
        else:
            _msg = None;
    else:
        _msg = None;
    return _msg;

# 将message组织成发给tgt的msg，message应当为一个约定好的形式，但此处为实现
#########################################             没实现呢
def tomsg(tgt, message, quote = None):
    if tgt:
        if re.match('mirai.*', tgt['mmk']):
            if tgt['ctype'] == 'p':
                _cmd = 'sendFriendMessage';
            elif tgt['ctype'] == 'pt':
                _cmd = 'sendFriendMessage';
            elif tgt['ctype'] == 'g':
                _cmd = 'sendFriendMessage';
            elif tgt['ctype'] == 'gt':
                _cmd = 'sendFriendMessage';
            else:
                _cmd = 'sendTempMessage';
            _msg = {'command': _cmd, 'content': {'target': tgt['rcid'], 'messageChain': 'XXXXXXXXXXXXXXXXXXXX'}};
        elif re.match('telegram.*', tgt['mmk']):
            if ...:
                _msg = {'command': 'sendMessage', 'type': 'application/json', 'content': {'chat_id': tgt['rcid'], 'XXXXXXXXXX': 'XXXXXXXXXXXXXXXX'}};
            elif ...:
                _msg = {'command': 'sendMessage', 'type': 'xxxx', 'content': {'chat_id': tgt['rcid'], 'XXXXXXXXXX': 'XXXXXXXXXXXXXXXX'}};
        else:
            _msg = None;
    else:
        _msg = None;
    return _msg;





# 接口函数

#保存
def save():
    return;
