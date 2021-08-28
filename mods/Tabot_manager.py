
import CONSTS;
import exs.tabot_msgproc as tmsgp;

import re;
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
# Tabot Manager：Tabot组件，用于处理各类非聊天交互
# 一般来说，我帮不到你，但如果你执意需要帮助的话，以下的信息可能在某些情况下会是对你调用执行的一种协助性指示
t                                   : 在聊天环境中调用以实现相关功能
    -help                           : 在聊天环境中展示帮助信息
    -ping                           : 在聊天环境中Ping本聊天处理系统，执行取决于架构实现下实际的作用效果
    -reload                         : 在特定的开发环境下应当执行环境支持的组件重载功能，需要是OP才可以执行
    -stop                           : 在特定的开发环境下应当执行环境支持的系统关闭功能，需要是OP才可以执行
""";



# tabot的全局变量
_tabot_cmd_help = 't -help';
_tabot_cmd_ping = 't -ping';
_tabot_cmd_reload = 't -reload';
_tabot_cmd_stop = 't -stop';
_tabot_cmd_help_doc = """
一般来说，我帮不到你。
但如果你执意需要帮助的话，以下的信息可能在某些情况下会是对你调用执行的一种协助性指示
t               : 在聊天环境中调用以实现相关功能
    -help       : 在聊天环境中展示帮助信息
    -ping       : 在聊天环境中Ping本聊天处理系统，执行取决于架构实现下实际的作用效果
    -reload     : 在特定的开发环境下应当执行环境支持的组件重载功能
    -stop       : 在特定的开发环境下应当执行环境支持的系统关闭功能
    -henshin    : 变身
    -reboot     : 并不能控制重启
""";


# 实现

def _tellop(mmk, txt):
    if re.match('mirai.*', mmk):
        _botcontrol.send(mmk, tmsgp.totxtmsg(mmk, CONSTS.BOT_OP_QQCID, txt));
    elif re.match('telegram.*', mmk):
        _botcontrol.send(mmk, tmsgp.totxtmsg(mmk, CONSTS.BOT_OP_TGCID, txt));
    return;



# 回调接口

_tabot_cb_flt_msgecho = {
    'mmk':{'mirai.*', 'telegram.*'},
    'msg':{}
};
def _tabot_cb_fnc_msgecho(mmk, msg):
    if re.match('mirai.*', mmk):
        _cmd = {'mmk': mmk, 'syncid': msg['syncId']};
        _cmd.update(msg['data']);
        _botcontrol.send('IO', _cmd);
    elif re.match('telegram.*', mmk):
        _cmd = {'mmk': mmk, 'syncid': msg['update_id']};
        _cmd.update(msg['message']);
        _botcontrol.send('IO', _cmd);
    return;

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
    logger.info('mmk: %s 在群%s(gid:%s)中被禁言' % (mmk, _gnm, _gid));
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
    logger.info('mmk: %s 在群%s(gid:%s)中被解除禁言' % (mmk, _gnm, _gid));
    return;

# 加群
_tabot_cb_flt_joingroup_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotJoinGroupEvent'}}
};
def _tabot_cb_fnc_joingroup(mmk, msg):
    _gid = msg['data']['group']['id'];
    _gnm = msg['data']['group']['name'];
    logger.info('mmk: %s 进入群%s(gid:%s)' % (mmk, _gnm, _gid));
    logger.info('mmk: %s 进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    _tellop('mirai', 'mmk: %s 进入群%s(gid:%s)'%(mmk, _gnm, _gid));
    _tellop('telegram', 'mmk: %s 进入群%s(gid:%s)'%(mmk, _gnm, _gid));
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
    logger.info('mmk: %s 退出群%s(gid:%s)' % (mmk, _gnm, _gid));
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
    logger.info('mmk: %s 中%s(uid:%s)进入群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
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
    logger.info('mmk: %s 中%s(uid:%s)被踢出群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
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
    logger.info('mmk: %s 中%s(uid:%s)离开群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
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
        'command': 'resp_botInvitedJoinGroupRequestEvent',
        'content': {"eventId":_eid, "fromId":_fid, "groupId":_gid, "operate":0, "message":""}
    };
    _botcontrol.send(mmk, _cmd);
    logger.info('mmk: %s 中被邀请进入群%s(gid:%s)' % (mmk, _gnm, _gid));
    return;

# Bot指令
_tabot_cb_flt_help_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_help}]}}
};
_tabot_cb_flt_help_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': _tabot_cmd_help}}
};
def _tabot_cb_fnc_help(mmk, msg):
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    _msg = tmsgp.totxtmsg(mmk, _src['cid'], _tabot_cmd_help_doc);
    _botcontrol.send(mmk, _msg);
    return;

_tabot_cb_flt_ping_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_ping}]}}
};
_tabot_cb_flt_ping_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': _tabot_cmd_ping}}
};
def _tabot_cb_fnc_ping(mmk, msg):
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    _msg = tmsgp.totxtmsg(mmk, _src['cid'], 'Pong!');
    _botcontrol.send(mmk, _msg);
    return;

_tabot_cb_flt_reload_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_reload}], 'sender':{'id':CONSTS.BOT_OP_QQ}}}
};
_tabot_cb_flt_reload_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'from':{'id':CONSTS.BOT_OP_TG},'text': _tabot_cmd_reload}}
};
def _tabot_cb_fnc_reload(mmk, msg):
    _cmd = {'call': 'reload', 'args': ['-a']};
    _botcontrol.send('Loopback', _cmd);
    return;

_tabot_cb_flt_stop_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_stop}], 'sender':{'id':CONSTS.BOT_OP_QQ}}}
};
_tabot_cb_flt_stop_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'from':{'id':CONSTS.BOT_OP_TG},'text': _tabot_cmd_stop}}
};
def _tabot_cb_fnc_stop(mmk, msg):
    _cmd = {'call': 'stop', 'args': []};
    _botcontrol.send('Loopback', _cmd);
    return;



# 注册
_mod_cbs.append({'fnc': _tabot_cb_fnc_msgecho,      'flt': _tabot_cb_flt_msgecho,           'key': '_tabot_mn_cb_msgecho'           });
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
_mod_cbs.append({'fnc': _tabot_cb_fnc_reload,       'flt': _tabot_cb_flt_reload_qq,         'key': '_tabot_mn_cb_reload_qq'         });
_mod_cbs.append({'fnc': _tabot_cb_fnc_reload,       'flt': _tabot_cb_flt_reload_tg,         'key': '_tabot_mn_cb_reload_tg'         });
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
