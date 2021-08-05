
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
#   contextwin          : float,        // 语境时间窗，维护context的队列，单位s
#   contextcout         : int,          // 单条语句的预期提取关键词个数
#   contextfilter       : tuple,        // 单条语句的关键词词性过滤
#   contextmethod       : str,          // 单条语句的关键词提取方式，tfidf | tr | all
#   alpha               : float,        // 语境衰减系数
#   context[<key>]      : dict          // context的队列，需要用键值访问，维护按照加入时间的队列顺序
#   [
#       <key>:          : str           // context键值，为一个关键词
#       {
#           'v'         : float,        // 关键词的时间浓度，冲激响应模型为 v(t) = u(t) * exp(-alpha * t / tau)
#           't'         : float         // 上次最新加入队列的时间，time.time()的时间戳
#       }
#   ],
#   topics[]            : list{dict}    // topic的向量表
#   [
#       {
#           'sum'                       : float,                // 特征向量的和
#           'vec'[<key>]                : dict{float}           // 单个topic的特征向量，用dict来实现稀疏输入的向量乘法
#       }
#   ]
# }

# contextsensor = new()
# 初始化一个contextsensor
def new(
    topicdim: int = 32,
    contextwin: float = 60,
    contextcout: int = 20,
    contextfilter = ('n', 'nr', 'ns', 'nt', 'nw', 'vn', 'v', 'eng'),
    contextmethod = 'tfidf',
    alpha: float = 1
    ):
    _contextsensor = {
        'topicdim'      : topicdim,
        'contextwin'    : contextwin,
        'contextcount'  : contextcout,
        'contextfilter' : contextfilter,
        'contextmethod' : contextmethod,
        'alpha'         : alpha,
        'context'       : dict(),
        'topics'        : [{'sum' : 0, 'vec' : dict()} for _ in range(topicdim)]
    };
    return _contextsensor;

# contextsensor = clearcontext(contextsensor)
# 清除context，可以在原topic基础上继续操作
def clearcontext(cs: dict):
    cs['context'] = dict();
    return cs;

# contextsensor = addtopic(contextsensor, topicvec)
# 写入一条特定的topic，或多条空topic
# 该topic也会参与后续的update
def addtopic(cs: dict, vec: dict, count: int = 1):
    if type(vec) == dict and not vec == dict():
        _topic = {
            'sum'       : sum([vec[_k] for _k in vec]),
            'vec'       : vec
        };
        cs['topicdim'] += 1;
        cs['topics'].append(_topic);
    elif (type(vec) == list or type(vec) == set) and not (vec == [] or vec == {}):
        _topic = {
            'sum'       : len(vec),
            'vec'       : {_k : 1 for _k in vec}
        };
        cs['topicdim'] += 1;
        cs['topics'].append(_topic);
    elif vec == dict() or vec == list() or vec == set():
        for _i in range(count):
            _topic = {
                'sum'   : 0,
                'vec'   : dict()
            };
            cs['topics'].append(_topic);
        cs['topicdim'] += count;
    return cs;

# contextsensor = push(contextsensor, message, time)
# 在time时刻向contextsensor中加入一条message
# 将会将message提取出tag加入context队列
def push(cs: dict, msg: str = '', t: int = None):
    if t == None:
        t = time.time();
    if cs['contextmethod'] == 'all':
        _keys_k = jieba.cut(msg);
        _keys = [(_k, 1) for _k in _keys_k];
    elif cs['contextmethod'] == 'tr':
        _keys = jieba.analyse.textrank(msg, topK = cs['contextcount'], withWeight = True, allowPOS = cs['contextfilter']);
    elif cs['contextmethod'] == 'tfidf':
        _keys = jieba.analyse.extract_tags(msg, topK = cs['contextcount'], withWeight = True, allowPOS = cs['contextfilter']);
    else:
        _keys = [];
    for _k, _w in _keys:
        if _k in cs['context']:
            _q = cs['context'].pop(_k);
            _q['v'] = _q['v'] * pow(2, cs['alpha'] * (_q['t'] - t) / cs['contextwin']) + _w;
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

# topicvector = topic(contextsensor, time)
# 在time时刻对context向量求与topic特征向量相关性
# 计算得到topic空间上的向量组
def topics(cs: dict, t: int = None):
    if t == None:
        t = time.time();
    _result = [];
    for _topic in cs['topics']:
        _v = 0;
        _s = 0;
        for _k in cs['context']:
            if _k in _topic['vec']:
                _v += cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']) * _topic['vec'][_k];
        if _topic['sum'] == 0:
            _result.append(1);
        else:
            _result.append(_v / _topic['sum']);
    return _result;

# tid = topic(contextsensor, time)
# 在time时刻计算得到当前的topic的估计
# 多个并列则返回第一个
def topic(cs: dict, t: int = None):
    if t == None:
        t = time.time();
    _topics = topics(cs, t);
    return _topics.index(max(_topics));

# contextsensor = updatetopic(contextsensor, tid, time)
# 在time时刻监督学习contextsensor的topic符合tid所指的topic
# 在time时刻将contextsensor的context向量加入tid所指的topic的特征向量中
# 维护topic的特征向量的sum
def updatetopic_ver1(cs: dict, tid: int = None, t: int = None):
    if t == None:
        t = time.time();
    if tid == None:
        tid = topic(cs, t);
    elif tid == -1:
        return cs;
    _contexts = list(cs['context'].keys());
    _i = 0;
    while _i < len(_contexts) and t - cs['context'][_contexts[_i]]['t'] > cs['contextwin']:
        cs['context'].pop(_contexts[_i]);
        _i += 1;
    _s = 0;
    for _k in cs['context']:
        if _k in cs['topics'][tid]['vec']:
            cs['topics'][tid]['vec'][_k] += cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
            _s += cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
        else:
            cs['topics'][tid]['vec'][_k] = cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
            _s += cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
    cs['topics'][tid]['sum'] += _s;
    return cs;

# contextsensor = updatetopic(contextsensor, tid, time)
# 在time时刻监督学习contextsensor的topic符合tid所指的topic
# 在time时刻将contextsensor的context向量加入tid所指的topic的特征向量中
# 维护topic的特征向量的sum
def updatetopic_ver2(cs: dict, tid: int = None, t: int = None):
    if t == None:
        t = time.time();
    if tid == None:
        tid = topic(cs, t);
    elif tid == -1:
        return cs;
    _contexts = list(cs['context'].keys());
    _i = 0;
    while _i < len(_contexts) and t - cs['context'][_contexts[_i]]['t'] > cs['contextwin']:
        cs['context'].pop(_contexts[_i]);
        _i += 1;
    _topics = topics(cs, t);
    for _tid in range(cs['topicdim']):
        if _tid == tid:
            _p = _topics[_tid] + 1;
        else:
            _p = - _topics[_tid];
        _s = 0;
        for _k in cs['context']:
            if _k in cs['topics'][_tid]['vec']:
                cs['topics'][_tid]['vec'][_k] += _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
                _s += _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
            else:
                cs['topics'][_tid]['vec'][_k] = _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
                _s += _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
        cs['topics'][_tid]['sum'] += _s;
    return cs;

# contextsensor = updatetopic(contextsensor, tid, time)
# 在time时刻监督学习contextsensor的topic符合tid所指的topic
# 在time时刻将contextsensor的context向量加入tid所指的topic的特征向量中
# 维护topic的特征向量的sum
def updatetopic(cs: dict, tid: int = None, t: int = None):
    if t == None:
        t = time.time();
    if tid == None:
        tid = topic(cs, t);
    elif tid == -1:
        return cs;
    _contexts = list(cs['context'].keys());
    _i = 0;
    while _i < len(_contexts) and t - cs['context'][_contexts[_i]]['t'] > cs['contextwin']:
        cs['context'].pop(_contexts[_i]);
        _i += 1;
    _topics = topics(cs, t);
    for _tid in range(cs['topicdim']):
        if _tid == tid:
            _p = _topics[_tid] + 3;
        else:
            _p = - _topics[_tid];
        _s = 0;
        for _k in cs['context']:
            if _k in cs['topics'][_tid]['vec']:
                cs['topics'][_tid]['vec'][_k] += _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
                _s += _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
            else:
                cs['topics'][_tid]['vec'][_k] = _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
                _s += _p * cs['context'][_k]['v'] * pow(2, cs['alpha'] * (cs['context'][_k]['t'] - t) / cs['contextwin']);
        cs['topics'][_tid]['sum'] += _s;
    return cs;

