
import sys;
import os;
import fnmatch;
import json;
import random;
import logging;

VERSION = 'v20210802';
PATH_PATTEN = './sentencepatten/';
MAX_DEPTH = 16;

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);

logger.info('Sentence Generator Loaded');


# patten                : dict
# {
#   'patten'            : str,          // patten名
#   '<key1>'            : subsent,      // patten内的转义
#   '<key2>'            : subsent,      // patten内的转义
#   ...
#                                       // 在解析的时候会根据这里的key对patten展开的内容中的"#key"进行替换
#                                       // 转义的作用域是本patten内的subsent及嵌套元素，不对patten内subsent转义后的内容进行转义
#                                       // 逻辑上允许对展开的patten的patten名进行转义，但不建议
# }

# sentence              : list          // 一段语句的表达形式
# [
#   subsent             : subsent       // 语句由subsent连缀而成
# ]

# subsent               : sentence, patten, str     // 语句的元素可以是一个patten，一个语句或者一个字符串


# subsent = getpatten(pattenname);
# 根据pattenname取patten中的一则subsent
def getpatten(patten: str = ''):
    try:
        _fp = open(PATH_PATTEN + patten + '.json', encoding='utf-8');
        _pattens = json.load(_fp);
        _fp.close();
        _result = random.choice(_pattens);
        return _result;
    except:
        logger.error('getpatten: unseccsessful get a patten');
        return '';

# subsent = depatten(subsent, trans);
# 将patten模板的subsent根据trans进行转义
# trans                 : dict
# {
#   '#<key1>'           : subsent,      // 一条转义
#   '#<key2>'           : subsent,
#   ...
# }
def depatten(patten, trans: dict = dict()):
    if type(patten) == str:
        if patten in trans:
            _result = trans[patten];
        else:
            _result = patten;
        return _result;
    elif type(patten) == list:
        _result = [depatten(_val, trans) for _val in patten];
        return _result;
    elif type(patten) == dict:
        _result = {_key : depatten(patten[_key], trans) for _key in patten};
        return _result;
    else:
        logger.error('depatten: unseccsessful depatten');
        return '';

# str = translate(subsent);
# 将subsent嵌套迭代翻译为字符串
def translate(s = '', depth : int = 0):
    if depth > MAX_DEPTH:
        logger.error('translate: too deep translation');
        return '';
    elif type(s) == str:
        return s;
    elif type(s) != list and type(s) != dict:
        logger.error('translate: unrecognized translation');
        return '';
    elif type(s) == list:
        _result = '';
        for _sub in s:
            _result = _result + translate(_sub, depth + 1);
        return _result;
    elif type(s) == dict:
        if not 'patten' in s.keys():
            logger.error('translate: unrecognized translation');
            return '';
        elif not os.path.isfile(PATH_PATTEN + s['patten'] + '.json'):
            logger.error('translate: unrecognized patten');
            return '';
        else:
            _patten = getpatten(s['patten']);
            _trans = {('#' + _key) : s[_key] for _key in s if _key != 'patten'}
            _result = translate(depatten(_patten, _trans), depth + 1);
            return _result;





# 管理功能接口

def listpatten(filter: str = '*'):
    _files = [];
    for _fpath, _fdirs, _fnames in os.walk(PATH_PATTEN):
        for _fname in _fnames:
            if fnmatch.fnmatch(_fname, filter):
                _file = _fpath + '/' + _fname;
                _files.append(_file);
    return json.dumps(_files, indent = 4);

def showpatten(patten: str):
    if os.path.isfile(PATH_PATTEN + patten + '.json'):
        try:
            _fp = open(PATH_PATTEN + patten + '.json', encoding='utf-8');
            _pattens = json.load(_fp);
            _fp.close();
            return json.dumps(_pattens, indent = 4);
        except:
            return 'ERR: Unsuccsessful get a patten';
    else:
        return 'ERR: Unrecognized patten';

def addpatten(patten: str, content: str):
    if os.path.isfile(PATH_PATTEN + patten + '.json'):
        try:
            _fp = open(PATH_PATTEN + patten + '.json', encoding='utf-8');
            _pattens = json.load(_fp);
            _fp.close();
        except:
            return 'ERR: Unsuccsessful get a patten';

        try:
            _append = json.loads(content);
            _pattens.append(_append);
            _fp = open(PATH_PATTEN + patten + '.json', mode = 'w', encoding='utf-8');
            json.dump(_pattens, _fp, indent = 4);
            _fp.close();
        except:
            return 'ERR: Unsuccessful add to a patten';
    else:
        return 'ERR: Unrecognized patten';

def newpatten(patten: str, content: str):
    if not os.path.isfile(PATH_PATTEN + patten + '.json'):
        try:
            _patten = json.loads(content);
            _fp = open(PATH_PATTEN + patten + '.json', mode = 'w', encoding='utf-8');
            json.dump(_patten, _fp, indent = 4);
            _fp.close();
        except:
            return 'ERR: Unsuccessful new a patten';
    else:
        return 'ERR: Existing patten';

def runpatten(content: str):
    try:
        _content = json.loads(content);
        return translate(_content);
    except:
        return 'ERR: Unsuccsessful decode: ' + json.dumps(sys.exc_info());


