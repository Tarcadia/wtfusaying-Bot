
import math;
import json
from operator import mul;
import os;
import logging

VERSION = 'v20210807';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Topic Sensor Loaded');

# topicsensor           : dict
# {
#   memorypath          : str,          // 数据存储的路径，应当保证文件的可访问性以实现定期的数据存储
#   recyclepath         : str,          // 数据回收站的路径，应当保证文件的可访问性以实现定期的数据存储
#   topiccount          : int           // topic的个数
#   topics[]            : list[]{dict}  // topic向量的列表
#   [
#       {
#           sum         : float,        // 特征向量的和的维护
#           sqs         : float,        // 特征向量的平方和的维护
#           cnt         : int,          // 特征向量的累加的维护
#           bia         : float,        // 特征向量的偏移
#           vec[<key>]  : dict{float}   // topic向量，用dict来实现稀疏下的计算，应当是未正规化或归一化的
#       }
#   ]
# }

# vector[<key>:str]{float}      : dict          // 一般是context向量，为稀疏的float类型向量，键值为一个关键词
# vector{<key>:str}             : set           // vector的化简，为稀疏的元素值为1的向量，为有元素的关键词的集合
# vector[<key>:str]             : list          // vector的化简，为稀疏的元素值为1的向量，为有元素的关键词的列表



# topicsensor = new()
# 初始化一个topicsensor
def new(
    memorypath          : str   = '',
    recyclepath         : str   = '',
    topiccount          : int   = 32
    ):

    _topicsensor = {
        'memorypath'    : memorypath,
        'recyclepath'    : recyclepath,
        'topiccount'    : 0,
        'topics'        : []
    };

    if memorypath == '' or not os.path.isfile(memorypath):
        for _i in range(topiccount):
            _topic = {
                'sum'       : 0,
                'sqs'       : 0,
                'cnt'       : 0,
                'bia'       : 0,
                'vec'       : dict()
            };
            _topicsensor['topics'].append(_topic);
        _topicsensor['topiccount'] = topiccount;
    
    elif os.path.isfile(memorypath):
        _fp = open(memorypath, mode = 'r', encoding = 'utf-8');
        _topics = json.load(_fp);
        _fp.close();
        _topicsensor['topiccount'] = len(_topics);
        _topicsensor['topics'] = _topics;

    return _topicsensor;

# topicsensor = load(topicsensor)
# 为topicsensor进行一次文件加载
def load(ts):
    if os.path.isfile(ts['memorypath']):
        _fp = open(ts['memorypath'], mode = 'r', encoding = 'utf-8');
        _topics = json.load(_fp);
        _fp.close();
        ts['topiccount'] = len(_topics);
        ts['topics'] = _topics;
    return ts;

# save(topicsensor)
# 为topicsensor进行一次文件保存
def save(ts):
    _fp = open(ts['memorypath'], mode = 'w', encoding = 'utf-8');
    json.dump(ts['topics'], _fp, ensure_ascii = False, indent = 4);
    _fp.close();
    return ts;

# topicsensor = extend(topicsensor, n)
# 将topicsensor的topic清空
def clear(ts: dict):
    ts['topics'] = [];
    for _i in range(ts['topiccount']):
        _topic = {
            'sum'       : 0,
            'sqs'       : 0,
            'cnt'       : 0,
            'bia'       : 0,
            'vec'       : dict()
        };
        ts['topics'].append(_topic);
    return ts;

# topicsensor = extend(topicsensor, n)
# 将topicsensor的topic增加n
def extend(ts: dict, n: int):
    for _i in range(n):
        _topic = {
            'sum'       : 0,
            'sqs'       : 0,
            'cnt'       : 0,
            'bia'       : 0,
            'vec'       : dict()
        };
        ts['topics'].append(_topic);
    return ts;

# topicsensor = extend(topicsensor, n)
# 将topicsensor中tid所指的topic放入回收站
def waste(ts: dict, tid: int):
    _topic = ts['topics'].pop(tid);

    if os.path.isfile(ts['recyclepath']):

        _fp = open(ts['recyclepath'], mode = 'r', encoding = 'utf-8');
        _topics = json.load(_fp);
        _fp.close();

        _topics.append(_topic);

        _fp = open(ts['recyclepath'], mode = 'w', encoding = 'utf-8');
        json.dump(_topics, _fp, ensure_ascii = False, indent = 4);
        _fp.close();

    else:
        _fp = open(ts['recyclepath'], mode = 'w', encoding = 'utf-8');
        json.dump([_topic], _fp, ensure_ascii = False, indent = 4);
        _fp.close();

    return ts;

# topicsensor = add(topicsensor, tid, k, vec)
# 为编号为tid的topic累加入一个k倍的vector
def add(ts: dict, tid: int, k: float = 1, vec:dict or set or list = dict()):
    if type(vec) == dict:
        _dsum = 0;
        _dsqs = 0;
        _dcnt = 1;
        for _k in vec:
            if _k in ts['topics'][tid]['vec']:
                _dsum += k * vec[_k];
                _dsqs += 2 * k * vec[_k] * ts['topics'][tid]['vec'][_k] + k * k * vec[_k] * vec[_k];
                ts['topics'][tid]['vec'][_k] += k * vec[_k];
            else:
                _dsum += k * vec[_k];
                _dsqs += k * k * vec[_k] * vec[_k];
                ts['topics'][tid]['vec'][_k] = vec[_k];
        ts['topics'][tid]['sum'] += _dsum;
        ts['topics'][tid]['sqs'] += _dsqs;
        ts['topics'][tid]['cnt'] += _dcnt;

    elif type(vec) == set or type(vec) == list:
        _dsum = 0;
        _dsqs = 0;
        _dcnt = 1;
        for _k in vec:
            if _k in ts['topics'][tid]['vec']:
                _dsum += k;
                _dsqs += 2 * k * ts['topics'][tid]['vec'][_k] + k * k;
                ts['topics'][tid]['vec'][_k] += k;
            else:
                _dsum += k;
                _dsqs += k * k;
                ts['topics'][tid]['vec'][_k] = k;
        ts['topics'][tid]['sum'] += _dsum;
        ts['topics'][tid]['sqs'] += _dsqs;
        ts['topics'][tid]['cnt'] += _dcnt;

    return ts;

# topicsensor = multime(topicsensor, tid, k)
# 为编号为tid的topic乘上一个k，cnt不变
def multime(ts: dict, tid: int, k: float):
    for _k in ts['topics'][tid]['vec']:
        ts['topics'][tid]['vec'][_k] *= k;
    ts['topics'][tid]['sum'] *= k;
    ts['topics'][tid]['sqs'] *= k * k;
    ts['topics'][tid]['bia'] *= k;

    return ts;
    
# topicsensor = shrink(topicsensor, tid, k)
# 为编号为tid的topic规模减小至cntx，即乘上一个cntx / cnt，cnt更新
# 用于在topic规模过大时缩减规模
def shrink(ts: dict, tid: int, cntx: int):
    kx = cntx / ts['topics'][tid]['cnt'];
    for _k in ts['topics'][tid]['vec']:
        ts['topics'][tid]['vec'][_k] *= kx;
    ts['topics'][tid]['sum'] *= kx;
    ts['topics'][tid]['sqs'] *= kx * kx;
    ts['topics'][tid]['bia'] *= kx;
    ts['topics'][tid]['cnt'] = cntx;
    return ts;

# topicsensor = unify(topicsensor, tid)
# 为编号为tid的topic归一化
# 用于在topic规模过大时缩减规模
def unify(ts: dict, tid: int):
    _sqs = sum([ts['topics'][tid]['vec'][_k] * ts['topics'][tid]['vec'][_k] for _k in ts['topics'][tid]['vec']]);
    ts['topics'][tid]['vec'] = [ts['topics'][tid]['vec'][_k] * math.sqrt(_sqs) for _k in ts['topics'][tid]['vec']];
    ts['topics'][tid]['sum'] = sum([ts['topics'][tid]['vec'][_k] for _k in ts['topics'][tid]['vec']]);
    ts['topics'][tid]['sqs'] = sum([ts['topics'][tid]['vec'][_k] * ts['topics'][tid]['vec'][_k] for _k in ts['topics'][tid]['vec']]);
    ts['topics'][tid]['cnt'] = 1;
    ts['topics'][tid]['bia'] *= math.sqrt(_sqs);
    return ts;

# topicsensor = pick(topicsensor, tid, n)
# 筛选保留topic的前n个关键词
# 或筛选保留topic的模的前k比例的关键词，|v[0:n]| / |v| <= k，保障第一个关键词
# cnt不变，bia等sum比例缩放
# 用于在topic规模过大时缩减规模
def pick(ts: dict, tid: int, n: int = None, k: float = None):
    if n != None and k == None:
        _kw = sorted(ts['topics'][tid]['vec'].items(), key = lambda x : x[1], reverse = True);
        _vec = {_k : _w for _k, _w in _kw[0 : min(len(_kw), n)]};
        _sum = sum([_w for _k, _w in _kw[0 : min(len(_kw), n)]]);
        _sqs = sum([_w * _w for _k, _w in _kw[0 : min(len(_kw), n)]]);
        _bia = ts['topics'][tid]['bia'] * _sum / ts['topics'][tid]['sum'];
        ts['topics'][tid]['vec'] = _vec;
        ts['topics'][tid]['sum'] = _sum;
        ts['topics'][tid]['sqs'] = _sqs;
        ts['topics'][tid]['bia'] = _bia;
        return ts;
    elif n == None and k != None:
        _kw = sorted(ts['topics'][tid]['vec'].items(), key = lambda x : x[1], reverse = True);
        _wq = [_w * _w for _k, _w in _kw];
        _cumwq = [sum(_wq[0 : _i + 1]) for _i in range(len(_wq))];
        _ks = [_i for _i in range(len(_cumwq)) if math.sqrt(_cumwq[_i]) / math.sqrt(sum(_wq)) <= k];
        _vec = {_kw[_i][0] : _kw[_i][1] for _i in _ks};
        _sum = sum([_kw[_i][1] for _i in _ks]);
        _sqs = sum([_kw[_i][1] * _kw[_i][1] for _i in _ks]);
        _bia = ts['topics'][tid]['bia'] * _sum / ts['topics'][tid]['sum'];
        ts['topics'][tid]['vec'] = _vec;
        ts['topics'][tid]['sum'] = _sum;
        ts['topics'][tid]['sqs'] = _sqs;
        ts['topics'][tid]['bia'] = _bia;
        return ts;
    elif n != None and k != None:
        _kw = sorted(ts['topics'][tid]['vec'].items(), key = lambda x : x[1], reverse = True);
        _wq = [_w * _w for _k, _w in _kw];
        _cumwq = [sum(_wq[0 : _i + 1]) for _i in range(len(_wq))];
        _ks = list(range(min(n, len(_cumwq)))) + [_i for _i in range(n, len(_cumwq)) if math.sqrt(_cumwq[_i]) / math.sqrt(sum(_wq)) <= k];
        _vec = {_kw[_i][0] : _kw[_i][1] for _i in _ks};
        _sum = sum([_kw[_i][1] for _i in _ks]);
        _sqs = sum([_kw[_i][1] * _kw[_i][1] for _i in _ks]);
        _bia = ts['topics'][tid]['bia'] * _sum / ts['topics'][tid]['sum'];
        ts['topics'][tid]['vec'] = _vec;
        ts['topics'][tid]['sum'] = _sum;
        ts['topics'][tid]['sqs'] = _sqs;
        ts['topics'][tid]['bia'] = _bia;
        return ts;

# topicsensor = repara(topicsensor, tid)
# 遍历更新sum，sqs等维护参数
# 用于在topic多次更新后消除误差
def repara(ts: dict, tid: int, n: int):
    ts['topics'][tid]['sum'] = sum([ts['topics'][tid]['vec'][_k] for _k in ts['topics'][tid]['vec']]);
    ts['topics'][tid]['sqs'] = sum([ts['topics'][tid]['vec'][_k] * ts['topics'][tid]['vec'][_k] for _k in ts['topics'][tid]['vec']]);
    return ts;

# vector = norm(vector)
# 对vector进行归一化
def norm(vec: dict or set or list):
    if type(vec) == set or type(vec) == list:
        vec = {_k : 1 for _k in vec};
    _sqs = sum([vec[_k] * vec[_k] for _k in vec]);
    if _sqs != 0:
        vec = {_k : vec[_k] / math.sqrt(_sqs) for _k in vec};
    else:
        vec = {_k : 0 for _k in vec};
    return vec;

# vector = topic(topicsensor, tid)
# 返回tid所指的topic的vector形式
def topic(ts: dict, tid: int):
    _vec = ts['topics'][tid]['vec'];
    return norm(_vec);

# vector = keywords(topicsensor, tid)
# 返回tid所指的topic的前n个关键词
def keywords(ts: dict, tid: int, n: int):
    _kw = sorted(ts['topics'][tid]['vec'].items(), key = lambda x : x[1], reverse = True)
    _keys = [_k for _k, _w in _kw[0 : min(len(_kw), n)]];
    return _keys;

# v = mult(topicsensor, tid, vector)
# 计算vector与tid所指的topic的内积
def mult(ts: dict, tid: int, vec: dict or set or list):
    if type(vec) == set or type(vec) == list:
        vec = {_k : 1 for _k in vec};
    _s = sum([ts['topics'][tid]['vec'][_k] * vec[_k] for _k in vec if _k in ts['topics'][tid]['vec']]);
    if ts['topics'][tid]['sqs'] != 0:
        _s = _s / ts['topics'][tid]['sqs'] + ts['topics'][tid]['bia'];
    else:
        _s = ts['topics'][tid]['bia'];
    return _s;

# [vi]*topiccount = match(topicsensor, vector)
# 计算vector与tid所指的topic的匹配结果，即归一化后的向量乘法
def match(ts: dict, tid: int, vec: dict or set or list):
    _val = mult(ts, tid, norm(vec));
    return _val;

# [vi]*topiccount = matches(topicsensor, vector)
# 计算vector与所有topic的匹配结果，即归一化后的矩阵乘法
def matches(ts: dict, vec: dict or set or list):
    _val = [0] * ts['topiccount'];
    _vec = norm(vec);
    for _i in range(ts['topiccount']):
        _val[_i] = mult(ts, _i, _vec);
    return _val;
