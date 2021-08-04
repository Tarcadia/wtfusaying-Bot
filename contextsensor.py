
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

# contextsensor = new()
# 初始化一个contextsensor
def new(topicdim: int = 32, contextwin: int = 60):
    _contextsensor = {
        'topicdim': topicdim,
        'contextwin': contextwin,
        'context':dict(),
        'topics': [{'sum' : 0, 'vec' : dict()} for _ in range(topicdim)]
    };
    return _contextsensor;

# contextsensor = push(contextsensor, message, time)
# 在time时刻向contextsensor中加入一条message
# 将会将message提取出tag加入context队列
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
                _v += cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']) * _topic['vec'][_k];
                _s += cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']);
            else:
                _s += cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']);
        if _s == 0:
            _result.append(0);
        elif _topic['sum'] == 0:
            _result.append(1);
        else:
            _result.append(_v / _s / _topic['sum']);
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
def updatetopic(cs: dict, tid: int = None, t: int = None):
    if t == None:
        t = time.time();
    if tid == None:
        tid = topic(cs, t);
    elif tid == -1:
        return cs;
    _s = 0;
    for _k in cs['context']:
        if _k in cs['topics'][tid]['vec']:
            cs['topics'][tid]['vec'][_k] += cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']);
            _s += cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']);
        else:
            cs['topics'][tid]['vec'][_k] = cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']);
            _s += cs['context'][_k]['v'] * pow(2, (cs['context'][_k]['t'] - t) / cs['contextwin']);
    cs['topics'][tid]['sum'] += _s;
    return cs;

