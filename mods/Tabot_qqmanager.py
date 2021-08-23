
import CONSTS;


import time;
import logging;

VERSION = 'v20210823';
CONFIG = './config/autosave.json';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(name)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot QQ Manager Loaded');

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
# TB_Talker：Tabot组件，用于处理QQ的各类非聊天交互
""";

# 实现

def tellop(mmk, txt):
    mmk, msg = totxtmsg(mmk, txt);
    return;



# 回调接口

_tabot_cb_flt_muted_qq_self = {
    'mmk':{'mirai.*'},
    'msg':{'type':'BotMuteEvent'}
};
_tabot_cb_flt_muted_qq_all = {
    'mmk':{'mirai.*'},
    'msg':{'type':'GroupMuteAllEvent','current':True}
};
def _tabot_cb_fnc_muted(mmk, msg):
    _gid = msg['operator']['group']['id'];
    _gnm = msg['operator']['group']['name'];
    return;

_tabot_cb_flt_unmuted_qq_self = {
    'mmk':{'mirai.*'},
    'msg':{'type':'BotUnmuteEvent'}
};
_tabot_cb_flt_unmuted_qq_all = {
    'mmk':{'mirai.*'},
    'msg':{'type':'GroupMuteAllEvent','current':False}
};
def _tabot_cb_fnc_unmuted(mmk, msg):
    _gid = msg['operator']['group']['id'];
    _gnm = msg['operator']['group']['name'];
    return;

_tabot_cb_flt_joingroup_qq = {
    'mmk':{'mirai.*'},
    'msg':{'type':'BotJoinGroupEvent'}
};
def _tabot_cb_fnc_joingroup(mmk, msg):
    return;

_tabot_cb_flt_leavegroup_qq = {
    'mmk':{'mirai.*'},
    'msg':{'type':'BotLeaveEventActive'}
};
def _tabot_cb_fnc_leavegroup(mmk, msg):
    return;

_tabot_cb_flt_newmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'type':'MemberJoinEvent'}
};
def _tabot_cb_fnc_newmember(mmk, msg):
    return;

_tabot_cb_flt_invited_qq = {
    'mmk':{'mirai.*'},
    'msg':{'type':'BotInvitedJoinGroupRequestEvent'}
};
def _tabot_cb_fnc_invited(mmk, msg):
    _eid = msg['eventId'];
    _fid = msg['fromId'];
    _gid = msg['groupId'];
    _gnm = msg['groupName'];
    _cmd = {'content':{"eventId":_eid,"fromId":_fid,"groupId":_gid,"operate":0,"message":""}};
    _botcontrol.send(mmk, _cmd);
    tellop(mmk, '被邀请进入群%s(%s)'%(_gnm, _gid));
    return;

_mod_cbs.append({'fnc': _tabot_cb_fnc_muted,        'flt': _tabot_cb_flt_muted_qq_self,     'key': '_tabot_qm_cb_muted_qq_self'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_muted,        'flt': _tabot_cb_flt_muted_qq_all,      'key': '_tabot_qm_cb_muted_qq_all'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_unmuted,      'flt': _tabot_cb_flt_unmuted_qq_self,   'key': '_tabot_qm_cb_unmuted_qq_self'   });
_mod_cbs.append({'fnc': _tabot_cb_fnc_unmuted,      'flt': _tabot_cb_flt_unmuted_qq_all,    'key': '_tabot_qm_cb_unmuted_qq_all'    });
_mod_cbs.append({'fnc': _tabot_cb_fnc_joingroup,    'flt': _tabot_cb_flt_joingroup_qq,      'key': '_tabot_qm_cb_joingroup_qq'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_leavegroup,   'flt': _tabot_cb_flt_leavegroup_qq,     'key': '_tabot_qm_cb_leavegroup_qq'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_newmember,    'flt': _tabot_cb_flt_newmember_qq,      'key': '_tabot_qm_cb_newmember_qq'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_invited,      'flt': _tabot_cb_flt_invited_qq,        'key': '_tabot_qm_cb_invited_qq'        });



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot QQ Manager Stopped');
    return;
