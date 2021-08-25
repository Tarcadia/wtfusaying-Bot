
import math;
import json
import os;
import logging

VERSION = 'v20210807';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);

logger.info('Word-link Sensor Loaded');

# wordlinksensor        : dict
# {
#   memorypath          : str,          // 数据存储的路径，应当保证文件的可访问性以实现定期的数据存储
#   words               : dict[str]     // 以单词为索引的wordlink向量的列表，形如topicsensor的topic向量
#   {{
#       sum             : float,        // 特征向量的和的维护
#       sqs             : float,        // 特征向量的平方和的维护
#       cnt             : int,          // 特征向量的累加的维护
#       bia             : float,        // 特征向量的偏移
#       vec[<key>]      : dict{float}   // topic向量，用dict来实现稀疏下的计算，应当是未正规化或归一化的
#   }}
# }

# vector[<key>:str]{float}      : dict          // 一般是context向量，为稀疏的float类型向量，键值为一个关键词
# vector{<key>:str}             : set           // vector的化简，为稀疏的元素值为1的向量，为有元素的关键词的集合
# vector[<key>:str]             : list          // vector的化简，为稀疏的元素值为1的向量，为有元素的关键词的列表



# wordlinksensor = new()
# 初始化一个wordlinksensor
def new(
    memorypath          : str   = ''
    ):

    _wordlinksensor = {
        'memorypath'    : memorypath,
        'words'         : dict()
    };

    if memorypath == '' or not os.path.isfile(memorypath):
        pass;
    elif os.path.isfile(memorypath):
        _fp = open(memorypath, mode = 'r', encoding = 'utf-8');
        _words = json.load(_fp);
        _fp.close();
        _wordlinksensor['words'] = _words;

    return _wordlinksensor;

# wordlink = newwordlink(k, vec)
# 创建一个新的wordlink
def newwordlink(k: float = 1, vec: dict or list or set = {}):
    _wordlink = {
        'sum'       : 0,
        'sqs'       : 0,
        'cnt'       : 0,
        'bia'       : 0,
        'vec'       : dict()
    };
    if type(vec) == dict:
        _dsum = 0;
        _dsqs = 0;
        _dcnt = 1;
        for _k in vec:
            if _k in _wordlink['vec']:
                _dsum += k * vec[_k];
                _dsqs += 2 * k * vec[_k] * _wordlink['vec'][_k] + k * k * vec[_k] * vec[_k];
                _wordlink['vec'][_k] += k * vec[_k];
            else:
                _dsum += k * vec[_k];
                _dsqs += k * k * vec[_k] * vec[_k];
                _wordlink['vec'][_k] = vec[_k];
        _wordlink['sum'] += _dsum;
        _wordlink['sqs'] += _dsqs;
        _wordlink['cnt'] += _dcnt;

    elif type(vec) == set or type(vec) == list:
        _dsum = 0;
        _dsqs = 0;
        _dcnt = 1;
        for _k in vec:
            if _k in _wordlink['vec']:
                _dsum += k;
                _dsqs += 2 * k * _wordlink['vec'][_k] + k * k;
                _wordlink['vec'][_k] += k;
            else:
                _dsum += k;
                _dsqs += k * k;
                _wordlink['vec'][_k] = k;
        _wordlink['sum'] += _dsum;
        _wordlink['sqs'] += _dsqs;
        _wordlink['cnt'] += _dcnt;

    return _wordlink;

# wordlinksensor = load(wordlinksensor)
# 为wordlinksensor进行一次文件加载
def load(wls: dict):
    if os.path.isfile(wls['memorypath']):
        _fp = open(wls['memorypath'], mode = 'r', encoding = 'utf-8');
        _words = json.load(_fp);
        _fp.close();
        wls['words'] = _words;
    return wls;

# wordlinksensor = save(wordlinksensor)
# 为wordlinksensor进行一次文件保存
def save(wls: dict):
    _fp = open(wls['memorypath'], mode = 'w', encoding = 'utf-8');
    json.dump(wls['words'], _fp, ensure_ascii = False, indent = 4);
    _fp.close();
    return wls;

# wordlinksensor = clear(wordlinksensor)
# 将wordlinksensor的words清空
def clear(wls: dict):
    wls['words'].clear();
    return wls;

# wordlinksensor = add(wordlinksensor, w, k, vec)
# 为关键词w的wordlink累加入一个k倍的vector
def add(wls: dict, w: str, k: float = 1, vec:dict or set or list = dict()):
    if not w in wls['words']:
        wls['words'][w] = newwordlink(k, vec);
    else:
        if type(vec) == dict:
            _dsum = 0;
            _dsqs = 0;
            _dcnt = 1;
            for _k in vec:
                if _k in wls['words'][w]['vec']:
                    _dsum += k * vec[_k];
                    _dsqs += 2 * k * vec[_k] * wls['words'][w]['vec'][_k] + k * k * vec[_k] * vec[_k];
                    wls['words'][w]['vec'][_k] += k * vec[_k];
                else:
                    _dsum += k * vec[_k];
                    _dsqs += k * k * vec[_k] * vec[_k];
                    wls['words'][w]['vec'][_k] = vec[_k];
            wls['words'][w]['sum'] += _dsum;
            wls['words'][w]['sqs'] += _dsqs;
            wls['words'][w]['cnt'] += _dcnt;

        elif type(vec) == set or type(vec) == list:
            _dsum = 0;
            _dsqs = 0;
            _dcnt = 1;
            for _k in vec:
                if _k in wls['words'][w]['vec']:
                    _dsum += k;
                    _dsqs += 2 * k * wls['words'][w]['vec'][_k] + k * k;
                    wls['words'][w]['vec'][_k] += k;
                else:
                    _dsum += k;
                    _dsqs += k * k;
                    wls['words'][w]['vec'][_k] = k;
            wls['words'][w]['sum'] += _dsum;
            wls['words'][w]['sqs'] += _dsqs;
            wls['words'][w]['cnt'] += _dcnt;

    return wls;

# wordlinksensor = multime(wordlinksensor, w, k)
# 为关键词w的wordlink乘上一个k，cnt不变
def multime(wls: dict, w: str, k: float):
    if not w in wls['words']:
        wls['words'][w] = newwordlink();
    else:
        for _k in wls['words'][w]['vec']:
            wls['words'][w]['vec'][_k] *= k;
        wls['words'][w]['sum'] *= k;
        wls['words'][w]['sqs'] *= k * k;
        wls['words'][w]['bia'] *= k;

    return wls;
    
# wordlinksensor = shrink(wordlinksensor, w, k)
# 为关键词w的wordlink规模减小至cntx，即乘上一个cntx / cnt，cnt更新
# 用于在wordlink规模过大时缩减规模
def shrink(wls: dict, w: str, cntx: int):
    if not w in wls['words']:
        wls['words'][w] = newwordlink();
        wls['words'][w]['cnt'] = cntx;
    else:
        kx = cntx / wls['words'][w]['cnt'];
        for _k in wls['words'][w]['vec']:
            wls['words'][w]['vec'][_k] *= kx;
        wls['words'][w]['sum'] *= kx;
        wls['words'][w]['sqs'] *= kx * kx;
        wls['words'][w]['bia'] *= kx;
        wls['words'][w]['cnt'] = cntx;
    return wls;

# wordlinksensor = unify(wordlinksensor, w)
# 为关键词w的wordlink归一化
# 用于在wordlink规模过大时缩减规模
def unify(wls: dict, w: str):
    if not w in wls['words']:
        wls['words'][w] = newwordlink();
        wls['words'][w]['cnt'] = 1;
    else:
        _sqs = sum([wls['words'][w]['vec'][_k] * wls['words'][w]['vec'][_k] for _k in wls['words'][w]['vec']]);
        wls['words'][w]['vec'] = [wls['words'][w]['vec'][_k] * math.sqrt(_sqs) for _k in wls['words'][w]['vec']];
        wls['words'][w]['sum'] = sum([wls['words'][w]['vec'][_k] for _k in wls['words'][w]['vec']]);
        wls['words'][w]['sqs'] = sum([wls['words'][w]['vec'][_k] * wls['words'][w]['vec'][_k] for _k in wls['words'][w]['vec']]);
        wls['words'][w]['cnt'] = 1;
        wls['words'][w]['bia'] *= math.sqrt(_sqs);
    return wls;

# wordlinksensor = pick(wordlinksensor, w, n)
# 筛选保留wordlink的前n个关键词
# 或筛选保留wordlink的模的前k比例的关键词，|v[0:n]| / |v| <= k，保障第一个关键词
# cnt不变，bia等sum比例缩放
# 用于在wordlink规模过大时缩减规模
def pick(wls: dict, w: str, n: int = None, k: float = None):
    if not w in wls['words']:
        wls['words'][w] = newwordlink();
    if n != None and k == None:
        _kw = sorted(wls['words'][w]['vec'].items(), key = lambda x : x[1], reverse = True);
        _vec = {_k : _w for _k, _w in _kw[0 : min(len(_kw), n)]};
        _sum = sum([_w for _k, _w in _kw[0 : min(len(_kw), n)]]);
        _sqs = sum([_w * _w for _k, _w in _kw[0 : min(len(_kw), n)]]);
        _bia = wls['words'][w]['bia'] * _sum / wls['words'][w]['sum'] if wls['words'][w]['sum'] != 0 else wls['words'][w]['bia'];
        wls['words'][w]['vec'] = _vec;
        wls['words'][w]['sum'] = _sum;
        wls['words'][w]['sqs'] = _sqs;
        wls['words'][w]['bia'] = _bia;
        return wls;
    elif n == None and k != None:
        _kw = sorted(wls['words'][w]['vec'].items(), key = lambda x : x[1], reverse = True);
        _wq = [_w * _w for _k, _w in _kw];
        _cumwq = [sum(_wq[0 : _i + 1]) for _i in range(len(_wq))];
        _ks = [_i for _i in range(len(_cumwq)) if math.sqrt(_cumwq[_i]) / math.sqrt(sum(_wq)) <= k];
        _vec = {_kw[_i][0] : _kw[_i][1] for _i in _ks};
        _sum = sum([_kw[_i][1] for _i in _ks]);
        _sqs = sum([_kw[_i][1] * _kw[_i][1] for _i in _ks]);
        _bia = wls['words'][w]['bia'] * _sum / wls['words'][w]['sum'] if wls['words'][w]['sum'] != 0 else wls['words'][w]['bia'];
        wls['words'][w]['vec'] = _vec;
        wls['words'][w]['sum'] = _sum;
        wls['words'][w]['sqs'] = _sqs;
        wls['words'][w]['bia'] = _bia;
        return wls;
    elif n != None and k != None:
        _kw = sorted(wls['words'][w]['vec'].items(), key = lambda x : x[1], reverse = True);
        _wq = [_w * _w for _k, _w in _kw];
        _cumwq = [sum(_wq[0 : _i + 1]) for _i in range(len(_wq))];
        _ks = list(range(min(n, len(_cumwq)))) + [_i for _i in range(n, len(_cumwq)) if _cumwq[_i] / sum(_wq) <= k * k];
        _vec = {_kw[_i][0] : _kw[_i][1] for _i in _ks};
        _sum = sum([_kw[_i][1] for _i in _ks]);
        _sqs = sum([_kw[_i][1] * _kw[_i][1] for _i in _ks]);
        _bia = wls['words'][w]['bia'] * _sum / wls['words'][w]['sum'] if wls['words'][w]['sum'] != 0 else wls['words'][w]['bia'];
        wls['words'][w]['vec'] = _vec;
        wls['words'][w]['sum'] = _sum;
        wls['words'][w]['sqs'] = _sqs;
        wls['words'][w]['bia'] = _bia;
        return wls;

# wordlinksensor = repara(wordlinksensor, w)
# 遍历更新sum，sqs等维护参数
# 用于在wordlink多次更新后消除误差
def repara(wls: dict, w: str):
    if not w in wls['words']:
        wls['words'][w] = newwordlink();
    else:
        wls['words'][w]['sum'] = sum([wls['words'][w]['vec'][_k] for _k in wls['words'][w]['vec']]);
        wls['words'][w]['sqs'] = sum([wls['words'][w]['vec'][_k] * wls['words'][w]['vec'][_k] for _k in wls['words'][w]['vec']]);
    return wls;






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

# vector = wordlink(wordlinksensor, w)
# 返回关键词w的wordlink的vector形式
def wordlink(wls: dict, w: str):
    _vec = wls['words'][w]['vec'];
    return norm(_vec);

# vector = keywords(wordlinksensor, w, n)
# 返回关键词w的wordlink的前n个关键词
def keywords(wls: dict, w: str, n: int):
    if not w in wls['words']:
        return [];
    else:
        _kw = sorted(wls['words'][w]['vec'].items(), key = lambda x : x[1], reverse = True)
        _keys = [_k for _k, _w in _kw[0 : min(len(_kw), n)]];
    return _keys;

# v = mult(wordlinksensor, w, vector)
# 计算vector与关键词w的wordlink的内积
def mult(wls: dict, w: str, vec: dict or set or list):
    if not w in wls['words']:
        return 0;
    else:
        if type(vec) == set or type(vec) == list:
            vec = {_k : 1 for _k in vec};
        _s = sum([wls['words'][w]['vec'][_k] * vec[_k] for _k in vec if _k in wls['words'][w]['vec']]);
        if wls['words'][w]['sqs'] != 0:
            _s = _s / wls['words'][w]['sqs'] + wls['words'][w]['bia'];
        else:
            _s = wls['words'][w]['bia'];
        return _s;

# v = match(wordlinksensor, vector)
# 计算vector与关键词w的wordlink的匹配结果，即归一化后的向量乘法
def match(wls: dict, w: str, vec: dict or set or list):
    _val = mult(wls, w, norm(vec));
    return _val;

# {w:vw} = matches(wordlinksensor, vector)
# 计算vector与所有wordlink的匹配结果，即归一化后的矩阵乘法，返回是vector
def matches(wls: dict, vec: dict or set or list):
    _val = {_k : 0 for _k in wls['words']};
    _vec = norm(vec);
    for _k in wls['words']:
        _val[_k] = mult(wls, _k, _vec);
    return _val;



class WordLinkSensor:

    def __init__(
        self,
        memorypath      : str   = ''
    ) -> None:
        self._wls = new(
            memorypath = memorypath
        );
        return;

    def __iter__(self):
        for _w in self._wls['words']:
            yield _w;
    
    def __getitem__(self, key):
        return self.wordlink(key);

    def load(self):
        self._wls = load(self._wls);
        return;

    def save(self):
        self._wls = save(self._wls);
        return;

    def clear(self):
        self._wls = clear(self._wls);
        return;

    def add(self, w: str, k: float = 1, vec:dict or set or list = dict()):
        self._wls = add(self._wls, w = w, k = k, vec = vec);
        return;

    def multime(self, w: str, k: float):
        self._wls = multime(self._wls, w = w, k = k);
        return;

    def shrink(self, w: str, cntx: int):
        self._wls = shrink(self._wls, w = w, cntx = cntx);
        return;

    def unify(self, w: str):
        self._wls = unify(self._wls, w = w);
        return;

    def pick(self, w: str, n:int, k:float):
        self._wls = pick(self._wls, w = w, n = n, k = k);
        return;

    def repara(self, w: str):
        self._wls = repara(self._wls, w = w);

    def mult(self, w: str, vec: dict or list or set):
        return mult(self._wls, w = w, vec = vec);
    
    def match(self, w: str, vec: dict or list or set):
        return match(self._wls, w = w, vec = vec);
    
    def matches(self, vec: dict or list or set):
        return matches(self._wls, vec = vec);

    def wordlink(self, w: str):
        return wordlink(self._wls, w = w);

    def keywords(self, w: str, n: int):
        return keywords(self._wls, w = w, n = n);
    


