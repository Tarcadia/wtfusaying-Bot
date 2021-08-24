
import CONSTS;

import re;
import logging;

VERSION = 'v20210823';
CONFIG = './config/autosave.json';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[1;34m[%(asctime)s][%(levelname)s]\033[0;32m[%(name)s]\033[0m >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot ex Loaded');



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
        'cid'       : _t + str(msg['sender']['group']['id'] if _t == 'g' else msg['sender']['id']),
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



# 将一个mmk的message翻译成一个tabotmessage
def fromtxtmsg(mmk, msg):
    if re.match('mirai.*', mmk):
        _src, _txt = miraitxtmsg(mmk, msg['data']);
    elif re.match('telegram.*', mmk):
        _src, _txt = tgtxtmsg(mmk, msg['message']);
    else:
        _src, _txt = None, '';
    return _src, _txt;



# 将一个tabotmessage翻译成mmk对应的message
def totxtmsg(mmk, cid, txt):
    msg = None;
    if re.match('mirai.*', mmk):
        if cid[0] == 'p':
            msg = {
                'command'           : 'sendFriendMessage',
                'content'           : {
                    'target'        : int(cid[1:]),
                    'messageChain'  : [{
                        'type'      : 'Plain',
                        'text'      : txt
                    }]
                }
            }
        elif cid[0] == 'g':
            msg = {
                'command'           : 'sendGroupMessage',
                'content'           : {
                    'target'        : int(cid[1:]),
                    'messageChain'  : [{
                        'type'      : 'Plain',
                        'text'      : txt
                    }]
                }
            }
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
