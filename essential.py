
import sys;
import os;
import importlib;
import logging;

VERSION = 'v20210822';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(name)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
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


_sys_botcontrol = None;             # 底层系统组件的 Bot Control 引用
_sys_threads = [];                  # 底层系统组件的线程列表，由main附入引用THREADS
_sys_mms = [];                      # 底层系统组件的 Message Manager 列表
_sys_cbs = [];                      # 底层系统组件的 Callback 列表
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
    # 解注册当前所有模块组件接口，关闭当前所有模块组件
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        try:
            for _cb in _mod._mod_cbs:
                _sys_botcontrol.deregcallback(_cb['key']);
        except KeyError:
            logger.error('Failed dereg call back or Key Error');
        except Exception as _err:
            logger.error('Failed dereg call back %s with %s' % (_cb['key'], type(_err)));
            logger.debug(_err);
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
        
        del sys.modules['mods.%s' % _modname];
        logger.info('Deport %s' % _modname);
    # 重加载新查找的模块组件，开启模块组件，注册接口
    _sys_mods.clear();
    for _modname in _modname_list:
        try:
            _mod = importlib.import_module('mods.' + _modname);
            _mod._botcontrol = _sys_botcontrol;
            _sys_mods[_modname] = _mod;
            logger.info('Import %s' % _modname);
        except Exception as _err:
            logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
        try:
            _mod_thrs = _mod.start();
            _sys_threads.extend(_mod_thrs);
        except Exception as _err:
            logger.error('Failed start mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
        try:
            for _cb in _mod._mod_cbs:
                _sys_botcontrol.regcallback(func = _cb['fnc'], filter = _cb['flt'], key = _cb['key']);
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
            try:
                for _cb in _mod._mod_cbs:
                    _sys_botcontrol.deregcallback(_cb['key']);
            except KeyError:
                logger.error('Failed dereg call back or Key Error');
            except Exception as _err:
                logger.error('Failed dereg call back %s with %s' % (_cb['key'], type(_err)));
                logger.debug(_err);
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
            del sys.modules['mods.%s' % _modname];
            logger.info('Deport %s' % _modname);
        # 重加载模块组件，开启模块组件，注册接口
        if os.path.isfile('./mods/' + _modname + '.py'):
            try:
                _mod = importlib.import_module('mods.' + _modname);
                _mod._botcontrol = _sys_botcontrol;
                _sys_mods[_modname] = _mod;
            except Exception as _err:
                logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
                logger.debug(_err);
            try:
                _mod_thrs = _mod.start();
                _sys_threads.extend(_mod_thrs);
            except Exception as _err:
                logger.error('Failed start mod %s with %s' % (_modname, type(_err)));
                logger.debug(_err);
            try:
                for _cb in _mod._mod_cbs:
                    _sys_botcontrol.regcallback(func = _cb['fnc'], filter = _cb['flt'], key = _cb['key']);
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
            logger.error('Failed dereg call back or Key Error');
        except Exception as _err:
            logger.error('Failed dereg call back %s with %s' % (_cb['key'], type(_err)));
            logger.debug(_err);
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



# 底层系统组件接口

_sys_cb_flt_echo = {'mmk' : {'mirai', 'telegram'}, 'msg' : {}};
def _sys_cb_fnc_echo(mmk, msg):
    logger.info(msg);

_sys_cb_flt_help = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'help'}};
def _sys_cb_fnc_help(mmk, msg):
    _sys_botcontrol.send('IO', _sys_help_doc);
    for _modname in _sys_mods:
        _mod = _sys_mods[_modname];
        _sys_botcontrol.send('IO', _mod._mod_help_doc);

_sys_cb_flt_reload = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'reload'}};
def _sys_cb_fnc_reload(mmk, msg):
    if msg['args']:
        if msg['args'][0] == '-a':
            _sys_botcontrol.send('IO', '开始重加载全部...');
            reloadall();
            _sys_botcontrol.send('IO', '重加载完成');
        elif msg['args'][0] == '-m':
            try:
                _sys_botcontrol.send('IO', '开始重加载...');
                reloadmod(msg['args'][1:]);
                _sys_botcontrol.send('IO', '重加载完成');
            except Exception as _err:
                _sys_botcontrol.send('IO', '执行失败，help一下');
                logger.error('Failed reload mod with %s' % type(_err));
                logger.debug(_err);
    else:
        _sys_botcontrol.send('IO', '参数不对，help一下');

_sys_cb_flt_save = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'save'}};
def _sys_cb_fnc_save(mmk, msg):
    _sys_botcontrol.send('IO', '开始保存...');
    save();
    _sys_botcontrol.send('IO', '保存完成');

_sys_cb_flt_stop = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'stop'}};
def _sys_cb_fnc_stop(mmk, msg):
    _sys_botcontrol.send('IO', '正在关闭...');
    global TO_STOP;
    TO_STOP = True;
    _sys_botcontrol.send('IO', '已启动关闭线程');



# 底层系统组件加载

def load():

    # 注册底层系统组件的callback
    _sys_cbs.append({'fnc': _sys_cb_fnc_echo, 'flt': _sys_cb_flt_echo, 'key': '_sys_cb_echo'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_help, 'flt': _sys_cb_flt_help, 'key': '_sys_cb_help'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_reload, 'flt': _sys_cb_flt_reload, 'key': '_sys_cb_reload'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_save, 'flt': _sys_cb_flt_save, 'key': '_sys_cb_save'});
    _sys_cbs.append({'fnc': _sys_cb_fnc_stop, 'flt': _sys_cb_flt_stop, 'key': '_sys_cb_stop'});

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
    
    # 加载查找的模块组件
    for _modname in _modname_list:
        try:
            _mod = importlib.import_module('mods.' + _modname);
            _mod._botcontrol = _sys_botcontrol;
            _sys_mods[_modname] = _mod;
        except Exception as _err:
            logger.error('Failed import mod %s with %s' % (_modname, type(_err)));
            logger.debug(_err);
    
    return;