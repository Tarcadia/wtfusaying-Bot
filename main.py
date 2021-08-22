
import CONSTS;

import botcontrol as bc;

import iomessagemanager as iomm;
import miraimessagemanager as mmm;
import tgmessagemanager as tmm;

import threading as thr;
import time;
import os;
import importlib;
import logging;

VERSION = 'v20210820';
THREADS = [];
TO_STOP = False;

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
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



# 底层系统组件的定义：
# _sys_cbs          : dict
# {
#   'fnc'           : function,     // 回调函数，详情请咨询BotControl中对回调的具体要求；
#   'flt'           : flt,          // 过滤器以确定一条消息是否需要调用回调，详情请咨询BotControl中对回调的具体要求；
#                                   // 明明可以在回调函数里面实现，为什么要拿出来呢？
#                                   // 因为作者还有着最后一丝丝的对性能的微弱希冀，企图用数据flt的形式实现过滤；
#   'key'           : str           // 回调函数的识别码，要求每个回调函数独一无二，建议用"_modname_funcname_xxx"的形式；
# },
# _sys_mods         : dict[modname] // 加载的模块组件的列表
# {
#   m1              : module,       // 各个模块组件
#   m2              : module,
#   m3              : module,
#   ...
# }
# _sys_help_doc     : str           // 底层系统组件的help显示



# 底层系统组件的功能：用于实现系统的基本后台控制内容对人接口，
# 1. 实现系统启动和合法结束的后台对人接口，
# 2. 实现系统和模块组件重加载、保存的后台对人接口，
# main.py的功能
# 4. 实现最基本的一堆加载，启动，作为程序入口,
# 5. 4包括了利用定义的模块组件mods的接口调用模块组件mods,
# 6. 没有3，
# 7. 由于以上的这些需求是杂糅的，所以就写在一起了；
# 8. 没有将MessageManager的部分写进来，因为觉得main里写底层系统组件还是确实太肿了，这部分反正基本不会重载啥的，就不要搞了；



# 一个模块组件需要的定义实现：
# 为一个单独的module的py，放在./mods/下以供调用，在调用时应当实现如下的接口
# _mod_help_doc     : str,          // 形如_sys_help_doc，为模块组件的help内容
# _mod_cbs          : list,         // 形如_sys_cbs，为模块组件要注册的callback列表
# start()                           // 模块的合法启动，返回自己的线程列表，虽然没用，但是这是要求
# save()                            // 模块的保存操作
# stop()                            // 模块的合法结束


# 初始化BotControl
_bc = bc.BotControl();

# 初始化API接口类（MessageManager）
_iomm = iomm.IOMessageManager();

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



# 底层系统组件实现

_sys_cbs = [];                      # 底层系统组件的 call back 列表
_sys_mods = dict();                 # 引入mods列表
_sys_help_doc = """
# 底层系统组件
help                                : 获取帮助
reload                              : 重载组件
    -a                              : 重载全部组件
    -m <m1>[ <m2> ...]              : 重载组件<m_i>
save                                : 调起存档
stop                                : 合法结束运行
""";                                # 底层系统组件的help doc

def reloadall():
    # 查找所有模块组件
    _modname_list = [];
    _files = os.listdir('./mods/');
    for _file in _files:
        _filename, _fileext = os.path.splitext(_file);
        if _fileext == 'py':
            _modname = _filename;
            _modname_list.append(_modname);
    # 解注册当前所有模块组件接口，关闭当前所有模块组件
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        for _cb in _mod._mod_cbs:
            _bc.deregcallback(_cb['key']);
        try:
            _mod.save();
        except Exception as _err:
            logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
        try:
            _mod.stop();
        except Exception as _err:
            logger.error('Failed stop mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
    # 重加载新查找的模块组件，开启模块组件，注册接口
    _sys_mods.clear();
    for _modname in _modname_list:
        try:
            _mod = importlib.import_module('mods.' + _modname);
            _sys_mods[_modname] = _mod;
        except Exception as _err:
            logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
        try:
            _mod_thrs = _mod.start();
            THREADS.extend(_mod_thrs);
        except Exception as _err:
            logger.error('Failed start mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
        for _cb in _mod._mod_cbs:
            try:
                _bc.regcallback(_cb['fnc'], _cb['flt'], _cb['key']);
            except KeyError:
                logger.error('Failed reg call back or Key Error');
            except Exception as _err:
                logger.error('Failed reg call back %s with %s' % (_cb['key'], type(_err)));
                logger.debug(_err);
    return;

def reloadmod(modlist: list = []):
    for _modname in modlist:
        # 查找已有模块组件，解注册模块组件接口，关闭模块组件
        if _modname in _sys_mods:
            _mod = _sys_mods[_modname];
            for _cb in _mod._mod_cbs:
                _bc.deregcallback(_cb['key']);
            try:
                _mod.save();
            except Exception as _err:
                logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
                logger.debug(_err);
            try:
                _mod.stop();
            except Exception as _err:
                logger.error('Failed stop mod %s with %s' % (_modname, type(_err)));
                logger.debug(_err);
            _sys_mods.pop(_modname);
        # 重加载模块组件，开启模块组件，注册接口
        if os.path.isfile('./mods/' + _modname + '.py'):
            try:
                _mod = importlib.import_module('mods.' + _modname);
                _sys_mods[_modname] = _mod;
            except Exception as _err:
                logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
                logger.debug(_err);
            try:
                _mod_thrs = _mod.start();
                THREADS.extend(_mod_thrs);
            except Exception as _err:
                logger.error('Failed start mod %s with %s' % (_modname, type(_err)));
                logger.debug(_err);
            for _cb in _mod._mod_cbs:
                try:
                    _bc.regcallback(_cb['fnc'], _cb['flt'], _cb['key']);
                except KeyError:
                    logger.error('Failed reg call back or Key Error');
                except Exception as _err:
                    logger.error('Failed reg call back %s with %s' % (_cb['key'], type(_err)));
                    logger.debug(_err);
        else:
            logger.debug('Failed import mod %s for non-exists' % _modname);
    return;

def save():
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        try:
            _mod.save();
        except Exception as _err:
            logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
    return;

def stop():
    # 关闭BotControl
    _bc.threadstop();
    # 关闭各个MM
    _iomm.threadstop();
    _mmm.threadstop();
    _tmm.threadstop();
    # 解注册当前所有模块组件接口，关闭当前所有模块组件
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        for _cb in _mod._mod_cbs:
            _bc.deregcallback(_cb['key']);
        try:
            _mod.save();
        except Exception as _err:
            logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
        try:
            _mod.stop();
        except Exception as _err:
            logger.error('Failed stop mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
    print('已关闭');
    return;

def stopwatch():
    while not TO_STOP:
        time.sleep(1);
    stop();



# 底层系统组件接口

_sys_cb_flt_echo = {'mmk' : {'mirai', 'telegram'}, 'msg' : {}};
def _sys_cb_fnc_echo(mmk, msg):
    logger.info(msg);

_sys_cb_flt_help = {'mmk' : {'IO'}, 'msg' : {'call' : 'help'}};
def _sys_cb_fnc_help(mmk, msg):
    _bc.send(mmk, _sys_help_doc);
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        _bc.send(mmk, _mod._mod_help_doc);

_sys_cb_flt_reload = {'mmk' : {'IO'}, 'msg' : {'call' : 'reload'}};
def _sys_cb_fnc_reload(mmk, msg):
    if msg['args']:
        if msg['args'][0] == '-a':
            _bc.send(mmk, '开始重加载全部...');
            reloadall();
            _bc.send(mmk, '重加载完成');
        elif msg['args'][0] == '-m':
            try:
                _bc.send(mmk, '开始重加载...');
                reloadmod(msg['args'][1:]);
                _bc.send(mmk, '重加载完成');
            except Exception as _err:
                _bc.send(mmk, '执行失败，help一下');
                logger.error('Failed reloadmod with %s' % type(_err));
                logger.debug(_err);
    else:
        _bc.send(mmk, '参数不对，help一下');

_sys_cb_flt_save = {'mmk' : {'IO'}, 'msg' : {'call' : 'save'}};
def _sys_cb_fnc_save(mmk, msg):
    _bc.send(mmk, '开始保存...');
    save();
    _bc.send(mmk, '保存完成');

_sys_cb_flt_stop = {'mmk' : {'IO'}, 'msg' : {'call' : 'stop'}};
def _sys_cb_fnc_stop(mmk, msg):
    _bc.send(mmk, '正在关闭...');
    global TO_STOP;
    TO_STOP = True;
    _bc.send(mmk, '已启动关闭线程');

_sys_cbs.append({'fnc': _sys_cb_fnc_echo, 'flt': _sys_cb_flt_echo, 'key': '_sys_cb_echo'});
_sys_cbs.append({'fnc': _sys_cb_fnc_help, 'flt': _sys_cb_flt_help, 'key': '_sys_cb_help'});
_sys_cbs.append({'fnc': _sys_cb_fnc_reload, 'flt': _sys_cb_flt_reload, 'key': '_sys_cb_reload'});
_sys_cbs.append({'fnc': _sys_cb_fnc_save, 'flt': _sys_cb_flt_save, 'key': '_sys_cb_save'});
_sys_cbs.append({'fnc': _sys_cb_fnc_stop, 'flt': _sys_cb_flt_stop, 'key': '_sys_cb_stop'});



# main
def main():
    # 注册各个messagemanager类的接口到BotControl
    _bc.regmessagemanager(_mmm, 'mirai');
    _bc.regmessagemanager(_tmm, 'telegram');
    _bc.regmessagemanager(_iomm, 'IO');
    # 注册各个callback接口到BotControl
    for _cb in _sys_cbs:
        _bc.regcallback(_cb['fnc'], _cb['flt'], _cb['key']);
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        for _cb in _mod._mod_cbs:
            _bc.regcallback(_cb['fnc'], _cb['flt'], _cb['key']);
    # 启动各个组件
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        _mod_thrs = _mod.start();
        THREADS.extend(_mod_thrs);
    # 启动各个MM
    for _mm in [ _iomm, _mmm, _tmm ]:
        _mm.open();
        _mm_thrs = _mm.threadpolling();
        THREADS.extend(_mm_thrs);
    # 启动BotControl
    _bc_thrs = _bc.threadpolling();
    THREADS.extend(_bc_thrs);
    return;

if __name__ == '__main__':
    # 启动
    main();
    # 退出等待
    stopwatch();