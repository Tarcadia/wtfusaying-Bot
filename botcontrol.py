
import sys;
import os;
import json;
import fnmatch;
import logging;
import sentencegenerator;

VERSION = 'v20210803';
PATH_CONFIG = './config/';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(format='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Sentence Manager Loaded');


BotState = {
    'op': [],
    'memories':[]
}

def loadop():
    _fp = open(PATH_CONFIG + 'op.json', encoding='utf-8');
    _config = json.load(_fp);
    _fp.close();
    BotState['op'] = _config;
    return 'OP loaded';

def addop(cid):
    _fp = open(PATH_CONFIG + 'op.json', encoding='utf-8');
    _config = json.load(_fp);
    _fp.close();
    if cid in _config:
        return 'OP already exsists';
    else:
        _config.append(cid);
        BotState['op'] = _config;
        _fp = open(PATH_CONFIG + 'op.json', mode = 'w', encoding='utf-8');
        json.dump(_config, _fp);
        _fp.close();
        return 'OP added';

def removeop(cid):
    _fp = open(PATH_CONFIG + 'op.json', encoding='utf-8');
    _config = json.load(_fp);
    _fp.close();
    if not cid in _config:
        return 'OP does not exsist';
    else:
        _config.remove(cid);
        BotState['op'] = _config;
        _fp = open(PATH_CONFIG + 'op.json', mode = 'w', encoding='utf-8');
        json.dump(_config, _fp);
        _fp.close();
        return 'OP added';

def saveop():
    _fp = open(PATH_CONFIG + 'op.json', mode = 'w', encoding='utf-8');
    json.dump(BotState['op'], _fp);
    _fp.close();

def loadmemories():
    _fp = open(PATH_CONFIG + 'memories.json', encoding='utf-8');
    _config = json.load(_fp);
    _fp.close();
    BotState['memories'] = _config;

def savememories():
    _fp = open(PATH_CONFIG + 'op.json', mode = 'w', encoding='utf-8');
    json.dump(BotState['memories'], _fp);
    _fp.close();

def loadstate():
    loadop();
    
