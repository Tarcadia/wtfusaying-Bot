
import json
import websocket as ws;
import websocket._abnf as wsabnf;
import logging;

VERSION = 'v20210808';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Mirai Message Manager Loaded');


# messagemanager        : dict
# {
#   # 链接
#   'remote_host'       : str,          // 目标host
#   'timeout'           : float,        // 超时设置
#   'verify_qq'         : str,          // 目标QQ
#   'verify_key'        : str,          // 验证key
#   'websocket'         : websocket,    // 链接WebSocket实例
#   'session'           : str,          // 链接Session
#   'state'             : str,          // 连接状态，'None' | 'Opening' | 'Opened' | 'Failed' | 'Closing' | 'Closed'
#   'sync_id'           : int,          // 同步号
#
#   # 消息队列
#   'buffer_size'       : int = 1024,           // 缓存大小
#   'send'              : dict[syncId]{msg},    // 待发送的消息队列
#   'sending'           : dict[syncId]{msg},    // 发送但未收到回复的消息队列
#   'failed'            : dict[syncId]{msg},    // 发送超时的消息队列
#   'succed'            : dict[syncId]{msg},    // 发送反馈的消息队列
#   'recv'              : list[msg]             // 接受后待处理的消息队列
# }


# messagemanager = new()
# 初始化一个messagemanager
def new(
    remote_host         : str = 'localhost:8080',
    timeout             : float = 3,
    verify_qq           : str = '',
    verify_key          : str = 'INITKEYxxxxxxxx'
    ):
    mm = {
        'remote_host'   : remote_host,
        'timeout'       : timeout,
        'verify_qq'     : verify_qq,
        'verify_key'    : verify_key,
        'websocket'     : ws.WebSocket(),
        'session'       : '',
        'state'         : 'None',
        'sync_id'       : -1,
        'send'          : [],
        'sending'       : [],
        'failed'        : [],
        'recv'          : []
    }
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager建立连接并验证连接状态
def open(mm):

    logger.info('Opening');
    mm['state'] = 'Opening';

    _uri = 'ws://' + mm['remote_host'] + '/message?' + 'verifyKey=' + mm['verify_key'] + '&qq=' + mm['verify_qq'];
    mm['websocket'].connect(_uri, timeout = mm['timeout']);
    mm['websocket'].settimeout(0);
    _recv = mm['websocket'].recv();
    _auth = json.loads(_recv);
    mm['state_code'] = _auth['data']['code'];
    if mm['state_code'] == 0:
        logger.info('Log in success');
        mm['session'] = _auth['data']['session'];
        mm['state'] = 'Opened';
    else:
        logger.info('Log in failed with code: %d' % mm['state_code']);
        mm['state'] = 'Failed';
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager关闭连接
def close(mm):
    logger.info('Closing');
    mm['state'] = 'Closing';
    mm['websocket'].close(timeout = mm['timeout']);
    mm['state'] = 'Closed';
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager进行一次接收轮询
def recv(mm):
    _frame = mm['websocket'].recv_frame();
    if _frame:
        if _frame.opcode in {wsabnf.ABNF.OPCODE_TEXT, wsabnf.ABNF.OPCODE_BINARY, wsabnf.ABNF.OPCODE_CONT}:
            mm['websocket'].cont_frame.validate(_frame);
            mm['websocket'].cont_frame.add(_frame);
            if mm['websocket'].cont_frame.is_fire(_frame):
                _opcode, _recv = mm['websocket'].cont_frame.extract(_frame);
                if _opcode in {wsabnf.ABNF.OPCODE_TEXT}:
                    try:
                        _data = json.loads(_recv);
                        if _data['syncId'] in {None, '', '-1', -1}:
                            mm['recv'].append(_data);
                        else:
                            mm['sending'].pop(int(_data['syncId']));
                            mm['succed']['syncId'] = _data;
                    except:
                        logger.error('Invalid text frame');
                else:
                    logger.error('Invalid binary frame');
        
        elif _frame.opcode in {wsabnf.ABNF.OPCODE_CLOSE}:
            logger.info('Closing');
            mm['status'] = 'Closing';
            mm['websocket'].send_close();
            mm['status'] = 'Closed';
        elif _frame.opcode in {wsabnf.ABNF.OPCODE_PING}:
            if len(_frame.data) < 126:
                logger.info('Recv ping');
                logger.info('Send pong');
                mm['websocket'].pong(_frame.data)
            else:
                logger.error('Invalid ping');
        elif _frame.opcode in {wsabnf.ABNF.OPCODE_PONG}:
                logger.info('Recv pong');
    else:
        logger.error('Invalid frame %s' % _frame);
    
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager的发送队列进行处理
def send(mm):
    while len(mm['send']) > 0:
        _data = mm['send'].pop();
        mm['sending'][_data['syncId']] = _data;
        _send = json.dumps(_data, ensure_ascii = False);
        mm['websocket'].send(_send);
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager的缓存消息维护缓存大小
def trim(mm):

    _len = len(mm['sending']);
    _k = iter(mm['sending'].keys());
    _dekey = [next(_k) for _i in range(_len - mm['buffer_size'])];
    for _k in _dekey:
        _d = mm['sending'].pop(_k);
        mm['failed'][_k] = _d;
    
    _len = len(mm['failed']);
    _k = iter(mm['failed'].keys());
    _dekey = [next(_k) for _i in range(_len - mm['buffer_size'])];
    for _k in _dekey: mm['failed'].pop(_k);

    _len = len(mm['succed']);
    _k = iter(mm['succed'].keys());
    _dekey = [next(_k) for _i in range(_len - mm['buffer_size'])];
    for _k in _dekey: mm['succed'].pop(_k);

    mm['recv'] = mm['recv'][ -mm['buffer_size'] : ];

    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager进行一次标准轮询，包括接受轮询，发送队列处理，缓存清理
def update(mm):
    if mm['state'] == 'Opened':
        mm = recv(mm);
        mm = send(mm);
        mm = trim(mm);
    return mm;

# messagemanager = open(messagemanager)
# 对一个messagemanager的接收队列pop一个元素，无消息返回None
def pop(mm):
    if len(mm['recv']) > 0:
        data = mm['recv'].pop(0);
    else:
        data = None;
    return mm, data;

# messagemanager = open(messagemanager)
# 对一个messagemanager的反馈队列pop一个元素，无消息返回None
def ans(mm, syncid):
    if syncid in mm['succed']:
        data = mm['succed'].pop(syncid);
    else:
        data = None;
    return mm, data;

# messagemanager = open(messagemanager)
# 对一个messagemanager的发送队列push一个元素
def push(mm, data):
    if mm['state'] == 'Opened':
        data['syncId'] = mm['sync_id'];
        data['data']['sessionKey'] = mm['session'];
        mm['sync_id'] += 1;
        return mm, data['syncId'];
    else:
        return mm, -1;
