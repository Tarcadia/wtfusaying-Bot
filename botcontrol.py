
import json;
import re;
import logging;
import threading as thr;

VERSION = 'v20210803';
PATH_CONFIG = './config/';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(format='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Bot Control Loaded');


# botcontrol            : dict
# {
#   # 链接配置
#   'mms'               : dict[mmkey],  // MessageManager接口表；
#   {
#       mm              : object,       // 一个MessageManager类；
#       ...                             // 这里没写一个MM基类，需要实现的接口的定义在下面；
#   }
#   'cbs'               : list,         // 回调列表；
#   [
#       cb              : dict
#       {
#           'flt'       : dict,         // 回调条件，一个dict或者一个函数；
#                                       // 如果是dict，则判定是否dict中的key和对应的元素匹配，
#                                       // 字符串支持re，list判定flt各元素在msg均存在元素匹配
#                                       // dict中的迭代元素迭代判断，
#                       : or function   // 如果是函数，则调用函数判定；
#           (
#               msg     : dict          // 消息的内容
#           ) -> bool,
#           'fnc'       : function      // 回调函数；
#           (
#               mmk     : str,          // 该消息的来源，接口列表中的mmkey
#               msg     : dict          // 消息的内容
#           ) -> None
#       }
#   ]
#   'cbl'               : RLock         // 回调锁；
#   'setl'              : RLock         // 设置锁；
#                                       // 用于避免在遍历mm接口列表和回调列表的过程中由于修改导致的异常
# }



# messagemanager        : object        // 一个MM在这里要求实现check，recv，send，query；
#                                       // check要求是非阻塞的，recv，send，query不建议是阻塞的；
# {
#   _private_,                          // 内部其他实现不管了；
#   ...,
#
#   check()             : bool,         // 返回当前是否有可接收数据；
#   recv()              : msg,          // 返回一个接收到的数据；
#   send(msg)           : bool,         // 发送一个数据；
#   query(msg)          : msg           // 发送一个数据并返回一个结果数据；
# }




def cbfltmatch(msg: dict, flt: dict):
    _f = True;
    if type(flt) == dict:
        for _k in flt:
            if _k in msg:
                if (type(msg[_k]) == int or type(msg[_k]) == float) and (type(flt[_k]) == int or type(flt[_k]) == float):
                    if flt[_k] == msg[_k]:
                        _f = True;
                    else:
                        _f = False;
                        break;
                elif type(msg[_k]) == str and type(flt[_k]) == str:
                    if re.match(flt[_k], msg[_k]):
                        _f = True;
                    else:
                        _f = False;
                        break;
                elif type(msg[_k]) == dict and type(flt[_k]) == dict:
                    if cbfltmatch(msg[_k], flt[_k]):
                        _f = True;
                    else:
                        _f = False;
                        break;
                elif type(msg[_k]) == list and type(flt[_k]) == list:
                    _r = True;
                    for _itm in flt[_k]:
                        _rr = False;
                        for _m in msg[_k]:
                            _rr |= cbfltmatch(_m, _itm);
                        _r &= _rr;
                    if _r:
                        _f = True;
                    else:
                        _f = False;
                        break;
                    
                else:
                    _f = False;
                    break;
            else:
                _f = False;
                break;
    return _f;





def new():
    _bc = dict();
    _bc['mms'] = dict();
    _bc['cbs'] = list();
    _bc['cbl'] = thr.RLock();
    _bc['setl'] = thr.RLock();
    return _bc;

def clear(bc: dict):
    bc.clear();

def regmessagemanager(bc: dict, mm:object, key:str = 'Default'):
    with bc['setl']:
        if key in bc['mms']:
            raise KeyError;
        else:
            bc['mms'][key] = mm;
    return bc;

def regcallback(bc: dict, cbfunc:function, cbfilter:function or dict = None):
    with bc['setl']:
        _cb = {
            'flt': cbfilter,
            'fnc': cbfunc
        };
        bc['cbs'].append(_cb);
    return bc;

def send(bc: dict, mmk: str, msg: dict):
    if mmk in bc['mms']:
        _rt = bc['mms'][mmk].send(msg);
    else:
        _rt = False;
        raise KeyError;
    return bc, _rt;

def query(bc: dict, mmk: str, msg: dict):
    if mmk in bc['mms']:
        _rt = bc['mms'][mmk].query(msg);
    else:
        _rt = None;
        raise KeyError;
    return bc, _rt;

def do_callback(bc: dict, mmk: str, msg: dict):
    with bc['setl']:
        for _cb in bc['cbs']:
            if (_cb['flt'] == None
            or type(_cb['flt']) == dict and cbfltmatch(msg, _cb['flt'])
            or callable(_cb['flt']) and _cb['flt'](msg)
            ):
                with bc['cbl']:
                    try:
                        _cb['fnc'](mmk, msg);
                    except Exception as _err:
                        logger.error('Call Back Failed');

            else:
                pass;
    return bc;


class BotControl:

    def __init__(self) -> None:

        self._bc = new();

        self._on_call_polling = False;
        self._th_call_polling = None;

        return;

    def clear(self):
        self._bc = clear(self._bc);
        return;

    def regmessagemanager(self, mm:object, key:str = 'Default'):
        self._bc = regmessagemanager(self._bc, mm = mm, key = key);
        return;
    
    def regcallback(self, cbfunc:function, cbfilter:function or dict = None):
        self._bc = regcallback(self._bc, cbfunc = cbfunc, cbfilter = cbfilter);
        return;

    def send(self, mmk: str, msg: dict):
        self._bc, _rt = send(self._bc, mmk = mmk, msg = msg);
        return _rt;
    
    def query(self, mmk: str, msg: dict):
        self._bc, _rt = query(self._bc, mmk = mmk, msg = msg);
        return _rt;
    
    def _call_polling(self):
        while self._on_call_polling:
            with self._bc['setl']:
                for _k in self._bc['mms']:
                    if self._bc['mms'][_k].check():
                        _recv = self._bc['mms'][_k].recv();
                        self._bc = do_callback(self._bc, _k, _recv);

        return;
    
    def threadpolling(self):

        self._on_call_polling = True;
        self._th_call_polling = thr.Thread(
            target = self._call_polling,
            name = 'Bot Control Call Polling'
        );
        self._th_call_polling.start();

        return [self._th_call_polling];
    
    def threadstop(self):
        self._on_call_polling = False;
        self._th_call_polling.join();
