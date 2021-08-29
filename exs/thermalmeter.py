
import random;
import time;
import threading as thr;
import logging;

VERSION = 'v20210804';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);

logger.info('Thermal Meter Loaded');

# thermalmeter          : dict
# {
#   tau                 : float,        // 热度半衰期，即一个影响发言欲望的行为应当带来一定半衰期的指数冲击响应，单位s
#   talkrate            : float = 1,    // 发言的对话率，即同时发言，平均每talkrate条群消息回复一条
#   callrate            : float = 1,    // 刺激的对话率
#   size                : int,          // 队列的大小，维护talkheat、selfheat、selfcool队列，不建议过大或过小
#   talklock            : RLock,        // 访问锁
#   value               : float,        // 自己的发言欲望，群消息后自己的发言欲望上升，受刺激后自己的发言欲望上升，发言后自己发言欲望下降
#                                       // 做指数响应的衰变，即v = sum(xi * u(t-ti) * 2^(-(t-ti)/tau))
#                                       // 更新：考虑到长期累积的大量发言会带来很大的发言欲望，这里需要引入非线性响应
#                                       // 可以考虑非线性声学之类的模型
#   valuetime           : time          // 自己的发言欲望值计算的时间维护
# }



# 建立一个thermalmeter
def new(
    tau                 : float = 60 * 60,
    talkrate            : float = 4,
    callrate            : float = 1,
    size                : int = 64
):
    _tm = {
        'tau'           : tau,
        'talkrate'      : talkrate,
        'callrate'      : callrate,
        'size'          : size,
        'talklock'      : thr.RLock(),
        'value'         : 0,
        'valuetime'     : 0
    };
    return _tm;

# 根据时间更新计算
def update(tm: dict, t = None):
    if t == None:
        t = time.time();
    dt = t - tm['valuetime'];
    b = 1;
    if tm['value'] > 1E-3:
        vinvb = 1 / tm['value'] + b;
        vinvbx = vinvb * pow(2, dt / tm['tau']);
        tm['value'] = 1/(vinvbx - b);
        tm['valuetime'] = t;
    else:
        tm['value'] = tm['value'] * pow(2, -dt / tm['tau']);
        tm['valuetime'] = t;
    return tm;

# 加入一条对话消息的时间响应
def onmsg(tm: dict, t = None):
    if t == None:
        t = time.time();
    with tm['talklock']:
        tm = update(tm, t = t);
        tm['value'] += 1 / tm['talkrate'];
    return tm;

# 加入一条刺激的时间响应
def oncall(tm: dict, k = 1, t = None):
    if t == None:
        t = time.time();
    with tm['talklock']:
        tm = update(tm, t = t);
        tm['value'] += k / tm['callrate'];
    return tm;

# 加入一条受激发言的时间响应
def oncalltalk(tm: dict, t = None):
    if t == None:
        t = time.time();
    with tm['talklock']:
        tm = update(tm, t = t);
        tm['value'] -= 1 / tm['talkrate'];
    return tm;

# 加入一条发言的时间响应
def ontalk(tm: dict, t = None):
    if t == None:
        t = time.time();
    with tm['talklock']:
        tm = update(tm, t = t);
        tm['value'] -= 1;
    return tm;

# 计算当前欲望
def valuetalk(tm: dict, t = None):
    if t == None:
        t = time.time();
    with tm['talklock']:
        tm = update(tm, t = t);
        v = tm['value'];
        return tm, v;

# 计算当前是否可以发言，p为引入条件概率
def cantalk(tm: dict, p: float = 1, t = None):
    return random.random() <= valuetalk(tm = tm, t = t) and random.random() <= p;

class ThermalMeter():

    @property
    def value(self):
        self._tm, _v = valuetalk(self._tm);
        return _v;

    def __init__(
        self,
        tau             : float = 60 * 60,
        talkrate        : float = 4,
        callrate        : float = 1,
        size            : int = 64
    ) -> None:
        self._tm = new(
            tau = tau,
            talkrate = talkrate,
            callrate = callrate,
            size = size
        );
        return;

    def onmsg(self, t = None):
        self._tm = onmsg(self._tm, t = t);
        return;
    
    def oncall(self, k = 1, t = None):
        self._tm = oncall(self._tm, k = k, t = t);
        return;
    
    def oncalltalk(self, t = None):
        self._tm = oncalltalk(self._tm, t = t);
        return;
    
    def ontalk(self, t = None):
        self._tm = ontalk(self._tm, t = t);
        return;
    
    def cantalk(self, p: float = 1, t = None):
        return cantalk(self._tm, p = p, t = t);