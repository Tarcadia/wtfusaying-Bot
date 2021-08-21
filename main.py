
import CONSTS;
import mods;
import botcontrol as bc;
import iomessagemanager as iomm;
import miraimessagemanager as mmm;
import tgmessagemanager as tmm;
import logging;

VERSION = 'v20210820';
THREADS = [];

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(format='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
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


# 底层系统组件实现

def reload():
    import mods as _mods;
    mods = _mods;
    mods.loader.load();
    for _cb in mods.loader.regs:
        _bc.regcallback(_cb['fnc'], _cb['flt']);

# 底层系统组件接口

_sys_cb_flt_reload = {
    'mmk'               : {'IO'},
    'msg'               : {
        'msgs'          : 'reload',
        'args'          : None
    }
};

def _sys_cb_fnc_reload(mmk, msg):
    reload();

def main():
    # 注册各个messagemanager类的接口到BotControl
    _bc.regmessagemanager(_mmm, 'mirai');
    _bc.regmessagemanager(_tmm, 'telegram');
    _bc.regmessagemanager(_iomm, 'IO');
    
    # 注册各个callback接口到BotControl
    _bc.regcallback(_sys_cb_fnc_reload, _sys_cb_flt_reload);

    # 启动Polling
    for _part in [
        _iomm,
        _mmm,
        _tmm
    ]:
        THREADS.extend(_part.threadpolling());

    return;

if __name__ == '__main__':
    main();