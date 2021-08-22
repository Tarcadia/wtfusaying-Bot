
from contextsensor import update
import random;
import json;
import time;
import io;
import http.client as htpc;
import threading as thr;
import logging;

VERSION = 'v20210808';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Telegram Message Manager Loaded');


TELEGRAM_HOST = 'api.telegram.org';
BOT_AGENT = 'Bot';

# tgmessagemanager      : dict
# {
#   # 链接配置
#   'timeout'           : float,        // 超时设置
#   'conntimeout'       : float,        // https超时设置，用于底层的超时
#   'token'             : str,          // 验证token
#
#   # 链接实现
#   'connlock'          : RLock,        // 链接访问锁，包括链接实例的访问，修改和模块对外呈现的state的访问和修改
#   'connection'        : httpsconn,    // 链接HTTPSConnection实例
#   'state'             : str,          // 链接状态，'None' | 'Opening' | 'Opened' | 'Failed' | 'Closing' | 'Closed'
#   'upd_id'            : int,          // 更新id
#
#   # 消息缓存队列
#   'buffer_size'       : int = 1024,   // 缓存大小
#   'buffer_lock'       : lock,         // 缓存锁
#   'buffer_send'       : list,         // 发送缓存
#   'buffer_recv'       : dict[updId]   // 接收缓存
# }


# messagemanager = new()
# 初始化一个messagemanager
def new(
    timeout             : float = 10,
    conntimeout         : float = 10,
    token               : str = '<id>:<key>',
    buffer_size         : int = 1024
    ):
    mm = {
        'timeout'       : timeout,
        'conntimeout'   : conntimeout,
        'token'         : token,
        'connlock'      : thr.RLock(),
        'connection'    : None,
        'state'         : 'None',
        'upd_id'        : 0,
        'buffer_size'   : buffer_size,
        'buffer_lock'   : thr.RLock(),
        'buffer_send'   : list(),
        'buffer_recv'   : dict()
    }
    return mm;

# messagemanager = set(messagemanager)
# 对一个messagemanager进行部分设置
def set(
    mm,
    timeout             : float = None,
    conntimeout         : float = None,
    token               : str = None,
    buffer_size         : int = None

    ):
    with mm['connlock']:
        if token:
            if mm['state'] in {'None', 'Closed'}:
                mm['token'] = token;
            else:
                mm['state'] = 'Closing';
                mm['connection'].close();
                mm['token'] = token;
                mm['state'] = 'Closed';
                logger.info('Reset close');
        if conntimeout:
            if mm['state'] in {'None', 'Closed'}:
                mm['timeout'] = timeout;
            else:
                mm['state'] = 'Closing';
                mm['connection'].close();
                mm['timeout'] = timeout;
                mm['state'] = 'Closed';
            
    if timeout != None:
        mm['timeout'] = timeout;
    
    with mm['buffer_lock']:
        if buffer_size != None:
            mm['buffer_size'] = buffer_size;
    
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager建立连接并验证连接状态
def open(mm):

    with mm['connlock']:
        _state = mm['state'];
        if _state in {'None', 'Closed'}:
            mm['state'] = 'Opening';
            _header = {'connection': 'keep-alive', 'user-agent': BOT_AGENT};
            _url = '/bot' + mm['token'];
            try:
                _cmd = '/getMe';
                if _state in {'None'}:
                    mm['connection'] = htpc.HTTPSConnection(host = TELEGRAM_HOST, timeout = mm['timeout']);
                elif _state in {'Closed'}:
                    mm['connection'].connect();
                mm['connection'].request('GET', _url + _cmd, headers = _header);
                _resp = mm['connection'].getresponse();
                _code = _resp.status;
            except:
                logger.error('Log in failed');
                mm['state'] = 'Failed';
                return mm;
            
            if _code in range(200, 300):
                _resp.read();
                logger.info('Log in success');
                mm['state'] = 'Opened';
            else:
                logger.error('Log in failed with code: %d' % _code);
                mm['state'] = 'Failed';
    
    return mm;

# messagemanager = close(messagemanager)
# 对一个messagemanager关闭连接
def close(mm):
    with mm['connlock']:
        if mm['state'] in {'Opened', 'Failed'}:
            mm['state'] = 'Closing';
            mm['connection'].close();
            mm['state'] = 'Closed';
            logger.info('Closed');
    return mm;

# messagemanager = do_update(messagemanager)
# 对一个messagemanager进行一轮接收
def do_update(mm):
    with mm['connlock']:
        if mm['state'] == 'Opened':
            try:
                _url = '/bot' + mm['token'] + '/getUpdates?offset=' + str(mm['upd_id']);
                _header = {'connection': 'keep-alive', 'user-agent': BOT_AGENT};
                mm['connection'].request('GET', _url, headers = _header);
                _resp = mm['connection'].getresponse();
                _code = _resp.status;
                if _code in range(200, 300):
                    _recv = _resp.read();
                    _pack = json.loads(_recv);
                    _ok = _pack['ok'];
                    _datas = _pack['result'] if 'result' in _pack else [];
                else:
                    mm['state'] = 'Failed';
                    logger.error('Recv failed, with code %d' % _code);
                    return mm;
            
            except json.JSONDecodeError:
                _datas = [];
                logger.error('Invalid recv');
            
            except htpc.NotConnected:
                mm['connection'].close();
                mm['state'] = 'Closed';
                logger.error('Invalid connection');
                return mm;
            
            except:
                mm['state'] = 'Failed';
                logger.error('Recv failed');
                return mm;

        else:
            logger.error('Invalid connection');
            return mm;
        
        if not _ok:
            mm['state'] = 'Failed';
            logger.error('Recv failed');
            return mm;
        
    for _data in _datas:
        if _data:
            upd_id = _data['update_id'];
            with mm['buffer_lock']:
                if not upd_id in mm['buffer_recv']:
                    mm['upd_id'] = upd_id + 1;
                if len(mm['buffer_recv']) < mm['buffer_size']:
                    mm['buffer_recv'][upd_id] = _data;
                else:
                    _k = next(iter(mm['buffer_recv']))
                    mm['buffer_recv'].pop(_k);
                    mm['buffer_recv'][upd_id] = _data;
                    logger.error('Full recv buffer');

    return mm;

# messagemanager, obj = query(messagemanager, obj)
# 对一个messagemanager的连接进行一次查询，等待成功返回查询结构，或等待失败返回None
def query(mm, data: dict = None):
    if data:
        with mm['connlock']:
            if mm['state'] == 'Opened':
                try: # SEND
                    _cmd = data['command'];
                    _type = data['type'] if 'type' in data else 'application/json';
                    _body = data['content'] if 'content' in data else {};
                    _url = '/bot' + mm['token'] + '/' + _cmd;
                    if _type == 'application/x-www-form-urlencoded':
                        if type(_body) == str:
                            _send = _body;
                        elif type(_body) == dict:
                            _send = '&'.join([_k + '=' + _body[_k] for _k in _body]);
                        else:
                            _send = str(_body);
                    elif _type == 'application/json':
                        _send = json.dumps(_body);
                    elif _type == 'multipart/form-data' and type(_body) == list:
                        _boundary = '-' + '-'.join(str(random.randint(1000000000000000, 9999999999999999))) + '---';
                        _list = [];
                        for _sub in _body:
                            if 'file' in _sub:
                                _file = _sub['file'];
                                _name = _sub['name'] if 'name' in _sub else 'tmp';
                                _fnam = _sub['filename'] if 'filename' in _sub else 'tmp';
                                _ftyp = _sub['filetype'] if 'filetype' in _sub else 'application/*';
                                _type = _type + '; ' + 'boundary=' + _boundary;
                                _tag = 'Content-Disposition: form-data; name="%s"; filename="%s"' % (_name, _fnam);
                                _tty = 'Content-Type: %s' % _ftyp;
                                _list += ['--' + _boundary, _tag, _tty, '', _file.read()];
                        _list.append('--' + _boundary + '--');
                        _send = '\r\n'.join(_list);
                    else:
                        _send = str(_body);
                    _header = {'connection': 'keep-alive', 'user-agent': BOT_AGENT, 'Content-Type': _type, 'Content-Length' : len(_send)};
                    mm['connection'].request('POST', _url, body = _send, headers = _header);
                
                except KeyError:
                    logger.error('Invalid sned');
                    return mm, None;

                except htpc.NotConnected:
                    mm['state'] = 'Closing';
                    mm['connection'].close();
                    mm['state'] = 'Closed';
                    logger.error('Invalid connection');
                    return mm, None;
                
                except:
                    mm['state'] = 'Failed';
                    logger.error('Send failed');
                    return mm, None;
                
                try: # RECV
                    _resp = mm['connection'].getresponse();
                    _code = _resp.status;
                    if _code in range(200, 300):
                        _recv = _resp.read();
                        _pack = json.loads(_recv);
                        _ok = _pack['ok'];
                        _data = _pack['result'];
                    
                    else:
                        mm['state'] = 'Failed';
                        logger.error('Recv failed, with code %d' % _code);
                        return mm, None;
                
                except json.JSONDecodeError:
                    logger.error('Invalid recv');
                    return mm, None;
                
                except htpc.NotConnected:
                    mm['connection'].close();
                    mm['state'] = 'Closed';
                    logger.error('Invalid connection');
                    return mm, None;
                
                except:
                    mm['state'] = 'Failed';
                    logger.error('Recv failed');
                    return mm, None;
                
                if _ok:
                    return mm, _data;
                
                else:
                    logger.error('Recv failed');
                    return mm, None;
                
            else:
                logger.error('Invalid connection');
                return mm, None;
            
    else:
        return mm, None;

# messagemanager, bool = send(messagemanager, obj)
# 对一个messagemanager的连接进行一次发送，等待成功或失败或超时返回成功状态
def send(mm, data: dict = None):
    mm, _ret = query(mm, data = data);
    if _ret == None:
        return mm, False;
    else:
        return mm, True;

# messagemanager, obj = recv(messagemanager)
# 对一个messagemanager的连接进行一次接收，如果超时无内容返回None
def recv(mm):
    time_start = time.time();
    while time.time() - time_start <= mm['timeout']:
        with mm['buffer_lock']:
            if len(mm['buffer_recv']) > 0:
                _k = next(iter(mm['buffer_recv']));
                _recv = mm['buffer_recv'].pop(_k);
                return mm, _recv;
    return mm, None;

# messagemanager, succ = check(messagemanager)
# 对一个messagemanager的连接进行一次查询，无内容返回False，有内容返回True
def check(mm):
    with mm['buffer_lock']:
        if len(mm['buffer_recv']) > 0:
            return mm, True;
        else:
            return mm, False;



class TgMessageManager:

    @property
    def state(self):
        with self._mm['connlock']:
            return self._mm['state'];
    
    def __init__(
        self,
        timeout         : float = 10,
        conntimeout     : float = 10,
        token           : str = '<id>:<key>',
        buffer_size     : int = 1024
        ) -> None:

        self._on_updt_polling = False;
        self._th_updt_polling = None;

        self._mm = new(
            timeout = timeout,
            conntimeout = conntimeout,
            token = token,
            buffer_size = buffer_size
        );
        return None;
    
    def set(
        self,
        timeout         : float = None,
        conntimeout     : float = None,
        token           : str = None,
        buffer_size     : int = None
        ):

        self._mm = set(
            self._mm,
            timeout = timeout,
            conntimeout = conntimeout,
            token = token,
            buffer_size = buffer_size
        );
        return;

    def open(self):
        self._mm = open(self._mm);
        return;

    def close(self):
        self._mm = close(self._mm);
        return;
    
    def send(self, data: dict = None):
        self._mm, _ack = send(self._mm, data = data);
        return _ack;
    
    def query(self, data: dict = None):
        self._mm, _resp = query(self._mm, data = data);
        return _resp;

    def recv(self):
        self._mm, _recv = recv(self._mm);
        return _recv;

    def check(self):
        self._mm, _succ = check(self._mm);
        return _succ;
    

    def _updt_polling(self):
        _reopen_delay = 1;
        _max_reopen_delay = 16;
        _last_open = time.time();
        
        while self._on_updt_polling:
            if self.state == 'None':
                self.open();
                logger.info('Updt polling open');
            elif self.state == 'Failed':
                self.close();
                logger.info('Updt polling fail close');
            elif self.state == 'Closed':
                if time.time() - _last_open >= _reopen_delay:
                    self.open();
                    _last_open = time.time();
                    if _reopen_delay * 2 < _max_reopen_delay:
                        _reopen_delay *= 2;
                    logger.info('Updt polling open');
            elif self.state == 'Opened':
                self._mm = do_update(self._mm);
                _last_open = time.time();
                _reopen_delay = 1;
            time.sleep(_reopen_delay);
        self.close();
        return;

    def threadpolling(self):
        self._on_updt_polling = True;
        self._th_updt_polling = thr.Thread(
            target = self._updt_polling,
            name = 'Telegram Message Manager Updt Polling'
        )

        _time_start = time.time();
        self._th_updt_polling.start();
        while time.time() - _time_start < self._mm['timeout'] and not self.state == 'Opened':
            pass;
        if self.state == 'Opened':
            return [self._th_updt_polling];
        else:
            self._on_updt_polling = False;
            self._th_updt_polling.join();
            logger.error('Thread polling start failed');
            return [];
    
    def threadstop(self):
        self.send({'command': 'close'});
        self._on_updt_polling = False;
        if self._th_updt_polling.is_alive():
            self._th_updt_polling.join();
        return;

