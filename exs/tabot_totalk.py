
import time
import CONSTS;

import exs.wordlinksensor as xwls;
import exs.contextsensor as xcs;
import exs.topicsensor as xts;
import exs.thermalmeter as xtm;

import re;
import threading as thr;
import logging;

VERSION = 'v20210823';
CONFIG_PATH = './config/';
WORDLINK_CFG = 'tabot_totalk_wls.json'

GROUP_TALKRATE = 10;
PRIV_TALKRATE = 1;

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot To Talk - ex Loaded');

# 数据记录：
# chatkey = '<mmk>.<ctype><rcid>';              // 用于跨接口的标识语境
# contexts = dict[chatkey]{contextsensor};      // 记录聊天上下文的contextsensor模块
# thermals = dict[chatkey]{thermalmeter};       // 记录聊天热度和发言控制的thermalmeter模块
# wordlinks = wordlinksensor;                   // 学习的结果，将会文件存储

datalock = thr.RLock();
contexts = dict();
thermals = dict();
wordlink = xwls.WordLinkSensor(memorypath = CONFIG_PATH + WORDLINK_CFG);

def onmsg(src, txt = '', t = None):
    if t == None:
        if src['time']:
            t = src['time'];
        else:
            t = time.time();
    
    if txt:
        with datalock:
            if src['cid'] in contexts and contexts[src['cid']]:
                contexts[src['cid']].update(txt, t = t);
            else:
                contexts[src['cid']] = xcs.ContextSensor();
                contexts[src['cid']].update(txt, t = t);
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].onmsg(t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
                thermals[src['cid']].onmsg(t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
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
                contexts[src['cid']].update(txt, t = t);
            else:
                contexts[src['cid']] = xcs.ContextSensor();
                contexts[src['cid']].update(txt, t = t);
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].oncall(k = k, t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
                thermals[src['cid']].oncall(k = k, t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
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
                contexts[src['cid']].update(txt, t = t);
            else:
                contexts[src['cid']] = xcs.ContextSensor();
                contexts[src['cid']].update(txt, t = t);
    
    with datalock:
        if src['cid'] in thermals and thermals[src['cid']]:
            thermals[src['cid']].oncalltalk(t = t);
        else:
            if src['ctype'][0] == 'g':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
                thermals[src['cid']].oncalltalk(t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
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
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
                thermals[src['cid']].ontalk(t = t);
            elif src['ctype'][0] == 'p':
                thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
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
        lines.append("————前向度：%.1f%%" % (thermals[src['cid']].value * 100));
    else:
        lines.append("————前向度缺失");
    if src['cid'] in contexts and contexts[src['cid']]:
        cvec = contexts[src['cid']].get(t = src['time']);
        lines.append("————上下文关键词：" + ','.join(['%s: %.1f' % (_k, cvec[_k]) for _k in cvec]));
    else:
        lines.append("————上下文信息缺失");
    return '\n'.join(lines);

# 接口函数

#保存
def save():
    return;
