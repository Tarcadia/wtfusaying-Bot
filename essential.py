
import sys;
import os;
import importlib;
import threading as thr;
import logging;

VERSION = 'v20210822';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;33m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Essential Loaded');



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



# 一个模块组件需要的定义实现：
# 为一个单独的module的py，放在./mods/下以供调用，在调用时应当实现如下的接口
# _mod_help_doc     : str,          // 形如ess._sys_help_doc，为模块组件的help内容
# _mod_cbs          : list,         // 形如ess._sys_cbs，为模块组件要注册的callback列表
# _botcontrol       : botcontrol    // 系统由此参数附回系统的botcontrol接口
# start()                           // 模块的合法启动，返回自己的线程列表，虽然没用，但是这是要求
# save()                            // 模块的保存操作
# stop()                            // 模块的合法结束

_sys_tostop = False;                # 底层系统组件的结束控制，供main的stopwatch调用
_sys_botcontrol = None;             # 底层系统组件的 Bot Control 引用
_sys_threads = [];                  # 底层系统组件的线程列表，由main附入引用THREADS
_sys_mms = [];                      # 底层系统组件的 Message Manager 列表
_sys_cbs = [];                      # 底层系统组件的 Callback 列表
_sys_mods = dict();                 # 引入mods列表
_sys_exs = dict();                  # 引入exs列表
_sys_help_doc = """
# 底层系统组件
help                                : 获取帮助
echo                                : 控制mm消息回显
    -on                             : 开启mm消息回显
    -off                            : 关闭mm消息回显
reload                              : 重载组件
    -a                              : 重载全部组件
    -m <m1>[ <m2> ...]              : 重载组件<m_i>
    -x <ex1>[ <ex2> ...]            : 重载ex模块<ex_i>
    -e                              : 同 -x
save                                : 调起存档
stop                                : 合法结束运行
""";                                # 底层系统组件的help doc

_sys_echoon = True;



# 底层系统组件实现
def reloadall():
    # 查找所有模块组件
    _modname_list = [];
    _files = os.listdir('./mods/');
    logger.info('Detecting mods');
    for _file in _files:
        logger.info('Detected file %s' % _file);
        _filename, _fileext = os.path.splitext(_file);
        if _fileext == '.py':
            logger.info('Accept file %s' % _file);
            _modname = _filename;
            _modname_list.append(_modname);
    # 查找所有额外支持
    _exname_list = [];
    _files = os.listdir('./exs/');
    logger.info('Detecting exs');
    for _file in _files:
        logger.info('Detected file %s' % _file);
        _filename, _fileext = os.path.splitext(_file);
        if _fileext == '.py':
            logger.info('Accept file %s' % _file);
            _exname = _filename;
            _exname_list.append(_exname);
    # 解注册当前所有模块组件接口，关闭当前所有模块组件
    _mods_topop = list(_sys_mods.keys()).copy();
    for _modname in _mods_topop:
        _mod = _sys_mods.pop(_modname);
        try:
            for _cb in _mod._mod_cbs:
                _sys_botcontrol.deregcallback(_cb['key']);
        except KeyError:
            logger.error('Failed dereg callback or Key Error');
        except Exception as _err:
            logger.error('Failed dereg callback %s with %s' % (_cb['key'], type(_err)));
            logger.exception(_err);
        try:
            _mod.save();
        except Exception as _err:
            logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
        try:
            _mod.stop();
        except Exception as _err:
            logger.error('Failed stop mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
        del sys.modules['mods.%s' % _modname];
        logger.info('Deport mods.%s' % _modname);
    # 卸载当前所有exs
    _exs_topop = list(_sys_exs.keys()).copy();
    for _exname in _exs_topop:
        _ex = _sys_exs.pop(_exname);
        del sys.modules['exs.%s' % _exname];
        logger.info('Deport exs.%s' % _exname);
    # 重载当前所有exs
    for _exname in _exname_list:
        try:
            _ex = importlib.import_module('exs.' +  _exname);
            _sys_exs[_exname] = _ex;
            logger.info('Import exs.%s' % _exname);
        except Exception as _err:
            logger.error('Failed import ex %s with %s' % (_exname, type(_err)));
            logger.exception(_err);
    # 重加载新查找的模块组件，开启模块组件，注册接口
    for _modname in _modname_list:
        try:
            _mod = importlib.import_module('mods.' + _modname);
            _mod._botcontrol = _sys_botcontrol;
            _sys_mods[_modname] = _mod;
            logger.info('Import mods.%s' % _modname);
        except Exception as _err:
            logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
        try:
            _mod_thrs = _mod.start();
            _sys_threads.extend(_mod_thrs);
        except Exception as _err:
            logger.error('Failed start mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
        try:
            for _cb in _mod._mod_cbs:
                _sys_botcontrol.regcallback(func = _cb['fnc'], filter = _cb['flt'], key = _cb['key']);
        except KeyError:
            logger.error('Failed reg callback or Key Error');
        except Exception as _err:
            logger.error('Failed reg callback %s with %s' % (_cb['key'], type(_err)));
            logger.exception(_err);
    return;



def reloadmod(modlist: list = []):
    for _modname in modlist:
        # 查找已有模块组件，解注册模块组件接口，关闭模块组件
        if _modname in _sys_mods:
            _mod = _sys_mods.pop(_modname);
            try:
                for _cb in _mod._mod_cbs:
                    _sys_botcontrol.deregcallback(_cb['key']);
            except KeyError:
                logger.error('Failed dereg callback or Key Error');
            except Exception as _err:
                logger.error('Failed dereg callback %s with %s' % (_cb['key'], type(_err)));
                logger.exception(_err);
            try:
                _mod.save();
            except Exception as _err:
                logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
                logger.exception(_err);
            try:
                _mod.stop();
            except Exception as _err:
                logger.error('Failed stop mod %s with %s' % (_modname, type(_err)));
                logger.exception(_err);
            del sys.modules['mods.%s' % _modname];
            logger.info('Deport mods.%s' % _modname);
        # 重加载模块组件，开启模块组件，注册接口
        if os.path.isfile('./mods/' + _modname + '.py'):
            try:
                _mod = importlib.import_module('mods.' + _modname);
                _mod._botcontrol = _sys_botcontrol;
                _sys_mods[_modname] = _mod;
                logger.info('Import mods.%s' % _modname);
            except Exception as _err:
                logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
                logger.exception(_err);
            try:
                _mod_thrs = _mod.start();
                _sys_threads.extend(_mod_thrs);
            except Exception as _err:
                logger.error('Failed start mod %s with %s' % (_modname, type(_err)));
                logger.exception(_err);
            try:
                for _cb in _mod._mod_cbs:
                    _sys_botcontrol.regcallback(func = _cb['fnc'], filter = _cb['flt'], key = _cb['key']);
            except KeyError:
                logger.error('Failed reg callback or Key Error');
            except Exception as _err:
                logger.error('Failed reg callback %s with %s' % (_cb['key'], type(_err)));
                logger.exception(_err);
        else:
            logger.debug('Failed import mod %s for non-exists' % _modname);
    return;



def reloadex(exlist: list = []):
    for _exname in exlist:
        # 查找已有模块组件，解注册模块组件接口，关闭模块组件
        if _exname in _sys_exs:
            _ex = _sys_exs.pop(_exname);
            del sys.modules['exs.%s' % _exname];
            logger.info('Deport exs.%s' % _exname);
        # 重加载模块组件，开启模块组件，注册接口
        if os.path.isfile('./exs/' + _exname + '.py'):
            try:
                _ex = importlib.import_module('exs.' + _exname);
                _sys_exs[_exname] = _ex;
                logger.info('Import exs.%s' % _exname);
            except Exception as _err:
                logger.error('Failed import mod %s with %s' % (_exname, type(_err)));
                logger.exception(_err);
        else:
            logger.debug('Failed import mod %s for non-exists' % _exname);
    return;



# 底层系统组件加载
def load():

    # 注册底层系统组件的callback
    _sys_cbs.append({'fnc': _sys_cb_fnc_echo, 'flt': _sys_cb_flt_echo, 'key': '_sys_cb_echo'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_cmd_help, 'flt': _sys_cb_flt_cmd_help, 'key': '_sys_cb_cmd_help'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_cmd_echo, 'flt': _sys_cb_flt_cmd_echo, 'key': '_sys_cb_cmd_echo'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_cmd_reload, 'flt': _sys_cb_flt_cmd_reload, 'key': '_sys_cb_cmd_reload'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_cmd_save, 'flt': _sys_cb_flt_cmd_save, 'key': '_sys_cb_cmd_save'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_cmd_stop, 'flt': _sys_cb_flt_cmd_stop, 'key': '_sys_cb_cmd_stop'});

    # 查找所有exs
    _exname_list = [];
    _files = os.listdir('./exs/');
    for _file in _files:
        _filename, _fileext = os.path.splitext(_file);
        if _fileext == '.py':
            _exname = _filename;
            _exname_list.append(_exname);

    # 加载查找的exs
    for _exname in _exname_list:
        try:
            _ex = importlib.import_module('exs.' + _exname);
            _sys_exs[_exname] = _ex;
        except Exception as _err:
            logger.error('Failed import ex %s with %s' % (_exname, type(_err)));
            logger.exception(_err);

    # 查找所有模块组件
    _modname_list = [];
    _files = os.listdir('./mods/');
    for _file in _files:
        _filename, _fileext = os.path.splitext(_file);
        if _fileext == '.py':
            _modname = _filename;
            _modname_list.append(_modname);
    
    # 加载查找的模块组件
    for _modname in _modname_list:
        try:
            _mod = importlib.import_module('mods.' + _modname);
            _mod._botcontrol = _sys_botcontrol;
            _sys_mods[_modname] = _mod;
        except Exception as _err:
            logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
    
    return;



def save():
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        try:
            _mod.save();
        except Exception as _err:
            logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
    return;



def stop():
    # 关闭BotControl
    try:
        _sys_botcontrol.threadstop();
    except:
        pass;
    # 关闭各个MM
    for _mm in _sys_mms:
        try:
            _mm.threadstop();
        except:
            pass;
    # 解注册当前所有模块组件接口，关闭当前所有模块组件
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        try:
            for _cb in _mod._mod_cbs:
                _sys_botcontrol.deregcallback(_cb['key']);
        except KeyError:
            logger.error('Failed dereg callback or Key Error');
        except Exception as _err:
            logger.error('Failed dereg callback %s with %s' % (_cb['key'], type(_err)));
            logger.exception(_err);
        try:
            _mod.save();
        except Exception as _err:
            logger.error('Failed save mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
        try:
            _mod.stop();
        except Exception as _err:
            logger.error('Failed stop mod %s with %s' % (_modname, type(_err)));
            logger.exception(_err);
    print('\033[1;30;47m已关闭\033[0m');
    return;



# 底层系统组件接口

_sys_cb_flt_echo = {'mmk' : {'mirai', 'telegram', 'IO', 'Loopback'}, 'msg' : {}};
def _sys_cb_fnc_echo(mmk, msg):
    if _sys_echoon:
        _sys_botcontrol.send('IO', msg);

_sys_cb_flt_cmd_help = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'help'}};
def _sys_cb_fnc_cmd_help(mmk, msg):
    _sys_botcontrol.send('IO', _sys_help_doc);
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        _sys_botcontrol.send('IO', _mod._mod_help_doc);

_sys_cb_flt_cmd_echo = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'echo'}};
def _sys_cb_fnc_cmd_echo(mmk, msg):
    global _sys_echoon;
    if msg['args']:
        if msg['args'][0] == '-on':
            _sys_echoon = True;
        elif msg['args'][0] == '-off':
            _sys_echoon = False;
        else:
            _sys_botcontrol.send('IO', '参数不对，help一下');
    else:
        _sys_botcontrol.send('IO', {'echo' : _sys_echoon});

_sys_cb_flt_cmd_reload = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'reload'}};
def _sys_cb_fnc_cmd_reload(mmk, msg):
    def toreload():
        with _sys_botcontrol.setlock:
            if msg['args']:
                if msg['args'][0] == '-a':
                    _sys_botcontrol.send('IO', '开始重加载全部...');
                    reloadall();
                    _sys_botcontrol.send('IO', '重加载全部完成');
                elif msg['args'][0] == '-m' and len(msg['args']) >= 2:
                    _sys_botcontrol.send('IO', '开始重加载组件模块...');
                    reloadmod(msg['args'][1:]);
                    _sys_botcontrol.send('IO', '重加载组件模块完成');
                elif msg['args'][0] == '-x' or msg['args'][0] == '-e' and len(msg['args']) >= 2:
                    _sys_botcontrol.send('IO', '开始重加载额外模块...');
                    reloadex(msg['args'][1:]);
                    _sys_botcontrol.send('IO', '重加载额外模块完成');
                else:
                    _sys_botcontrol.send('IO', '参数不对，help一下');
        return;
    
    if (msg['args'] and (
        (msg['args'][0] == '-a') or
        (msg['args'][0] == '-m' and len(msg['args']) >= 2) or
        (msg['args'][0] == '-x' or msg['args'][0] == '-e' and len(msg['args']) >= 2)
    )):
        _thr_reload = thr.Thread(target = toreload, name = 'To Reload Run');
        _sys_botcontrol.send('IO', '开启重加载线程...');
        _thr_reload.start();
    else:
        _sys_botcontrol.send('IO', '参数不对，help一下');
    

_sys_cb_flt_cmd_save = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'save'}};
def _sys_cb_fnc_cmd_save(mmk, msg):
    _sys_botcontrol.send('IO', '开始保存...');
    save();
    _sys_botcontrol.send('IO', '保存完成');

_sys_cb_flt_cmd_stop = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'stop'}};
def _sys_cb_fnc_cmd_stop(mmk, msg):
    _sys_botcontrol.send('IO', '正在关闭...');
    global _sys_tostop;
    _sys_tostop = True;
    _sys_botcontrol.send('IO', '已启动关闭线程');


