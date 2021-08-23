
import threading as thr;
import time;
import os;
import json;
import logging;

VERSION = 'v20210823';
CONFIG = './config/autosave.json';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(name)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Auto Save Loaded');

# 一个模块组件需要的定义实现：
# 为一个单独的module的py，放在./mods/下以供调用，在调用时应当实现如下的接口
# _mod_help_doc     : str,          // 形如_sys_help_doc，为模块组件的help内容
# _mod_cbs          : list,         // 形如_sys_cbs，为模块组件要注册的callback列表
# _botcontrol       : botcontrol    // 系统由此参数附回系统的botcontrol接口
# start()                           // 模块的合法启动，返回自己的线程列表，虽然没用，但是这是要求
# save()                            // 模块的保存操作
# stop()                            // 模块的合法结束

_botcontrol = None;
_mod_cbs = [];
_mod_help_doc = """
# Auto Save：用于定时自动保存
autosave                            : 定时自动保存的设置
    -t <second>                     : 设置每隔<second>秒进行一次自动保存
    -on                             : 打开自动保存
    -off                            : 关闭自动保存
""";

_autosave_on_polling = False;
_autosave_time = -1;
_autosave_on = False;
_autosave_thr = None;


# 回调接口

_autosave_cb_flt_autosave_t = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'autosave', 'args' : ['-t']}};
def _autosave_cb_fnc_autosave_t(mmk, msg):
    global _autosave_time;
    _autosave_time = int(msg['args'][1]);
    return;

_autosave_cb_flt_autosave_on = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'autosave', 'args' : ['-on']}};
def _autosave_cb_fnc_autosave_on(mmk, msg):
    global _autosave_on;
    _autosave_on = True;
    return;

_autosave_cb_flt_autosave_off = {'mmk' : {'IO', 'Loopback'}, 'msg' : {'call' : 'autosave', 'args' : ['-off']}};
def _autosave_cb_fnc_autosave_off(mmk, msg):
    global _autosave_on;
    _autosave_on = False;
    return;

_mod_cbs.append({'fnc': _autosave_cb_fnc_autosave_t, 'flt': _autosave_cb_flt_autosave_t, 'key': '_autosave_cb_fnc_autosave_t'});
_mod_cbs.append({'fnc': _autosave_cb_fnc_autosave_on, 'flt': _autosave_cb_flt_autosave_on, 'key': '_autosave_cb_fnc_autosave_on'});
_mod_cbs.append({'fnc': _autosave_cb_fnc_autosave_off, 'flt': _autosave_cb_flt_autosave_off, 'key': '_autosave_cb_fnc_autosave_off'});





def _autosave_polling():
    _time_last = time.time();
    while _autosave_on_polling:
        if time.time() - _time_last < _autosave_time:
            time.sleep(1);
        elif _autosave_time > 0 and _autosave_on:
            _time_last = time.time();
            _cmd = {'call' : 'save', 'args' : []};
            _botcontrol.send('Loopback', _cmd);
    return;



def start():
    global _autosave_on_polling;
    global _autosave_time;
    global _autosave_on;
    global _autosave_thr;
    # 加载配置
    if os.path.isfile(CONFIG):
        _fp = open(CONFIG, mode = 'r');
        _config = json.load(_fp);
        _fp.close();
        _autosave_time = _config['_autosave_time'];
        _autosave_on = _config['_autosave_on'];
    
    # 启动线程
    _autosave_on_polling = True;
    _autosave_thr = thr.Thread(
        target = _autosave_polling,
        name = 'Auto Save Polling',
        daemon = True
    );
    _autosave_thr.start();
    return [_autosave_thr];

def save():
    global _autosave_time;
    global _autosave_on;

    _fp = open(CONFIG, mode = 'w');
    _config = {
        '_autosave_time'    : _autosave_time,
        '_autosave_on'      : _autosave_on
    };
    json.dump(_config, _fp);
    _fp.close();
    return;

def stop():
    global _autosave_on_polling;
    _autosave_on_polling = False;
    if _autosave_thr.is_alive():
        _autosave_thr.join();
    logger.info('Auto Save Stopped');
    return;
