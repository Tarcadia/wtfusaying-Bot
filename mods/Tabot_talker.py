
import CONSTS;
import exs.tabot_msgproc as tmsgp;
import exs.tabot_totalk as ttalk;

import logging;

VERSION = 'v20210823';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;35m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot Talker Loaded');

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
# Tabot Talker：Tabot组件，用于根据语境实现对话
""";

# 接口级实现

# 一条 Tabot 里的 message 应该在接口处就被翻译成统一的形式，通过'<mmk>.<cid>'的形式实现唯一的对话场景的标识；
# 在内部处理时应当用统一的逻辑处理统一的 Tabot Message 形式，将一条消息视作一个对话场景里的一个上下文元素；
# 一条 Tabot 中的 message 应当是保护“来源”（src）或“去向”（tgt），和消息内容本体（msg）的；
# Tabot_talker中的miraitxtmsg，tgtxtmsg，totxtmsg接口应当是有高优先级的，作为Tabot中通用的txtmsg处理接口；
# 这些消息管理的消息在exs.tabot_msgproc中定义;


# 本地实现
def on_atme(src, txt):
    return;

# 回调接口

_tabot_cb_flt_atme_qqgroup = {
    'mmk':{'mirai.*'},
    'msg':{'data':{'type':'GroupMessage','messageChain':[{'type':'At','target':CONSTS.BOT_QQ}]}}
};
_tabot_cb_flt_atme_tggroup = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': '.*@%s.*' % CONSTS.BOT_TG, 'entities': [{'type': 'mention'}]}}
};
def _tabot_cb_fnc_atme(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    on_atme(_src, msg);
    return;

_mod_cbs.append({'fnc': _tabot_cb_fnc_atme,         'flt': _tabot_cb_flt_atme_qqgroup,      'key': '_tabot_talker_cb_atme_qqgroup'  });
_mod_cbs.append({'fnc': _tabot_cb_fnc_atme,         'flt': _tabot_cb_flt_atme_tggroup,      'key': '_tabot_talker_cb_atme_tggroup'  });





# 主流程接口函数

# 启动
def start():
    return [];

# 保存
def save():
    tmsgp.save();
    ttalk.save();
    return;

# 停止
def stop():
    logger.info('Tabot Talker Stopped');
    return;
