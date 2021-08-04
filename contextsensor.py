
import jieba;
import jieba.analyse;
import jieba.posseg;
import logging
import time;

VERSION = 'v20210804';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Sentence Generator Loaded');

# contextsensor         : dict
# {
#   topicdim            : int,          // 话题维度，话题应当由context做向量运算得到
#   contextwin          : float,        // 话题时间窗，维护context的队列，单位s
#   context[<key>]      : dict          // context的队列，需要用键值访问，维护按照加入时间的队列顺序
#   [
#       <key>:          : str           // context键值，为一个关键词
#       {
#           'v'         : float,        // 关键词的时间浓度，冲激响应模型为 v(t) = u(t) * exp(-alpha * t / tau)
#           't'         : float         // 上次最新加入队列的时间，time.time()的时间戳
#       }
#   ],
#   topics[]            : list          // topic的向量表
#   [
#       vector[<key>]   : dict          // 单个topic的特征向量
#       [
#           {
#               'sum'                   : float,                // vector的sum
#               'vec'[<key>]            : dict{float}           // vector，用dict来实现稀疏输入的向量乘法
#           }
#       ]
#   ]
# }

def new(topicdim: int = 32, contextwin: int = 60):
    _contextsensor = {
        'topicdim': topicdim,
        'contextwin': contextwin,
        'context':dict(),
        'topics': [{'sum' : 0, 'vec' : dict()} for _ in range(topicdim)]
    };
    return _contextsensor;

def push(cs: dict, msg: str = '', t: int = None):
    if t == None:
        t = time.time();
    #_keys = jieba.analyse.textrank(msg, topK = 3, withWeight = True, allowPOS = ('n', 'nr', 'ns', 'nt', 'nw', 'vn', 'v'));
    _keys = jieba.analyse.extract_tags(msg, topK = 3, withWeight = True, allowPOS = ('n', 'nr', 'ns', 'nt', 'nw', 'vn', 'v'));
    for _k, _w in _keys:
        if _k in cs['context']:
            _q = cs['context'].pop(_k);
            _q['v'] = _q['v'] * pow(2, (_q['t'] - t) / cs['contextwin']) + _w;
            _q['t'] = t;
            cs['context'][_k] = _q;
        else:
            _q = dict();
            _q['v'] = _w;
            _q['t'] = t;
            cs['context'][_k] = _q;
    _contexts = list(cs['context'].keys());
    _i = 0;
    while _i < len(_contexts) and t - cs['context'][_contexts[_i]]['t'] > cs['contextwin']:
        cs['context'].pop(_contexts[_i]);
        _i += 1;
    return cs;

def gettopics(cs: dict, t: int = None):
    if t == None:
        t = time.time();
    return [0] * cs['topicdim'];

def gettopic(cs: dict, t: int = None):
    if t == None:
        t = time.time();
    return -1;

def updatetopic(cs: dict, tid: int = None, t: int = None):
    if t == None:
        t = time.time();
    if tid == None:
        tid = gettopic(cs, t);

