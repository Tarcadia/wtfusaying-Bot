#!/usr/bin/env python3

import CONSTS;

import botcontrol as bc;

import iomessagemanager as iomm;
import loopbackmessagemanager as lbmm;
import miraimessagemanager as mmm;
import tgmessagemanager as tmm;

import essential as ess;

import time;
import logging;

VERSION = 'v20210823';
THREADS = [];

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[1;34m[%(asctime)s][%(levelname)s]\033[0;32m[%(name)s]\033[0m >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Main Loaded');



# ================================================================ #
#                           系统架构和序言                          #
# 关于系统的架构和实现方式的简述；                                   #
# 对自己毫不负责的垃圾代码的阅读方式的简述；                          #
# 对阅读到这里的你的期望。                                           #
# ================================================================ #
#                      Tarcadia 20210823-0310                      #
# ================================================================ #

# 系统分为三部分：
#
# |-----------------|      |--------------|      |------------------------|
# | MessageManagerA | <==> |              | <==> |  底层系统组件回调 _sys  |
# |-----------------|      |              |      |------------------------|
# | MessageManagerB | <==> |              | <==> |  加载模块组件回调 ModA  |
# |-----------------|      |  BotControl  |      |------------------------|
# | MessageManagerC | <==> |              | <==> |  加载模块组件回调 ModB  |
# |-----------------|      |              |      |------------------------|
# |      .....      | <==> |              | <==> |   加载模块组件回调 ...  |
# |-----------------|      |--------------|      |------------------------|
#
# 正常应该写一个MessageManager父类，写一个BotControl类，写一个Mod类，然后定义一下抽象的接口啥的，
#
# =================================================
# ============>>> 但是我不正常，我懒 <<<============
# =================================================
#
# 所以我啥都没写，大部分“定义”的操作都在注释里了，我都忘记写在哪里了，大概用到的地方才会写吧，所以各个类的具体内容都写在类的文档里；
# 而且大部分类的实现其实都是先用dict做了一个平行的无类实现版本，然后用类封装了一下的；
# MessageManager的接口需求和回调的接口需求都写在了BotControl里，模块组件面向加载系统的接口需求写在了main里，
# 并且main里直接写了一大堆加载、基本控制的实现，正常这些你是不是希望我建立一个essential模块或者类，不可能的，我不会；
# 是不是看到这里就已经头疼了，不要紧，反正我不打算维护；
# 架构就写这里了，谁想改都可以改，只要充分的读完各个注释“定义”，然后在调dict的key的时候不会手残，那你应该开发起来还是很轻松的；
# 其实定义都是写给编译器和IDE看的，我相信作为一名优秀的代码诗人，你一定能在没有自动补全和关键词修正的条件下，利用你完美的代码逻辑思维能力，完成伟大的编码工作；

# ================================================================ #
#                           系统架构和序言                          #
# 关于系统的架构和实现方式的简述；                                   #
# 对自己毫不负责的垃圾代码的阅读方式的简述；                          #
# 对阅读到这里的你的期望。                                           #
# ================================================================ #
#                      Tarcadia 20210823-0939                      #
# ================================================================ #

# 好消息，我刚刚把底层系统组件的部分都塞进了essential.py里，只不过这部分组件还是和main水乳交融在一起，我感觉放过去可读性其实更差了，你只要知道essential是main中很多功能的具体实现就可以了



# 底层系统组件的功能：用于实现系统的基本后台控制内容对人接口，
# 1. 实现系统启动和合法结束的后台对人接口，
# 2. 实现系统和模块组件重加载、保存的后台对人接口，
# main.py的功能
# 4. 实现最基本的一堆加载，启动，作为程序入口,
# 5. 4包括了利用定义的模块组件mods的接口调用模块组件mods,
# 6. 没有3，
# 7. 由于以上的这些需求是杂糅的，所以就写在一起了；
# 8. 没有将MessageManager的部分写进来，因为觉得main里写底层系统组件还是确实太肿了，这部分反正基本不会重载啥的，就不要搞了；



# 初始化BotControl
_bc = bc.BotControl();

# 初始化API接口类（MessageManager）
# 注册各个messagemanager类的接口到BotControl时回要求一个mmk
# 约定的，mmk在作为MM的标识符的同时应当起到识别mm类型的作用
# 所以mmk应当满足'<type>_<xxx>'的形式，或至少满足'<type>.*'的正则判定
_iomm = iomm.IOMessageManager();
_lbmm = lbmm.LoopbackMessageManager();

_mmm = mmm.MiraiMessageManager(
    host                = CONSTS.REMOTE_HOST,
    timeout             = 10,
    verify_qq           = CONSTS.VERIFY_QQ,
    verify_key          = CONSTS.VERIFY_KEY,
    buffer_size         = 1024
);

_tmm = tmm.TgMessageManager(
    timeout             = 10,
    conntimeout         = 3,
    token               = CONSTS.TOKEN,
    buffer_size         = 1024
);




# 主流程

def main():
    # 加载ess
    ess._sys_botcontrol = _bc;
    ess._sys_threads = THREADS;
    ess._sys_mms = [ _iomm, _lbmm, _mmm, _tmm ];
    ess.load();
    # 注册各个messagemanager类的接口到BotControl
    _bc.regmessagemanager(_iomm, 'IO');
    _bc.regmessagemanager(_lbmm, 'Loopback');
    _bc.regmessagemanager(_mmm, 'mirai');
    _bc.regmessagemanager(_tmm, 'telegram');
    # 注册各个callback接口到BotControl
    for _cb in ess._sys_cbs:
        _bc.regcallback(func = _cb['fnc'], filter = _cb['flt'], key = _cb['key']);
    for _modname in ess._sys_mods:
        _mod = ess._sys_mods[_modname];
        for _cb in _mod._mod_cbs:
            _bc.regcallback(func = _cb['fnc'], filter = _cb['flt'], key = _cb['key']);
    # 启动各个组件
    for _modname in ess._sys_mods:
        _mod = ess._sys_mods[_modname];
        _mod_thrs = _mod.start();
        THREADS.extend(_mod_thrs);
    # 启动各个MM
    for _mm in [ _iomm, _lbmm, _mmm, _tmm ]:
        _mm.open();
        _mm_thrs = _mm.threadpolling();
        THREADS.extend(_mm_thrs);
    # 启动BotControl
    _bc_thrs = _bc.threadpolling();
    THREADS.extend(_bc_thrs);
    return;

def stopwatch():
    while not ess._sys_tostop:
        time.sleep(1);
    ess.stop();

if __name__ == '__main__':
    # 启动
    main();
    # 退出等待
    stopwatch();