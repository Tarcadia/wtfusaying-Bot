
import sys;
import os;
import json;
import fnmatch;
import logging;
import sentencegenerator;

VERSION = 'v20210803';
PATH_PATTEN = sentencegenerator.PATH_PATTEN;

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[1;34m[%(asctime)s][%(levelname)s]\033[0;32m[%(name)s]\033[0m >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);

logger.info('Sentence Manager Loaded');


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
        return sentencegenerator.translate(_content);
    except:
        return 'ERR: Unsuccsessful decode: ' + json.dumps(sys.exc_info());
