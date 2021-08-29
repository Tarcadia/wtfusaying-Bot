
import threading
import CONSTS;

import exs.wordlinksensor as xwls;
import exs.contextsensor as xcs;
import exs.topicsensor as xts;
import exs.thermalmeter as xtm;

import re;
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

contexts = dict();
thermals = dict();
wordlink = xwls.WordLinkSensor(memorypath = CONFIG_PATH + WORDLINK_CFG);

def onmsg(src, txt = ''):
    if txt:
        if src['cid'] in contexts and contexts[src['cid']]:
            contexts[src['cid']].update(txt);
        else:
            contexts[src['cid']] = xcs.ContextSensor();
            contexts[src['cid']].update(txt);
    
    if src['cid'] in thermals and thermals[src['cid']]:
        thermals[src['cid']].onmsg(src['time']);
    else:
        if src['ctype'][0] == 'g':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
            thermals[src['cid']].onmsg(src['time']);
        elif src['ctype'][0] == 'p':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
            thermals[src['cid']].onmsg(src['time']);
        else:
            thermals[src['cid']] = None;

def oncall(src, txt = '', k = 1):
    if txt:
        if src['cid'] in contexts and contexts[src['cid']]:
            contexts[src['cid']].update(txt);
        else:
            contexts[src['cid']] = xcs.ContextSensor();
            contexts[src['cid']].update(txt);
    
    if src['cid'] in thermals and thermals[src['cid']]:
        thermals[src['cid']].oncall(src['time'], k = k);
    else:
        if src['ctype'][0] == 'g':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
            thermals[src['cid']].oncall(src['time'], k = k);
        elif src['ctype'][0] == 'p':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
            thermals[src['cid']].oncall(src['time'], k = k);
        else:
            thermals[src['cid']] = None;

def oncalltalk(src, txt = ''):
    if txt:
        if src['cid'] in contexts and contexts[src['cid']]:
            contexts[src['cid']].update(txt);
        else:
            contexts[src['cid']] = xcs.ContextSensor();
            contexts[src['cid']].update(txt);
    
    if src['cid'] in thermals and thermals[src['cid']]:
        thermals[src['cid']].oncalltalk(src['time']);
    else:
        if src['ctype'][0] == 'g':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
            thermals[src['cid']].oncalltalk(src['time']);
        elif src['ctype'][0] == 'p':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
            thermals[src['cid']].oncalltalk(src['time']);
        else:
            thermals[src['cid']] = None;

def ontalk(src):
    if src['cid'] in thermals and thermals[src['cid']]:
        thermals[src['cid']].ontalk(src['time']);
    else:
        if src['ctype'][0] == 'g':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = GROUP_TALKRATE);
            thermals[src['cid']].ontalk(src['time']);
        elif src['ctype'][0] == 'p':
            thermals[src['cid']] = xtm.ThermalMeter(talkrate = PRIV_TALKRATE);
            thermals[src['cid']].ontalk(src['time']);
        else:
            thermals[src['cid']] = None;

def cantalk(src, p: float = 1):
    if src['cid'] in thermals and thermals[src['cid']]:
        return thermals[src['cid']].cantalk(p = p);
    else:
        return False;
    
def trycantalk(src, p: float = 1):
    if cantalk(src, p = p):
        thermals[src['cid']].ontalk();
        return True;
    else:
        return False;

def strparams(src):
    lines = [];
    lines.append("当前对话key：%s" % src['cid']);
    if src['cid'] in thermals and thermals[src['cid']]:
        lines.append("————前向度：%.1f%%" % (thermals[src['cid']].value * 100));
    else:
        lines.append("————前向度缺失");
    if src['cid'] in contexts and contexts[src['cid']]:
        cvec = contexts[src['cid']].get();
        lines.append("————上下文关键词：" + ','.join(['%s: %.1f' % (_k, cvec[_k]) for _k in cvec]));
    else:
        lines.append("————上下文信息缺失");
    return '\n'.join(lines);

# 接口函数

#保存
def save():
    return;
