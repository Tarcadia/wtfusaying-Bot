

import CONSTS;

import exs.wordlinksensor as xwls;
import exs.contextsensor as xcs;
import exs.topicsensor as xts;
import exs.thermalmeter as xtm;

import os;
import re;
import json
import time;
import random;
import threading as thr;
import logging;

VERSION = 'v20210823';
CONFIG_PATH = './config/';
TALKLIST_CFG = 'tabot_totalk_talklst.json'
CMDLIST_CFG = 'tabot_totalk_cmdlst.json'
WORDLINK_CFG = 'tabot_totalk_wls.json'

KEYWORDS_COUNT = 5;

THERMAL_GROUP_TALKRATE = 4;
THERMAL_PRIV_TALKRATE = 1;
THERMAL_TAU = 60 * 60;

CONTEXT_FLT = ('n', 'nr', 'ns', 'nt', 'nw', 'vn', 'v', 'eng');
CONTEXT_METH = 'all';
CONTEXT_WEI = False;
CONTEXT_TAU = 180;
CONTEXT_ALPHA = 6;

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot To Talk - ex Loaded');

# 数据类型：
# chatkey = '<mmk>.<ctype><rcid>';              // 用于跨接口的标识语境

# 数据记录：
# talklist = list;                              // 简单查找表式的关键词对话内容
# cmdlist = list;                               // 简单查找表式的指令内容（其实就是强制发言的对话）
# contexts = dict[chatkey]{contextsensor};      // 记录聊天上下文的contextsensor模块
# thermals = dict[chatkey]{thermalmeter};       // 记录聊天热度和发言控制的thermalmeter模块
# wordlinks = wordlinksensor;                   // 学习的结果，将会文件存储

talklist = [];
cmdlist = [];
datalock = thr.RLock();
contexts = dict();
thermals = dict();
wordlink = xwls.WordLinkSensor(memorypath = CONFIG_PATH + WORDLINK_CFG);

def loadtalks():
    global talklist;
    global cmdlist;
    
    if os.path.isfile(CONFIG_PATH + TALKLIST_CFG, mode = 'w', encoding = 'utf-8'):
        _fp = open(CONFIG_PATH + TALKLIST_CFG);
        _lst = json.load(_fp);
        _fp.close();
    else:
        _lst = [];
    with datalock:
        talklist.clear();
        talklist.extend(_lst);
    
    if os.path.isfile(CONFIG_PATH + CMDLIST_CFG, mode = 'w', encoding = 'utf-8'):
        _fp = open(CONFIG_PATH + CMDLIST_CFG);
        _lst = json.load(_fp);
        _fp.close();
    else:
        _lst = [];
    with datalock:
        cmdlist.clear();
        cmdlist.extend(_lst);

def savetalks():
    with datalock:
        _fp = open(CONFIG_PATH + TALKLIST_CFG, mode = 'w', encoding = 'utf-8');
        json.dump(talklist, _fp, ensure_ascii = False, indent = 4);
        _fp.close();
        _fp = open(CONFIG_PATH + CMDLIST_CFG, mode = 'w', encoding = 'utf-8');
        json.dump(cmdlist, _fp, ensure_ascii = False, indent = 4);
        _fp.close();

def talk(txt: str):
    _lst = [];
    with datalock:
        for _talk in talklist:
            if re.match(_talk['pat'], txt):
                if random.random() <= _talk['p']:
                    _lst.extend(_talk['rep']);
    return random.choice(_lst);

def talkcmd(txt: str):
    _lst = [];
    with datalock:
        for _cmd in cmdlist:
            if re.match(_cmd['pat'], txt):
                _lst.append(random.choice(_cmd['rep']));
    return _lst;

def onmsg(src, txt = '', t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    if txt:
        with datalock:
            if src['cid'] in contexts and contexts[src['cid']]:
                _vec = contexts[src['cid']].update(txt, t = t);
                _cvec = contexts[src['cid']].get(t = t);
                for _w in _vec:
                    wordlink.add(w = _w, k = 1, vec = _cvec);
            else:
                contexts[src['cid']] = xcs.ContextSensor(
                    contextfilter = CONTEXT_FLT,
                    contextmethod = CONTEXT_METH,
                    contextwei = CONTEXT_WEI,
                    tau = CONTEXT_TAU,
                    alpha = CONTEXT_ALPHA
                );
                _vec = contexts[src['cid']].update(txt, t = t);
                _cvec = contexts[src['cid']].get(t = t);
                for _w in _vec:
                    wordlink.add(w = _w, k = 1, vec = _cvec);
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].onmsg(t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_GROUP_TALKRATE);
                thermals[src['cid']].onmsg(t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_PRIV_TALKRATE);
                thermals[src['cid']].onmsg(t = t);

def oncall(src, txt = '', k = 1, t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    if txt:
        with datalock:
            if src['cid'] in contexts and contexts[src['cid']]:
                _vec = contexts[src['cid']].update(txt, t = t);
                _cvec = contexts[src['cid']].get(t = t);
                for _w in _vec:
                    wordlink.add(w = _w, k = 1, vec = _cvec);
            else:
                contexts[src['cid']] = xcs.ContextSensor(
                    contextfilter = CONTEXT_FLT,
                    contextmethod = CONTEXT_METH,
                    contextwei = CONTEXT_WEI,
                    tau = CONTEXT_TAU,
                    alpha = CONTEXT_ALPHA
                );
                _vec = contexts[src['cid']].update(txt, t = t);
                _cvec = contexts[src['cid']].get(t = t);
                for _w in _vec:
                    wordlink.add(w = _w, k = 1, vec = _cvec);
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].oncall(k = k, t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_GROUP_TALKRATE);
                thermals[src['cid']].oncall(k = k, t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_PRIV_TALKRATE);
                thermals[src['cid']].oncall(k = k, t = t);

def oncalltalk(src, txt = '', t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    if txt:
        with datalock:
            if src['cid'] in contexts and contexts[src['cid']]:
                _vec = contexts[src['cid']].update(txt, t = t);
                _cvec = contexts[src['cid']].get(t = t);
                for _w in _vec:
                    wordlink.add(w = _w, k = 1, vec = _cvec);
            else:
                contexts[src['cid']] = xcs.ContextSensor(
                    contextfilter = CONTEXT_FLT,
                    contextmethod = CONTEXT_METH,
                    contextwei = CONTEXT_WEI,
                    tau = CONTEXT_TAU,
                    alpha = CONTEXT_ALPHA
                );
                _vec = contexts[src['cid']].update(txt, t = t);
                _cvec = contexts[src['cid']].get(t = t);
                for _w in _vec:
                    wordlink.add(w = _w, k = 1, vec = _cvec);
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].oncalltalk(t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_GROUP_TALKRATE);
                thermals[src['cid']].oncalltalk(t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_PRIV_TALKRATE);
                thermals[src['cid']].oncalltalk(t = t);

def ontalk(src, t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].ontalk(t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_GROUP_TALKRATE);
                thermals[src['cid']].ontalk(t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(tau = THERMAL_TAU, talkrate = THERMAL_PRIV_TALKRATE);
                thermals[src['cid']].ontalk(t = t);

def cantalk(src, p: float = 1, t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            return thermals[src['cid']].cantalk(p = p, t = t);
        else:
            return False;
    
def trycantalk(src, p: float = 1, t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    with datalock:
        if cantalk(src, p = p):
            thermals[src['cid']].ontalk(t = t);
            return True;
        else:
            return False;

def migratechat(srcfrom, srcto):
    if srcfrom['cid'] in thermals and not srcto['cid'] in thermals:
        with datalock:
            thermals[srcto['cid']] = thermals.pop(srcfrom['cid']);
    if srcfrom['cid'] in contexts and not srcto['cid'] in contexts:
        with datalock:
            contexts[srcto['cid']] = contexts.pop(srcfrom['cid']);

def strparams(src):
    lines = [];
    lines.append("当前对话key：%s" % src['cid']);
    if src['cid'] in thermals and thermals[src['cid']]:
        lines.append("——前向度：%.1f%%" % (thermals[src['cid']].value * 100));
    else:
        lines.append("——前向度缺失");
    if src['cid'] in contexts and contexts[src['cid']]:
        cvec = contexts[src['cid']].get(t = src['time']);
        cvec = {_k : _w for _k, _w in sorted(cvec.items(), key = lambda v : v[1], reverse = True)[0 : min(len(cvec), KEYWORDS_COUNT)]};
        lines.append("——上下文关键词：" + ', '.join(['%s: %.1f' % (_k, cvec[_k]) for _k in cvec]));
    else:
        lines.append("——上下文信息缺失");
    return '\n'.join(lines);

def save():
    wordlink.save();
    savetalks();
    return;





# 初始化数据加载
loadtalks();
