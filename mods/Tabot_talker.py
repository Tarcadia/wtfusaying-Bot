
import CONSTS;
import exs.tabot_msgproc as tmsgp;

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
# TB_Talker：Tabot组件，用于根据语境实现对话
""";

# 接口级实现

# 一条 Tabot 里的 message 应该在接口处就被翻译成统一的形式，通过'<mmk>.<cid>'的形式实现唯一的对话场景的标识；
# 在内部处理时应当用统一的逻辑处理统一的 Tabot Message 形式，将一条消息视作一个对话场景里的一个上下文元素；
# 一条 Tabot 中的 message 应当是保护“来源”（src）或“去向”（tgt），和消息内容本体（msg）的；
# Tabot_talker中的miraitxtmsg，tgtxtmsg，totxtmsg接口应当是有高优先级的，作为Tabot中通用的txtmsg处理接口；

# src               : dict          // 一条Tabot里的message的来源的表示
# {
#   'mmk'           : mmk,          // 来源mmk，
#   'cid'           : id,           // 来源chatid，形如'p<xxxxx>'或'g<xxxxx>'
#                                   // p表示是私戳，g是群聊，c是channel，特别的，u表示未识别
#                                   // <xxxxx>是qq号、qq群号、tg的chatid
#   'uid'           : id,           // 来源userid，是qq号或者tg的user的id
#   'mid'           : id,           // 消息的id，qq和tg的id
#   'time'          : time          // 消息的时间
# }

# tgt               : dict          // 一条Tabot里的message的去向的表示
# {
#   'mmk'           : mmk,          // 去向mmk，
#   'cid'           : id,           // 去向chatid，
# }



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
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    on_atme(_src, _txt);
    return;

_mod_cbs.append({'fnc': _tabot_cb_fnc_atme,         'flt': _tabot_cb_flt_atme_qqgroup,      'key': '_tabot_talker_cb_atme_qqgroup'  });
_mod_cbs.append({'fnc': _tabot_cb_fnc_atme,         'flt': _tabot_cb_flt_atme_tggroup,      'key': '_tabot_talker_cb_atme_tggroup'  });



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Talker Stopped');
    return;
