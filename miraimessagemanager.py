
import json
import time;
import threading as thr;
import websocket as ws;
import logging;

VERSION = 'v20210810';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(name)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Mirai Message Manager Loaded');


# miraimessagemanager   : dict
# {
#   # 链接配置
#   'host'              : str,          // 目标host
#   'timeout'           : float,        // 超时设置
#   'socktimeout'       : float,        // socket超时设置，用于底层的超时
#   'verify_qq'         : str,          // 目标QQ
#   'verify_key'        : str,          // 验证key
#
#   # 链接实现
#   'wslock'            : RLock,        // 链接访问锁，包括链接实例的访问，修改和模块对外呈现的state的访问和修改
#   'websocket'         : websocket,    // 链接WebSocket实例
#   'session'           : str,          // 链接Session
#   'state'             : str,          // 连接状态，'None' | 'Opening' | 'Opened' | 'Failed' | 'Closing' | 'Closed'
#   'sync_id'           : int,          // 同步号
#
#   # 消息缓存队列
#   'buffer_size'       : int = 1024,   // 缓存大小
#   'buffer_lock'       : RLock,        // 缓存锁
#   'buffer_send'       : list,         // 发送缓存
#   'buffer_resp'       : dict[syncId], // 回复缓存
#   'buffer_recv'       : list          // 接收缓存
# }


# messagemanager = new(...)
# 初始化一个messagemanager
def new(
    host                : str = 'localhost:8080',
    timeout             : float = 3,
    socktimeout         : float = 0.3,
    verify_qq           : str = '',
    verify_key          : str = 'INITKEYxxxxxxxx',
    buffer_size         : int = 1024
    ):
    mm = {
        'host'          : host,
        'timeout'       : timeout,
        'socktimeout'   : socktimeout,
        'verify_qq'     : verify_qq,
        'verify_key'    : verify_key,
        'wslock'        : thr.RLock(),
        'websocket'     : ws.WebSocket(),
        'session'       : '',
        'state'         : 'Closed',
        'sync_id'       : 0,
        'buffer_size'   : buffer_size,
        'buffer_lock'   : thr.RLock(),
        'buffer_send'   : list(),
        'buffer_resp'   : dict(),
        'buffer_recv'   : list()
    }
    return mm;

# messagemanager = set(messagemanager, ...)
# 对一个messagemanager进行部分设置
def set(
    mm,
    host                : str = None,
    timeout             : float = None,
    socktimeout         : float = None,
    verify_qq           : str = None,
    verify_key          : str = None,
    buffer_size         : int = None
    ):
    with mm['wslock']:
        if host or verify_qq or verify_key:
            if mm['state'] in {'None', 'Closed'}:
                if host:
                    mm['host'] = host;
                if verify_qq:
                    mm['verify_qq'] = verify_qq;
                if verify_key:
                    mm['verify_key'] = verify_key;
            else:
                mm['state'] = 'Closing';
                mm['websocket'].close();
                if host:
                    mm['host'] = host;
                if verify_qq:
                    mm['verify_qq'] = verify_qq;
                if verify_key:
                    mm['verify_key'] = verify_key;
                mm['state'] = 'Closed';
                logger.info('Reset close');
        if socktimeout != None:
            if mm['state'] != 'None' and mm['websocket'] != None:
                mm['timeout'] = timeout;
                mm['websocket'].settimeout(socktimeout);
            else:
                mm['timeout'] = timeout;
            
    if timeout != None:
        mm['timeout'] = timeout;
                
    with mm['buffer_lock']:
        if buffer_size != None:
            mm['buffer_size'] = buffer_size;
    
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager建立连接并验证连接状态
def open(mm):

    with mm['wslock']:
        _state = mm['state'];
        if _state in {'None', 'Closed'}:
            mm['state'] = 'Opening';
            _uri = 'ws://' + mm['host'] + '/all?' + 'verifyKey=' + mm['verify_key'] + '&qq=' + mm['verify_qq'];
            try:
                mm['websocket'].connect(_uri, timeout = mm['timeout']);
                _recv = mm['websocket'].recv();
                mm['websocket'].settimeout(mm['socktimeout']);
                _auth = json.loads(_recv);
                _auth_code = _auth['data']['code'];
                _auth_session = _auth['data']['session'];
            except:
                mm['state'] = 'Failed';
                return mm;
        
            if _auth_code == 0:
                logger.info('Log in success');
                mm['session'] = _auth_session;
                mm['state'] = 'Opened';
            else:
                logger.error('Log in failed with code: %d' % _auth_code);
                mm['state'] = 'Failed';
    
    return mm;

# messagemanager = close(messagemanager)
# 对一个messagemanager关闭连接
def close(mm):
    with mm['wslock']:
        if mm['state'] in {'Opened', 'Failed'}:
            mm['state'] = 'Closing';
            mm['websocket'].close(timeout = mm['timeout']);
            mm['state'] = 'Closed';
            logger.info('Closed');
    return mm;

# messagemanager = do_recv(messagemanager)
# 对一个messagemanager进行一轮接收
def do_recv(mm):
    time_start = time.time();
    while time.time() - time_start <= mm['timeout']:
        with mm['wslock']:
            if mm['state'] == 'Opened':
                try:
                    _recv = mm['websocket'].recv();
                    _data = json.loads(_recv);
                    _sync = _data['syncId'] if 'syncId' in _data else -1;
                    _cond = _data['data'] if 'data' in _data else {};
                    _code = _cond['code'] if 'code' in _cond else 0;
                
                except ws.WebSocketTimeoutException:
                    return mm;
                
                except json.JSONDecodeError:
                    _data = None;
                    logger.error('Invalid recv');
                
                except ws.WebSocketConnectionClosedException:
                    mm['websocket'].close();
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
            
            if _data:
                if _code in {1, 2, 3, 4}:
                    mm['state'] = 'Failed';
                    logger.error('Recv failed');
                    return mm;
        
        if _data:
            if _sync in {None, '', '-1', -1}:
                with mm['buffer_lock']:
                    if len(mm['buffer_recv']) < mm['buffer_size']:
                        mm['buffer_recv'].append(_data);
                    else:
                        mm['buffer_recv'].pop(0);
                        mm['buffer_recv'].append(_data);
                        logger.error('Full recv buffer');
            else:
                with mm['buffer_lock']:
                    if len(mm['buffer_resp']) < mm['buffer_size']:
                        mm['buffer_resp'][int(_sync)] = _data;
                    else:
                        _k = next(iter(mm['buffer_resp']));
                        mm['buffer_resp'].pop(_k);
                        mm['buffer_resp'][int(_sync)] = _data;
                        logger.error('Full resp buffer');
                    
    return mm;

# messagemanager = do_send(messagemanager)
# 对一个messagemanager的发送队列进行一轮处理
def do_send(mm):

    time_start = time.time();
    while time.time() - time_start <= mm['timeout']:

        with mm['buffer_lock']:
            if len(mm['buffer_send']) > 0:
                _data = mm['buffer_send'].pop(0);
            else:
                return mm;
        
        if _data:
            _buffback = None;
            try:
                _send = json.dumps(_data);
                mm['websocket'].send(_send);
            
            except ws.WebSocketConnectionClosedException:
                _buffback = _data;
                mm['state'] = 'Closing';
                mm['websocket'].close();
                mm['state'] = 'Closed';
                logger.error('Invalid connection');
            
            except:
                _buffback = _data;
                mm['state'] = 'Failed';
                logger.error('Send failed');
                
            if _buffback:
                with mm['buffer_lock']:
                    if len(mm['buffer_resp']) < mm['buffer_size']:
                        mm['buffer_send'].insert(0, _buffback);
                        return mm;
                    else:
                        logger.error('Full send buffer');
                        return mm;
        else:
            return mm;
        
    return mm;

# messagemanager, bool = send(messagemanager, obj)
# 对一个messagemanager的连接进行一次发送，等待成功或失败或超时返回成功状态
def send(mm, data: dict = None):
    time_start = time.time();
    if data and 'content' in data:
        with mm['buffer_lock']:
            _syncId = mm['sync_id'];
            _session = mm['session'];
            mm['sync_id'] = (mm['sync_id'] + 1) % 2147483647;
        
        _data = data.copy();
        _data['content'] = data['content'].copy();
        _data['syncId'] = _syncId;
        _data['content']['sessionKey'] = _session;
        
        with mm['buffer_lock']:
            if len(mm['buffer_send']) < mm['buffer_size']:
                mm['buffer_send'].append(_data);
            else:
                mm['buffer_send'].pop(0);
                mm['buffer_send'].append(_data);
                logger.error('Full send buffer');
        
        while time.time() - time_start <= mm['timeout']:
            with mm['buffer_lock']:
                if _syncId in mm['buffer_resp']:
                    _resp = mm['buffer_resp'].pop(_syncId);
                    _data = _resp['data'] if 'data' in _resp else dict();
                    _code = _data['code'] if 'code' in _data else 0;
                    if _code == 0:
                        return mm, True;
                    else:
                        logger.error('Resp failed');
                        return mm, False;
        logger.error('Resp timeout');
        return mm, False;
    else:
        logger.error('Invalid send');
        return mm, False;

# messagemanager, obj = query(messagemanager, obj)
# 对一个messagemanager的连接进行一次查询，等待成功返回查询结构，或等待失败返回None
def query(mm, data: dict = None):
    time_start = time.time();
    if data and 'content' in data:
        with mm['buffer_lock']:
            _syncId = mm['sync_id'];
            _session = mm['session'];
            mm['sync_id'] = (mm['sync_id'] + 1) % 2147483647;
        
        _data = data.copy();
        _data['content'] = data['content'].copy();
        _data['syncId'] = _syncId;
        _data['content']['sessionKey'] = _session;
        
        with mm['buffer_lock']:
            if len(mm['buffer_send']) < mm['buffer_size']:
                mm['buffer_send'].append(_data);
            else:
                mm['buffer_send'].pop(0);
                mm['buffer_send'].append(_data);
                logger.error('Full send buffer');
        
        while time.time() - time_start <= mm['timeout']:
            with mm['buffer_lock']:
                if _syncId in mm['buffer_resp']:
                    _resp = mm['buffer_resp'].pop(_syncId);
                    return mm, _resp;
        logger.error('Resp timeout');
        return mm, None;
    else:
        logger.error('Invalid send');
        return mm, None;

# messagemanager, obj = recv(messagemanager)
# 对一个messagemanager的连接进行一次接收，如果超时无内容返回None
def recv(mm):
    time_start = time.time();
    while time.time() - time_start <= mm['timeout']:
        with mm['buffer_lock']:
            if len(mm['buffer_recv']) > 0:
                _recv = mm['buffer_recv'].pop(0);
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


class MiraiMessageManager:

    @property
    def state(self):
        with self._mm['wslock']:
            return self._mm['state'];
    
    def __init__(
        self,
        host            : str = 'localhost:8080',
        timeout         : float = 3,
        socktimeout     : float = 0.3,
        verify_qq       : str = '',
        verify_key      : str = 'INITKEYxxxxxxxx',
        buffer_size     : int = 1024
        ) -> None:

        self._on_recv_polling = False;
        self._on_send_polling = False;
        self._on_conn_polling = False;

        self._th_recv_polling = None;
        self._th_send_polling = None;
        self._th_conn_polling = None;

        self._mm = new(
            host = host,
            timeout = timeout,
            socktimeout = socktimeout,
            verify_qq = verify_qq,
            verify_key = verify_key,
            buffer_size = buffer_size
        );
        return None;
    
    def set(
        self,
        host            : str = None,
        timeout         : float = None,
        socktimeout     : float = None,
        verify_qq       : str = None,
        verify_key      : str = None,
        buffer_size     : int = None
        ):

        self._mm = set(
            self._mm,
            host = host,
            timeout = timeout,
            socktimeout = socktimeout,
            verify_qq = verify_qq,
            verify_key = verify_key,
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
    

    def _recv_polling(self):
        self._on_recv_polling = True;
        while self._on_recv_polling:
            self._mm = do_recv(self._mm);
        return;
    
    def _send_polling(self):
        self._on_send_polling = True;
        while self._on_send_polling:
            self._mm = do_send(self._mm);
        return;

    def _conn_polling(self):
        _reopen_delay = 1;
        _max_reopen_delay = 16;
        _last_open = time.time();
        
        while self._on_conn_polling:
            if self.state == 'None':
                self.open();
                logger.info('Conn polling open');
            elif self.state == 'Failed':
                self.close();
                logger.info('Conn polling fail close');
            elif self.state == 'Closed':
                if time.time() - _last_open >= _reopen_delay:
                    self.open();
                    _last_open = time.time();
                    if _reopen_delay * 2 < _max_reopen_delay:
                        _reopen_delay *= 2;
                    logger.info('Conn polling open');
            elif self.state == 'Opened':
                _last_open = time.time();
                _reopen_delay = 1;
            time.sleep(_reopen_delay);
        self.close();
        return;

    def threadpolling(self):
        self._on_conn_polling = True;
        self._th_recv_polling = thr.Thread(
            target = self._recv_polling,
            name = 'Mirai Message Manager Recv Polling'
            );
        self._th_send_polling = thr.Thread(
            target = self._send_polling,
            name = 'Mirai Message Manager Send Polling'
            );
        self._th_conn_polling = thr.Thread(
            target = self._conn_polling,
            name = 'Mirai Message Manager Conn Polling'
        )

        _time_start = time.time();
        self._th_conn_polling.start();
        while time.time() - _time_start < self._mm['timeout'] and not self.state == 'Opened':
            pass;
        if self.state == 'Opened':
            self._th_recv_polling.start();
            self._th_send_polling.start();
            while time.time() - _time_start < self._mm['timeout'] and not self._on_recv_polling and not self._on_send_polling:
                pass;
            return [self._th_recv_polling, self._th_send_polling, self._th_conn_polling];
        else:
            self._on_conn_polling = False;
            self._th_conn_polling.join();
            logger.error('Thread polling start failed');
            return [];
    
    def threadstop(self):

        self._on_recv_polling = False;
        self._on_send_polling = False;
        if self._th_recv_polling.is_alive():
            self._th_recv_polling.join();
        if self._th_send_polling.is_alive():
            self._th_send_polling.join();
        logger.info('Mirai Message Manager Recv Polling Stopped');
        logger.info('Mirai Message Manager Send Polling Stopped');

        self._on_conn_polling = False;
        if self._th_conn_polling.is_alive():
            self._th_conn_polling.join();
        logger.info('Mirai Message Manager Conn Polling Stopped');
        return;
