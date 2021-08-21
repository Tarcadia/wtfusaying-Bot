
import CONSTS;

import botcontrol as bc;

import iomessagemanager as iomm;
import miraimessagemanager as mmm;
import tgmessagemanager as tmm;

import mods;

import logging;

VERSION = 'v20210820';
THREADS = [];

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Main Loaded');




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

_sys_cb_ = [];
_sys_doc = """
help        : 获取帮助
reload      : 重载组件
    -a      : 重载全部组件
    -m <m>  : 重载单个组件m
""";


# 底层系统组件实现

def reloadall():
    import mods as _mods;
    mods = _mods;
    # 1. 加载各个模块组件
    # 2. 启动各个模块组件
    # 3. 重注册接口
    _bc.clearcb();
    for _cb in _sys_cb_:
        _bc.regcallback(_cb['fnc'], _cb['flt'], _cb['key']);
    #for _cb in _______:
    #    _bc.regcallback(_cb['fnc'], _cb['flt']);
    return;

def reload(modlist: list = []):
    return;

def stop():
    # 关闭BotControl
    _bc.threadstop();
    # 关闭各个MM
    _iomm.threadstop();
    _mmm.threadstop();
    _tmm.threadstop();
    # 关闭各个组件
    #####
    return;


# 底层系统组件接口

_sys_cb_flt_echo = {'mmk' : {'mirai', 'telegram'}, 'msg' : {}};
def _sys_cb_fnc_echo(mmk, msg):
    logger.info(msg);

_sys_cb_flt_help = {'mmk' : {'IO'}, 'msg' : {'call' : 'help'}};
def _sys_cb_fnc_help(mmk, msg):
    _bc.send(mmk, _sys_doc);
    # 各个模块的help

_sys_cb_flt_reload = {'mmk' : {'IO'}, 'msg' : {'call' : 'reload'}};
def _sys_cb_fnc_reload(mmk, msg):
    if msg['args']:
        if msg['args'][0] == '-a':
            reloadall();
        elif msg['args'][0] == '-m':
            reload(msg['args'][1:]);
        else:
            _bc.send(mmk, '参数不对，help一下');

_sys_cb_.append({'fnc': _sys_cb_fnc_echo, 'flt': _sys_cb_flt_echo, 'key': '_sys_cb_echo'});
_sys_cb_.append({'fnc': _sys_cb_fnc_reload, 'flt': _sys_cb_flt_reload, 'key': '_sys_cb_reload'});



# main
def main():
    # 注册各个messagemanager类的接口到BotControl
    _bc.regmessagemanager(_mmm, 'mirai');
    _bc.regmessagemanager(_tmm, 'telegram');
    _bc.regmessagemanager(_iomm, 'IO');
    # 注册各个callback接口到BotControl
    for _cb in _sys_cb_:
        _bc.regcallback(_cb['fnc'], _cb['flt'], _cb['key']);
    # 启动各个组件
    #####
    # 启动各个MM
    for _mm in [
        _iomm,
        _mmm,
        _tmm
    ]:
        _mm.open();
        _mm_thrs = _mm.threadpolling();
        THREADS.extend(_mm_thrs);
    # 启动BotControl
    _bc_thrs = _bc.threadpolling();
    THREADS.extend(_bc_thrs);
    return;

if __name__ == '__main__':
    main();