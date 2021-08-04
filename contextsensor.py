
import jieba;
import jieba.analyse;
import jieba.posseg;
import time;

# contextsensor         : dict
# {
#   topicdim            : int,          // 话题维度，话题应当由context做向量运算得到
#   contextwin          : int,          // 话题时间窗，维护context的队列
#   context[<key>]      : dict          // context的队列，需要用键值访问，每次访问对某个键值进行更新计算
#   [
#       <key>           : str           // context键值，为一个关键词
#       {
#           'v'         : float,        // 关键词的时间浓度，冲激响应模型为 v(t) = u(t) * exp(-alpha * t / tau)
#           't'         : int           // 上次更新计算的时间
#       }
#   ]
# }

def new(topicdim: int = 32, contextwin: int = 60000):
    _contextsensor = {
        'topicdim': topicdim,
        'contextwin': contextwin,
        'context':dict(),
        'topic': [dict() for _ in range(topicdim)]
    };
    return _contextsensor();

def push(cs: dict, msg: str = '', t: int = None):
    if t == None:
        t = time.time();
    _keys = jieba.analyse.textrank(msg, topK = 3, withWeight = True, allowPOS = ('n', 'nr', 'ns', 'nt', 'nw', 'vn', 'v'));
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
    _contexts = cs['context'].keys();
    _i = 0;
    while _i < len(_contexts) and t - cs['context'][_contexts[_i]] > cs['contextwin']:
        cs['context'].pop(_contexts[_i]);
        _i += 1;
    return;

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

