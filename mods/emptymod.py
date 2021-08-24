
import logging;

VERSION = 'v20210823';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[1;34m[%(asctime)s][%(levelname)s]\033[0;32m[%(name)s]\033[0m >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Empty Mod Loaded');

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
# Empty Mod：毫无用处的mod模板
""";

# 接口级实现
# def func()

# 本地实现
def on_event(msg):
    return;

# 回调接口
_emptymod_cb_flt_event = {};
def _emptymod_cb_fnc_event(mmk, msg):
    on_event(msg);
    return;

_mod_cbs.append({'fnc': _emptymod_cb_fnc_event,     'flt': _emptymod_cb_flt_event,          'key': '_emptymod_cb_func'              });
#_mod_cbs.append({'fnc': _emptymod_cb_fnc_event,     'flt': _emptymod_cb_flt_event,          'key': '_emptymod_cb_func'              });
#_mod_cbs.append({'fnc': _emptymod_cb_fnc_event,     'flt': _emptymod_cb_flt_event,          'key': '_emptymod_cb_func'              });
#_mod_cbs.append({'fnc': _emptymod_cb_fnc_event,     'flt': _emptymod_cb_flt_event,          'key': '_emptymod_cb_func'              });



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Talker Stopped');
    return;
