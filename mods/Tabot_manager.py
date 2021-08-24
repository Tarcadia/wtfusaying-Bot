
import CONSTS;

from mods.Tabot_talker import fromtxtmsg;
from mods.Tabot_talker import totxtmsg;

import re;
import time;
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
logger.info('Tabot Manager Loaded');

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
    if re.match('mirai.*', mmk):
        _botcontrol.send(mmk, totxtmsg(mmk, CONSTS.BOT_OP_QQCID, txt));
    elif re.match('telegram.*', mmk):
        _botcontrol.send(mmk, totxtmsg(mmk, CONSTS.BOT_OP_TGCID, txt));
    return;



# 回调接口

# 禁言
_tabot_cb_flt_muted_qq_self = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotMuteEvent'}}
};
_tabot_cb_flt_muted_qq_all = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'GroupMuteAllEvent','current':True}}
};
def _tabot_cb_fnc_muted(mmk, msg):
    _gid = msg['data']['operator']['group']['id'];
    _gnm = msg['data']['operator']['group']['name'];
    logger.info('mmk: %s 在群%s(gid:%s)中被禁言'%(mmk, _gnm, _gid));
    tellop('mirai', 'mmk: %s 在群%s(gid:%s)中被禁言'%(mmk, _gnm, _gid));
    tellop('telegram', 'mmk: %s 在群%s(gid:%s)中被禁言'%(mmk, _gnm, _gid));
    return;

# 解除禁言
_tabot_cb_flt_unmuted_qq_self = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotUnmuteEvent'}}
};
_tabot_cb_flt_unmuted_qq_all = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'GroupMuteAllEvent','current':False}}
};
def _tabot_cb_fnc_unmuted(mmk, msg):
    _gid = msg['data']['operator']['group']['id'];
    _gnm = msg['data']['operator']['group']['name'];
    logger.info('mmk: %s 在群%s(gid:%s)中被解除禁言'%(mmk, _gnm, _gid));
    tellop('mirai', 'mmk: %s 在群%s(gid:%s)中被解除禁言'%(mmk, _gnm, _gid));
    tellop('telegram', 'mmk: %s 在群%s(gid:%s)中被解除禁言'%(mmk, _gnm, _gid));
    return;

# 加群
_tabot_cb_flt_joingroup_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotJoinGroupEvent'}}
};
def _tabot_cb_fnc_joingroup(mmk, msg):
    _gid = msg['data']['group']['id'];
    _gnm = msg['data']['group']['name'];
    logger.info('mmk: %s 进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    tellop('mirai', 'mmk: %s 进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    tellop('telegram', 'mmk: %s 进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    return;

# 退群
_tabot_cb_flt_leavegroup_qq_self = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotLeaveEventActive'}}
};
_tabot_cb_flt_leavegroup_qq_kick = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotLeaveEventKick'}}
};
def _tabot_cb_fnc_leavegroup(mmk, msg):
    _gid = msg['data']['group']['id'];
    _gnm = msg['data']['group']['name'];
    logger.info('mmk: %s 退出群%s(gid:%s)'%(mmk, _gnm, _gid));
    tellop('mirai', 'mmk: %s 退出群%s(gid:%s)'%(mmk, _gnm, _gid));
    tellop('telegram', 'mmk: %s 退出群%s(gid:%s)'%(mmk, _gnm, _gid));
    return;

# 群加人
_tabot_cb_flt_newmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'MemberJoinEvent'}}
};
def _tabot_cb_fnc_newmember(mmk, msg):
    _uid = msg['data']['member']['id'];
    _unm = msg['data']['member']['memberName'];
    _gid = msg['data']['member']['group']['id'];
    _gnm = msg['data']['member']['group']['name'];
    logger.info('mmk: %s 中%s(uid:%s)进入群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    tellop('mirai', 'mmk: %s 中%s(uid:%s)进入群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    tellop('telegram', 'mmk: %s 中%s(uid:%s)进入群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    return;

# 群踢人
_tabot_cb_flt_kickmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'MemberLeaveEventKick'}}
};
def _tabot_cb_fnc_kickmember(mmk, msg):
    _uid = msg['data']['member']['id'];
    _unm = msg['data']['member']['memberName'];
    _gid = msg['data']['member']['group']['id'];
    _gnm = msg['data']['member']['group']['name'];
    logger.info('mmk: %s 中%s(uid:%s)被踢出群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    tellop('mirai', 'mmk: %s 中%s(uid:%s)被踢出群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    tellop('telegram', 'mmk: %s 中%s(uid:%s)被踢出群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    return;

# 群退人
_tabot_cb_flt_quitmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'MemberLeaveEventQuit'}}
};
def _tabot_cb_fnc_quitmember(mmk, msg):
    _uid = msg['data']['member']['id'];
    _unm = msg['data']['member']['memberName'];
    _gid = msg['data']['member']['group']['id'];
    _gnm = msg['data']['member']['group']['name'];
    logger.info('mmk: %s 中%s(uid:%s)离开群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    tellop('mirai', 'mmk: %s 中%s(uid:%s)离开群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    tellop('telegram', 'mmk: %s 中%s(uid:%s)离开群%s(gid:%s)'%(mmk, _unm, _uid, _gnm, _gid));
    return;

# Bot被邀请加群
_tabot_cb_flt_invited_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotInvitedJoinGroupRequestEvent'}}
};
def _tabot_cb_fnc_invited(mmk, msg):
    _eid = msg['data']['eventId'];
    _fid = msg['data']['fromId'];
    _gid = msg['data']['groupId'];
    _gnm = msg['data']['groupName'];
    _cmd = {
        'command':'resp_botInvitedJoinGroupRequestEvent',
        'content':{"eventId":_eid,"fromId":_fid,"groupId":_gid,"operate":0,"message":""}
    };
    _botcontrol.send(mmk, _cmd);
    logger.info('mmk: %s 中被邀请进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    tellop('mirai', 'mmk: %s 中被邀请进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    tellop('telegram', 'mmk: %s 中被邀请进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    return;

# Bot指令
_tabot_cb_flt_help_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':'Tabot -help'}]}}
};
_tabot_cb_flt_help_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': 'Tabot -help'}}
};
def _tabot_cb_fnc_help(mmk, msg):
    _src, _txt = fromtxtmsg(mmk, msg);
    _msg = totxtmsg(mmk, _src['cid'], '对不起我帮不到你');
    _botcontrol.send(mmk, _msg);
    return;

_tabot_cb_flt_ping_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':'Tabot -ping'}]}}
};
_tabot_cb_flt_ping_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': 'Tabot -ping'}}
};
def _tabot_cb_fnc_ping(mmk, msg):
    _src, _txt = fromtxtmsg(mmk, msg);
    _msg = totxtmsg(mmk, _src['cid'], 'Pong!');
    _botcontrol.send(mmk, _msg);
    return;

_tabot_cb_flt_stop_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':'Tabot -stop'}], 'sender':{'id':CONSTS.BOT_OP_QQ}}}
};
_tabot_cb_flt_stop_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'from':{'id':CONSTS.BOT_OP_TG},'text': 'Tabot -stop'}}
};
def _tabot_cb_fnc_stop(mmk, msg):
    _src, _txt = fromtxtmsg(mmk, msg);
    _msg = totxtmsg(mmk, _src['cid'], '好我这就自闭');
    _botcontrol.send(mmk, _msg);
    _cmd = {'call':'stop', 'args':[]};
    _botcontrol.send('Loopback', _cmd);
    return;



# 注册
_mod_cbs.append({'fnc': _tabot_cb_fnc_muted,        'flt': _tabot_cb_flt_muted_qq_self,     'key': '_tabot_mn_cb_muted_qq_self'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_muted,        'flt': _tabot_cb_flt_muted_qq_all,      'key': '_tabot_mn_cb_muted_qq_all'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_unmuted,      'flt': _tabot_cb_flt_unmuted_qq_self,   'key': '_tabot_mn_cb_unmuted_qq_self'   });
_mod_cbs.append({'fnc': _tabot_cb_fnc_unmuted,      'flt': _tabot_cb_flt_unmuted_qq_all,    'key': '_tabot_mn_cb_unmuted_qq_all'    });
_mod_cbs.append({'fnc': _tabot_cb_fnc_joingroup,    'flt': _tabot_cb_flt_joingroup_qq,      'key': '_tabot_mn_cb_joingroup_qq'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_leavegroup,   'flt': _tabot_cb_flt_leavegroup_qq_self,'key': '_tabot_mn_cb_leavegroup_qq_self'});
_mod_cbs.append({'fnc': _tabot_cb_fnc_leavegroup,   'flt': _tabot_cb_flt_leavegroup_qq_kick,'key': '_tabot_mn_cb_leavegroup_qq_kick'});
_mod_cbs.append({'fnc': _tabot_cb_fnc_newmember,    'flt': _tabot_cb_flt_newmember_qq,      'key': '_tabot_mn_cb_newmember_qq'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_kickmember,   'flt': _tabot_cb_flt_kickmember_qq,     'key': '_tabot_mn_cb_kickmember_qq'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_quitmember,   'flt': _tabot_cb_flt_quitmember_qq,     'key': '_tabot_mn_cb_quitmember_qq'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_invited,      'flt': _tabot_cb_flt_invited_qq,        'key': '_tabot_mn_cb_invited_qq'        });

_mod_cbs.append({'fnc': _tabot_cb_fnc_help,         'flt': _tabot_cb_flt_help_qq,           'key': '_tabot_mn_cb_help_qq'           });
_mod_cbs.append({'fnc': _tabot_cb_fnc_help,         'flt': _tabot_cb_flt_help_tg,           'key': '_tabot_mn_cb_help_tg'           });
_mod_cbs.append({'fnc': _tabot_cb_fnc_ping,         'flt': _tabot_cb_flt_ping_qq,           'key': '_tabot_mn_cb_ping_qq'           });
_mod_cbs.append({'fnc': _tabot_cb_fnc_ping,         'flt': _tabot_cb_flt_ping_tg,           'key': '_tabot_mn_cb_ping_tg'           });
_mod_cbs.append({'fnc': _tabot_cb_fnc_stop,         'flt': _tabot_cb_flt_stop_qq,           'key': '_tabot_mn_cb_stop_qq'           });
_mod_cbs.append({'fnc': _tabot_cb_fnc_stop,         'flt': _tabot_cb_flt_stop_tg,           'key': '_tabot_mn_cb_stop_tg'           });



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Manager Stopped');
    return;
