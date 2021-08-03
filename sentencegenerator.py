
import os;
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
logger_formatter = logging.Formatter(format='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Sentence Generator Loaded');


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
            
            


