
import time;
import threading as thr;
import logging;

VERSION = 'v20210810';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[1;34m[%(asctime)s][%(levelname)s]\033[0;32m[%(name)s]\033[0m >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Loop Back Message Manager Loaded');


# loopbackmessagemanager: dict
# {
#   # 消息缓存队列
#   'buffer_size'       : int = 1024,   // 缓存大小
#   'buffer_lock'       : RLock,        // 缓存锁'
#   'buffer_recv'       : list          // 接收缓存
# }



# messagemanager = new()
# 初始化一个messagemanager
def new(
    buffer_size         : int = 1024
    ):
    mm = {
        'buffer_size'   : buffer_size,
        'buffer_lock'   : thr.RLock(),
        'buffer_recv'   : list()
    }
    return mm;

# messagemanager, bool = send(messagemanager, obj)
# 进行一次向loopback的发送
def send(mm, data: dict or str = None):
    if type(data) == str:
        logger.info(data);
    elif type(data) == dict:
        for _k in data:
            logger.info('%6s : %s' % (_k, data[_k]));
    with mm['buffer_lock']:
        if len(mm['buffer_recv']) < mm['buffer_size']:
            mm['buffer_recv'].append(data);
        else:
            mm['buffer_recv'].pop(0);
            mm['buffer_recv'].append(data);
            logger.error('Full recv buffer');
    
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
# 对一个messagemanager的连接进行一次查询，返回None
def query(mm, data: dict or str = None):
    mm, _ack = send(mm, data = data);
    return mm, None;

# messagemanager, succ = check(messagemanager)
# 对一个messagemanager的连接进行一次查询，无内容返回False，有内容返回True
def check(mm):
    with mm['buffer_lock']:
        if len(mm['buffer_recv']) > 0:
            return mm, True;
        else:
            return mm, False;

# messagemanager = do_recv(messagemanager)
# 对一个messagemanager进行一轮接收，不实现
def do_recv(mm):
    return mm;


class LoopbackMessageManager:

    def __init__(
        self,
        buffer_size     : int = 1024
        ) -> None:
    
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

    def threadpolling(self):
        logger.info('Loopback Message Manager Polling');
        return [];
    
    def threadstop(self):
        logger.info('Loopback Message Manager Polling Stopped');
        return;
