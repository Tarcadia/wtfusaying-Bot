
import time;
import threading as thr;
import logging;

VERSION = 'v20210810';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('IO Message Manager Loaded');


# iomessagemanager      : dict
# {
#   # 输出
#   'print_lock'        :RLock,         // Print锁
#   # 消息缓存队列
#   'buffer_size'       : int = 1024,   // 缓存大小
#   'buffer_lock'       : RLock,        // 缓存锁
#   'buffer_recv'       : list          // 接收缓存
# }



# obj = raw_recv()
# 进行一次键盘接收
def raw_recv():
    _recv = input();
    _recvs = _recv.split();
    if len(_recvs) > 1:
        _data = {
            'call'          : _recvs[0],
            'args'          : _recvs[1:]
        }
        
    elif len(_recvs) > 0:
        _data = {
            'call'          : _recvs[0],
            'args'          : None
        }
    else:
        _data = None;
    return _data;



# messagemanager = new()
# 初始化一个messagemanager
def new(
    buffer_size         : int = 1024
    ):
    mm = {
        'print_lock'    : thr.RLock(),
        'buffer_size'   : buffer_size,
        'buffer_lock'   : thr.RLock(),
        'buffer_recv'   : list()
    }
    return mm;

# messagemanager, bool = send(messagemanager, obj)
# 进行一次向屏幕的发送
def send(mm, data: dict or str = None):
    _t = time.strftime('%Y%m%d-%H%M%S');
    with mm['print_lock']:
        if type(data) == str:
            print("[%15s] >> %s" % (_t, data));
        elif type(data) == dict:
            for _k in data:
                print("[%15s] >> %6s : %s" % (_t, _k, data[_k]));
    return mm, True;

# messagemanager, obj = recv(messagemanager)
# 进行一次缓存接收
def recv(mm):
    with mm['buffer_lock']:
        if len(mm['buffer_recv']) > 0:
            return mm, mm['buffer_recv'].pop(0);
        else:
            return mm, None;

# messagemanager, obj = query(messagemanager, obj)
# 对一个messagemanager的连接进行一次查询，等待成功返回查询结构，或等待失败返回None
def query(mm, data: dict or str = None):
    mm = send(mm, data = data);
    _data = raw_recv();
    return mm, _data;

# messagemanager, succ = check(messagemanager)
# 对一个messagemanager的连接进行一次查询，无内容返回False，有内容返回True
def check(mm):
    with mm['buffer_lock']:
        if len(mm['buffer_recv']) > 0:
            return mm, True;
        else:
            return mm, False;

# messagemanager = do_recv(messagemanager)
# 对一个messagemanager进行一轮接收
def do_recv(mm):
    _data = raw_recv();
    mm, _ack = send(mm, data = _data);
    with mm['buffer_lock']:
        if len(mm['buffer_recv']) < mm['buffer_size']:
            mm['buffer_recv'].append(_data);
        else:
            mm['buffer_recv'].pop(0);
            mm['buffer_recv'].append(_data);
            logger.error('Full recv buffer');
    return mm;


class IOMessageManager:

    def __init__(
        self,
        buffer_size     : int = 1024
        ) -> None:

        self._on_updt_polling = False;
        self._th_updt_polling = None;

        self._mm = new(
            buffer_size = buffer_size
        );
        return None;
    
    def open(self):
        return;

    def close(self):
        return;
    
    def send(self, data: dict or str = None):
        self._mm, _ack = send(self._mm, data = data);
        return _ack;
    
    def query(self, data: dict or str = None):
        self._mm, _resp = query(self._mm, data = data);
        return _resp;

    def recv(self):
        self._mm, _recv = recv(self._mm);
        return _recv;

    def check(self):
        self._mm, _succ = check(self._mm);
        return _succ;

    def _updt_polling(self):
        while self._on_updt_polling:
            self._mm = do_recv(self._mm);
        return;

    def threadpolling(self):
        self._on_updt_polling = True;
        self._th_updt_polling = thr.Thread(
            target = self._updt_polling,
            name = 'IO Message Manager Update Polling'
        );
        self._th_updt_polling.start();
        return [self._th_updt_polling];
    
    def threadstop(self):
        self._on_updt_polling = False;
        self._th_updt_polling.daemon = True;
        if self._th_updt_polling.is_alive():
            self._th_updt_polling.join(timeout = 3);
        return;
