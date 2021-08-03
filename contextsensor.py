from botcontrol import PATH_CONFIG
import jieba;
import jieba.analyse;
import jieba.posseg;
import time;

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
    while t - cs['context'][next(iter(cs['context']))] > cs['contextwin']:
        cs['context'].pop(next(iter(cs['context'])));
    # 好丑
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

