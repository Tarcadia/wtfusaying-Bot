
import jieba;
import jieba.analyse;
import jieba.posseg;
import logging;
import time;

VERSION = 'v20210804';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Context Sensor Loaded');

# contextsensor         : dict
# {
#   contextcout         : int,          // 单条语句的预期提取最多关键词个数，jieba.analyse中tag提取的topK参数
#   contextfilter       : tuple,        // 单条语句的关键词词性过滤，jieba.analyse中tag提取的filter参数
#   contextmethod       : str,          // 单条语句的关键词提取方式，决定jieba的tag提取方式，或者直接采用分词结果，tfidf | tr | all
#   contextwei          : bool,         // 单条语句的关键词在context中的引入值方式，决定冲激响应的高度，true表示引入分词时的weight，false则采用1，直接分词时该参数不起作用而采用1
#   tau                 : float,        // 语境时间窗，维护context的队列，超时出队，同时也是语境单位时间tau，单位s
#   alpha               : float,        // 语境衰减系数alpha
#   context[<key>]      : dict          // context的队列，需要用键值访问，维护按照加入时间的队列顺序
#   [
#       <key>:          : str           // context键值，为一个关键词
#       {
#           'v'         : float,        // 关键词的浓度，冲激响应模型为 v(t) = u(t) * exp(-alpha * t / tau)
#           't'         : float         // 上次最新加入队列的时间，time.time()的时间戳
#       }
#   ]
# }

# contextvec[<key>:str]{float}  : dict      // context向量，为稀疏的float类型向量，键值为一个关键词
# contextvec{<key>:str}         : set       // context向量的化简，为稀疏的元素值为1的向量，为有元素的关键词的集合
# contextvec[<key>:str]         : list      // context向量的化简，为稀疏的元素值为1的向量，为有元素的关键词的列表


# contextsensor = new()
# 初始化一个contextsensor
def new(
    contextcount        : int   = 20,
    contextfilter       : tuple = ('n', 'nr', 'ns', 'nt', 'nw', 'vn', 'v', 'eng'),
    contextmethod       : str   = 'tfidf',
    contextwei          : bool  = False,
    tau                 : float = 360,
    alpha               : float = 1
    ):
    _contextsensor = {
        'contextcount'  : contextcount,
        'contextfilter' : contextfilter,
        'contextmethod' : contextmethod,
        'contextwei'    : contextwei,
        'tau'           : tau,
        'alpha'         : alpha,
        'context'       : dict()
    };
    return _contextsensor;

# contextsensor = clearcontext(contextsensor)
# 清除context
def clear(cs: dict):
    cs['context'] = dict();
    return cs;

# contextvec = contextvector(contextsensor, time)
# 在time时刻获取context向量，不对context中的超时项目进行pop
# time时刻默认为调用时刻
def get(cs: dict, t: float = None):

    if t == None:
        t = time.time();
    
    _v = {_k : cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['tau']) for _k in cs['context']};
    return _v;

# contextsensor = pop(contextsensor, time)
# 在time时刻对context中的超时项目进行pop
# time时刻默认为调用时刻
def pop(cs: dict, t: float = None):

    if t == None:
        t = time.time();
    
    _keys = list(cs['context'].keys());
    _i = 0;
    while _i < len(_keys) and t - cs['context'][_keys[_i]]['t'] > cs['tau']:
        cs['context'].pop(_keys[_i]);
        _i += 1;
    return cs;

# contextsensor = push(contextsensor, contextvec, time)
# 在time时刻向contextsensor中加入一条message
# 将会将message提取出tag加入context队列
# time时刻默认为调用时刻
def push(cs: dict, vec: dict or set or list = dict(), t: float = None):
    
    if t == None:
        t = time.time();
    
    if type(vec) == dict:
        for _key in vec:
            if _key in cs['context']:
                _q = cs['context'].pop(_key);
                _q['v'] = _q['v'] * pow(2, cs['alpha'] * (_q['t'] - t) / cs['tau']) + vec[_key];
                _q['t'] = t;
                cs['context'][_key] = _q;
            else:
                _q = dict();
                _q['v'] = vec[_key];
                _q['t'] = t;
                cs['context'][_key] = _q;
    
    elif type(vec) == set or type(vec) == list:
        for _key in vec:
            if _key in cs['context']:
                _q = cs['context'].pop(_key);
                _q['v'] = _q['v'] * pow(2, cs['alpha'] * (_q['t'] - t) / cs['tau']) + 1;
                _q['t'] = t;
                cs['context'][_key] = _q;
            else:
                _q = dict();
                _q['v'] = 1;
                _q['t'] = t;
                cs['context'][_key] = _q;
    return cs;

# contextsensor = update(contextsensor, message, time)
# 在time时刻向contextsensor中加入一条message
# 将会将message提取出tag加入context队列，并更新context队列，pop超时元素
# time时刻默认为调用时刻
def update(cs: dict, msg: str = '', t: float = None):
    if t == None:
        t = time.time();
    
    if cs['contextmethod'] == 'all':
        _vec = jieba.cut(msg);
    elif cs['contextmethod'] == 'tr':
        if cs['contextwei']:
            _kw = jieba.analyse.textrank(msg, topK = cs['contextcount'], withWeight = True, allowPOS = cs['contextfilter']);
            _vec = {_k : _w for _k, _w in _kw};
        else:
            _vec = jieba.analyse.textrank(msg, topK = cs['contextcount'], withWeight = False, allowPOS = cs['contextfilter']);
    elif cs['contextmethod'] == 'tfidf':
        if cs['contextwei']:
            _kw = jieba.analyse.extract_tags(msg, topK = cs['contextcount'], withWeight = True, allowPOS = cs['contextfilter']);
            _vec = {_k : _w for _k, _w in _kw};
        else:
            _vec = jieba.analyse.extract_tags(msg, topK = cs['contextcount'], withWeight = False, allowPOS = cs['contextfilter']);
    else:
        _keys = {};
    
    cs = push(cs, _vec, t);
    cs = pop(cs, t);
    return cs;
