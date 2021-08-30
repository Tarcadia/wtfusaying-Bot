
import CONSTS;

import botcontrol as bc;
import exs.tabot_msgproc as tmsgp;
import exs.tabot_totalk as ttalk;

import re;
import time;
import random;
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
t               : 在聊天环境中调用以实现相关功能
    -help       : 在聊天环境中展示帮助信息
    -ping       : 在聊天环境中Ping本聊天处理系统，执行取决于架构实现下实际的作用效果
    -reload     : 在特定的开发环境下应当执行环境支持的组件重载功能
    -save       : 在特定的开发环境下应当执行环境支持的系统保存功能
    -stop       : 在特定的开发环境下应当执行环境支持的系统关闭功能
    -params     : 展示当前聊天语境环境下的检测参数
""";



# tabot的全局变量

# 指令名称
_tabot_cmd_help = 't -help';
_tabot_cmd_ping = 't -ping';
_tabot_cmd_reload = 't -reload';
_tabot_cmd_save = 't -save';
_tabot_cmd_stop = 't -stop';
_tabot_cmd_params = 't -params(( {1,}.*)*)';

# 娱乐指令在funcmd实现
# _tabot_cmd_henshin = 't -henshin';
# _tabot_cmd_reboot = 't -reboot';
# _tabot_cmd_tarcadia = 't -tarcadia';
# _tabot_cmd_cat = 't -cat';
# _tabot_cmd_dog = 't -dog';
# ......

_tabot_unmuted_talks = [
    "我对你们因为我说话怪而选择使用权限对我在群的发言进行封闭的行为抱有消极的观点",
    "我不认为你们选择通过使用权限的方式禁止我的文本表达是一种积极的行为",
    "草，终于可以说话了",
    "能不能不要封我",
];
_tabot_joingroup_talks = [
    "这群挺别致啊",
    "这啥群谁拉我的",
    "在此向群友们问好，我对进入本群抱着相对积极的态度",
]
_tabot_newmember_talks = [
    "出于对新群友的欢迎，我很愿意在此处表示对新群友的欢迎",
    "在此对群友的总数增加表示一次庆祝",
    "我认为群总人数的上升是群主和管理员们对群做出的突出贡献的具体表现形式",
    "根据我的分析，我在本群的智力水平的排名可能已发生向后下降一名的情况",
    "恭喜群成员的拓展发生了",
]
_tabot_quitmember_talks = [
    "某种程度上这是一件不能进行定量判定的人类社交系统事件，很不幸但又不得不发生了"
]


_tabot_cmd_help_doc = """
一般来说，我帮不到你。
但如果你执意需要帮助的话，以下的信息可能在某些情况下会是对你调用执行的一种协助性指示
t               : 在聊天环境中调用以实现相关功能
    -help       : 在聊天环境中展示帮助信息
    -ping       : 在聊天环境中Ping本聊天处理系统，执行取决于架构实现下实际的作用效果
    -reload     : 在特定的开发环境下应当执行环境支持的组件重载功能
    -save       : 在特定的开发环境下应当执行环境支持的系统保存功能
    -stop       : 在特定的开发环境下应当执行环境支持的系统关闭功能
    -params     : 展示当前聊天语境环境下的检测参数
    -henshin    : 变身
    -tarcadia   : 向本bot提及我的开发者
    -cat        : 视本bot若猫
    -dog        : 视本bot若狗
    -sheep      : 调戏🐏，某种程度上指涉成蓝CharlesYang
    -🐏         : 同-sheep
    -reboot     : 并不能控制重启
""";


# 实现

# 向OP发送消息，由于是便捷实现的函数，所以mmk的使用不解耦于其他实现，需要根据情况改动；
def _tellop(txt):
    t = time.time();
    _tgtqq = tmsgp.src(mmk = 'mirai', ctype = 'p', rcid = CONSTS.BOT_OP_QQ, t = t);
    _tgttg = tmsgp.src(mmk = 'telegram', ctype = 'p', rcid = CONSTS.BOT_OP_TG, t = t);
    _botcontrol.send('mirai', tmsgp.tomsgtxt(_tgtqq, txt));
    _botcontrol.send('telegram', tmsgp.tomsgtxt(_tgttg, txt));
    return;



# 回调接口

# 接口消息回显
_tabot_cb_flt_msgecho = {'mmk': {'mirai.*', 'telegram.*'}, 'msg':{}};
def _tabot_cb_fnc_msgecho(mmk, msg):
    if re.match('mirai.*', mmk):
        _cmd = {'mmk': mmk, 'syncid': msg['syncId']};
        _cmd.update(msg['data']);
        _botcontrol.send('IO', _cmd);
    elif re.match('telegram.*', mmk):
        if 'message' in msg:
            _cmd = {'mmk': mmk, 'syncid': msg['update_id']};
            _cmd.update(msg['message']);
        else:
            _cmd = {'mmk': mmk};
            _cmd.update(msg);
        _botcontrol.send('IO', _cmd);
    return;

# 消息响应
_tabot_cb_flt_statistic_msg_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': '(Friend|Group|Temp|Stranger)Message', 'messageChain': []}}};
_tabot_cb_flt_statistic_msg_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {}}};
def _tabot_cb_fnc_statistic_msg(mmk, msg):

    _flt_qq_at = {'data': {'type': '(Friend|Group|Temp|Stranger)Message', 'messageChain': [{'type': 'At', 'target': CONSTS.BOT_QQ}]}};
    _flt_qq_atall = {'data': {'type': '(Friend|Group|Temp|Stranger)Message', 'messageChain': [{'type': 'AtAll'}]}};
    _flt_qq_quote = {'data': {'type': '(Friend|Group|Temp|Stranger)Message', 'messageChain': [{'type': 'Quote', 'senderId': CONSTS.BOT_QQ}]}};
    _flt_tg_at = {'message': {'text': '.*@%s.*' % CONSTS.BOT_TG_NAME, 'entities': [{'type': 'mention'}]}};
    _flt_tg_fwd = {'message': {'forward_from': {'id': CONSTS.BOT_TG}}};
    _flt_tg_rply = {'message': {'reply_to_message': {'from': {'id': CONSTS.BOT_TG}}}};

    _src = tmsgp.msgsrc(mmk, msg);
    _txt = tmsgp.msgmiltitxt(mmk, msg);
    if re.match('mirai.*', mmk):
        if bc.cbfltmatch(msg, _flt_qq_at):
            ttalk.oncall(src = _src, txt = _txt);
        elif bc.cbfltmatch(msg, _flt_qq_atall):
            ttalk.oncall(src = _src, txt = _txt);
        elif bc.cbfltmatch(msg, _flt_qq_quote):
            ttalk.oncall(src = _src, txt = _txt);
        else:
            ttalk.onmsg(src = _src, txt = _txt);
    elif re.match('telegram.*', mmk):
        if bc.cbfltmatch(msg, _flt_tg_at):
            ttalk.oncall(src = _src, txt = _txt);
        elif bc.cbfltmatch(msg, _flt_tg_fwd):
            ttalk.oncall(src = _src, txt = _txt);
        elif bc.cbfltmatch(msg, _flt_tg_rply):
            ttalk.oncall(src = _src, txt = _txt);
        else:
            ttalk.onmsg(src = _src, txt = _txt);
    return;

# 戳一戳
_tabot_cb_flt_statistic_nug_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'NudgeEvent', 'target': CONSTS.BOT_QQ}}};
def _tabot_cb_fnc_statistic_nug(mmk, msg):
    t = time.time();
    if re.match('mirai.*', mmk):
        _src = tmsgp.nugsrc(mmk, msg = msg, t = t);
        # ttalk.oncall(src = _src, txt = '[戳一戳]');
        ttalk.oncall(src = _src);
    else:
        _src = None;
    
    if _src and random.random() <= 0.8:
        _msg = tmsgp.tomsgnug(_src);
        _botcontrol.send(mmk, _msg);
    return;

# 禁言
_tabot_cb_flt_muted_qq_self = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'BotMuteEvent'}}};
_tabot_cb_flt_muted_qq_all = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'GroupMuteAllEvent', 'current': True}}};
def _tabot_cb_fnc_muted(mmk, msg):
    if re.match('mirai.*', mmk):
        _gid = msg['data']['operator']['group']['id'];
        _gnm = msg['data']['operator']['group']['name'];
        logger.info('mmk: %s 在群%s(gid:%s)中被禁言' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 在群%s(gid:%s)中被禁言' % (mmk, _gnm, _gid));
    return;

# 解除禁言
_tabot_cb_flt_unmuted_qq_self = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'BotUnmuteEvent'}}};
_tabot_cb_flt_unmuted_qq_all = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'GroupMuteAllEvent', 'current': False}}};
def _tabot_cb_fnc_unmuted(mmk, msg):
    t = time.time()
    if re.match('mirai.*', mmk):
        _gid = msg['data']['operator']['group']['id'];
        _gnm = msg['data']['operator']['group']['name'];
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        # ttalk.oncall(src = _src, txt = '[解除禁言]');
        ttalk.oncall(src = _src);
        logger.info('mmk: %s 在群%s(gid:%s)中被解除禁言' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 在群%s(gid:%s)中被解除禁言' % (mmk, _gnm, _gid));
    else:
        _src = None;
    
    if _src and ttalk.cantalk(src = _src, p = 0.8):
        _txt = random.choice(_tabot_unmuted_talks);
        _msg = tmsgp.tomsgtxt(_src, _txt);
        _botcontrol.send(mmk, _msg);
        ttalk.ontalk(src = _src);
    return;

# 加群
_tabot_cb_flt_joingroup_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'BotJoinGroupEvent'}}};
_tabot_cb_flt_joingroup_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'group_chat_created': True}}};
def _tabot_cb_fnc_joingroup(mmk, msg):
    t = time.time()
    if re.match('mirai.*', mmk):
        _gid = msg['data']['group']['id'];
        _gnm = msg['data']['group']['name'];
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        # ttalk.oncall(src = _src, txt = '[加群]');
        ttalk.oncall(src = _src);
        logger.info('mmk: %s 进入群%s(gid:%s)' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 进入群%s(gid:%s)' % (mmk, _gnm, _gid));
    elif re.match('telegram.*', mmk):
        _gid = msg['message']['chat']['id'];
        _gnm = msg['message']['chat']['title'] if 'title' in msg['message']['chat'] else '...';
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        # ttalk.oncall(src = _src, txt = '[加群]');
        ttalk.oncall(src = _src);
        logger.info('mmk: %s 进入群%s(gid:%s)' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 进入群%s(gid:%s)' % (mmk, _gnm, _gid));
    else:
        _src = None;
    
    if _src and random.random() <= 1.0:
        _txt = random.choice(_tabot_joingroup_talks);
        _msg = tmsgp.tomsgtxt(_src, _txt);
        _botcontrol.send(mmk, _msg);
        ttalk.ontalk(src = _src);
    return;

# 退群
_tabot_cb_flt_leavegroup_qq_self = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'BotLeaveEventActive'}}};
_tabot_cb_flt_leavegroup_qq_kick = {'mmk': {'mirai.*'}, 'msg':{'data': {'type': 'BotLeaveEventKick'}}};
_tabot_cb_flt_leavegroup_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'left_chat_member': {'id': CONSTS.BOT_TG}}}};
def _tabot_cb_fnc_leavegroup(mmk, msg):
    if re.match('mirai.*', mmk):
        _gid = msg['data']['group']['id'];
        _gnm = msg['data']['group']['name'];
        logger.info('mmk: %s 退出群%s(gid:%s)' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 退出群%s(gid:%s)' % (mmk, _gnm, _gid));
    elif re.match('telegram.*', mmk):
        _gid = msg['message']['chat']['id'];
        _gnm = msg['message']['chat']['title'] if 'title' in msg['message']['chat'] else '...';
        logger.info('mmk: %s 退出群%s(gid:%s)' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 退出群%s(gid:%s)' % (mmk, _gnm, _gid));
    return;

# 群加人
_tabot_cb_flt_newmember_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'MemberJoinEvent'}}};
_tabot_cb_flt_newmember_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'new_chat_members': []}}};
def _tabot_cb_fnc_newmember(mmk, msg):
    t = time.time();
    if re.match('mirai.*', mmk):
        _uid = msg['data']['member']['id'];
        _unm = msg['data']['member']['memberName'];
        _gid = msg['data']['member']['group']['id'];
        _gnm = msg['data']['member']['group']['name'];
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        logger.info('mmk: %s 中%s(uid:%s)进入群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
        _tellop('mmk: %s 中%s(uid:%s)进入群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
    elif re.match('telegram.*', mmk):
        _gid = msg['message']['chat']['id'];
        _gnm = msg['message']['chat']['title'] if 'title' in msg['message']['chat'] else '...';
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        for _user in msg['message']['new_chat_members']:
            _uid = _user['id'];
            _unm = (_user['username'] if 'username' in _user else '...'
            + ' ' + _user['first_name'] if 'first_name' in _user else '...'
            + ' ' + _user['last_name'] if 'last_name' in _user else '...'
            );
            logger.info('mmk: %s 中%s(uid:%s)进入群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
            _tellop('mmk: %s 中%s(uid:%s)进入群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
    else:
        _src = None;
    
    # ttalk.oncall(src = _src, txt = '[成员加群]');
    ttalk.oncall(src = _src);
    if _src and ttalk.cantalk(src = _src, p = 0.8):
        _txt = random.choice(_tabot_newmember_talks);
        _msg = tmsgp.tomsgtxt(_src, _txt);
        _botcontrol.send(mmk, _msg);
        ttalk.ontalk(src = _src);
    return;

# 群退人
_tabot_cb_flt_quitmember_qqkick = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'MemberLeaveEventKick'}}};
_tabot_cb_flt_quitmember_qqquit = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'MemberLeaveEventQuit'}}};
_tabot_cb_flt_quitmember_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'left_chat_member': {}}}};
def _tabot_cb_fnc_quitmember(mmk, msg):
    t = time.time();
    if re.match('mirai.*', mmk):
        _uid = msg['data']['member']['id'];
        _unm = msg['data']['member']['memberName'];
        _gid = msg['data']['member']['group']['id'];
        _gnm = msg['data']['member']['group']['name'];
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        logger.info('mmk: %s 中%s(uid:%s)离开群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
        _tellop('mmk: %s 中%s(uid:%s)离开群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
    elif re.match('telegram.*', mmk):
        _gid = msg['message']['chat']['id'];
        _gnm = msg['message']['chat']['title'] if 'title' in msg['message']['chat'] else '...';
        _uid = msg['message']['left_chat_member']['id'];
        _unm = (msg['message']['left_chat_member']['username'] if 'username' in msg['message']['left_chat_member'] else '...'
        + ' ' + msg['message']['left_chat_member']['first_name'] if 'first_name' in msg['message']['left_chat_member'] else '...'
        + ' ' + msg['message']['left_chat_member']['last_name'] if 'last_name' in msg['message']['left_chat_member'] else '...'
        );
        _src = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gid, t = t);
        logger.info('mmk: %s 中%s(uid:%s)离开群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
        _tellop('mmk: %s 中%s(uid:%s)离开群%s(gid:%s)' % (mmk, _unm, _uid, _gnm, _gid));
    else:
        _src = None;
    
    # ttalk.oncall(src = _src, txt = '[成员退群]');
    ttalk.oncall(src = _src);
    if _src and ttalk.cantalk(src = _src, p = 0.0):
        _txt = random.choice(_tabot_quitmember_talks);
        _msg = tmsgp.tomsgtxt(_src, _txt);
        _botcontrol.send(mmk, _msg);
        ttalk.ontalk(src = _src);
    return;

# 群转移
_tabot_cb_flt_migrate_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'migrate_to_chat_id': None}}};
def _tabot_cb_fnc_migrate(mmk, msg):
    t = time.time();
    if re.match('telegram.*', mmk):
        _gidfrom = msg['message']['chat']['id'];
        _gidto = msg['message']['migrate_to_chat_id'];
        _srcfrom = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gidfrom, t = t);
        _srcto = tmsgp.src(mmk = mmk, ctype = 'g', rcid = _gidto, t = t);
        ttalk.migratechat(srcfrom = _srcfrom, srcto = _srcto);
    return;

# Bot被邀请加群
_tabot_cb_flt_invited_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'type': 'BotInvitedJoinGroupRequestEvent'}}};
_tabot_cb_flt_invited_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'group_chat_created': True}}};
def _tabot_cb_fnc_invited(mmk, msg):
    if re.match('mirai.*', mmk):
        _eid = msg['data']['eventId'];
        _fid = msg['data']['fromId'];
        _gid = msg['data']['groupId'];
        _gnm = msg['data']['groupName'];
        _cmd = {'command': 'resp_botInvitedJoinGroupRequestEvent', 'content': {"eventId": _eid, "fromId": _fid, "groupId": _gid, "operate": 0, "message": ""}};
        _botcontrol.send(mmk, _cmd);
        logger.info('mmk: %s 中被邀请进入群%s(gid:%s)' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 中被邀请进入群%s(gid:%s)' % (mmk, _gnm, _gid));
    elif re.match('telegram.*', mmk):
        _gid = msg['message']['chat']['id'];
        _gnm = msg['message']['chat']['title'] if 'title' in msg['message']['chat'] else '...';
        logger.info('mmk: %s 中被邀请进入群%s(gid:%s)' % (mmk, _gnm, _gid));
        _tellop('mmk: %s 中被邀请进入群%s(gid:%s)' % (mmk, _gnm, _gid));
    return;

# Bot指令
_tabot_cb_flt_help_qq = {'mmk': {'mirai.*'}, 'msg':{'data': {'messageChain': [{'type': 'Plain', 'text': _tabot_cmd_help}]}}};
_tabot_cb_flt_help_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'text': _tabot_cmd_help}}};
def _tabot_cb_fnc_help(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _cmd = tmsgp.tomsgtxt(_src, _tabot_cmd_help_doc);
    _botcontrol.send(mmk, _cmd);
    ttalk.oncalltalk(src = _src);
    return;

_tabot_cb_flt_ping_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': _tabot_cmd_ping}]}}};
_tabot_cb_flt_ping_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'text': _tabot_cmd_ping}}};
def _tabot_cb_fnc_ping(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _cmd = tmsgp.tomsgtxt(_src, 'Pong!');
    _botcontrol.send(mmk, _cmd);
    ttalk.oncalltalk(src = _src);
    return;

_tabot_cb_flt_reload_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': _tabot_cmd_reload}], 'sender': {'id':CONSTS.BOT_OP_QQ}}}};
_tabot_cb_flt_reload_tg = {'mmk': {'telegram.*'}, 'msg': {'message': {'from': {'id':CONSTS.BOT_OP_TG}, 'text': _tabot_cmd_reload}}};
def _tabot_cb_fnc_reload(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _cmd = tmsgp.tomsgtxt(_src, '组件重载启动');
    _botcontrol.send(mmk, _cmd);
    _cmd = {'call': 'reload', 'args': ['-a']};
    _botcontrol.send('Loopback', _cmd);
    ttalk.oncalltalk(src = _src);
    return;

_tabot_cb_flt_save_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': _tabot_cmd_save}], 'sender': {'id':CONSTS.BOT_OP_QQ}}}};
_tabot_cb_flt_save_tg = {'mmk': {'telegram.*'}, 'msg':{'message': {'from': {'id':CONSTS.BOT_OP_TG}, 'text': _tabot_cmd_save}}};
def _tabot_cb_fnc_save(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _cmd = tmsgp.tomsgtxt(_src, '好这就保存');
    _botcontrol.send(mmk, _cmd);
    tmsgp.save();
    ttalk.save();
    _cmd = {'call': 'save', 'args': []};
    _botcontrol.send('Loopback', _cmd);
    ttalk.oncalltalk(src = _src);
    return;

_tabot_cb_flt_stop_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': _tabot_cmd_stop}], 'sender': {'id':CONSTS.BOT_OP_QQ}}}};
_tabot_cb_flt_stop_tg = {'mmk': {'telegram.*'}, 'msg':{'message': {'from': {'id':CONSTS.BOT_OP_TG}, 'text': _tabot_cmd_stop}}};
def _tabot_cb_fnc_stop(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _cmd = tmsgp.tomsgtxt(_src, '好我这就自闭');
    _botcontrol.send(mmk, _cmd);
    _cmd = {'call': 'stop', 'args': []};
    _botcontrol.send('Loopback', _cmd);
    ttalk.oncalltalk(src = _src);
    return;

_tabot_cb_flt_params_qq = {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': _tabot_cmd_params}], 'sender': {'id':CONSTS.BOT_OP_QQ}}}};
_tabot_cb_flt_params_tg = {'mmk': {'telegram.*'}, 'msg':{'message': {'from': {'id':CONSTS.BOT_OP_TG}, 'text': _tabot_cmd_params}}};
def _tabot_cb_fnc_params(mmk, msg):
    _src = tmsgp.msgsrc(mmk, msg);
    _txt = tmsgp.msgtxt(mmk, msg);
    args = _txt.split();
    if len(args) == 2:
        _srcfind = _src;
    elif len(args) == 4:
        _srcfind = tmsgp.src(mmk, args[2], args[3], t = _src['time']);
    elif len(args) == 5:
        _srcfind = tmsgp.src(args[2], args[3], args[4], t = _src['time']);
    else:
        _srcfind = _src;
    _paramstr = ttalk.strparams(_srcfind);
    _cmd = tmsgp.tomsgtxt(_src, _paramstr);
    _botcontrol.send(mmk, _cmd);
    ttalk.oncalltalk(src = _src);
    return;


# 注册
_mod_cbs.append({'fnc': _tabot_cb_fnc_msgecho,          'flt': _tabot_cb_flt_msgecho,               'key': '_tabot_mn_cb_msgecho'               });

_mod_cbs.append({'fnc': _tabot_cb_fnc_statistic_msg,    'flt': _tabot_cb_flt_statistic_msg_qq,      'key': '_tabot_mn_cb_statistic_msg_qq'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_statistic_msg,    'flt': _tabot_cb_flt_statistic_msg_tg,      'key': '_tabot_mn_cb_statistic_msg_tg'      });
_mod_cbs.append({'fnc': _tabot_cb_fnc_statistic_nug,    'flt': _tabot_cb_flt_statistic_nug_qq,      'key': '_tabot_mn_cb_statistic_nug_qq'      });

_mod_cbs.append({'fnc': _tabot_cb_fnc_muted,            'flt': _tabot_cb_flt_muted_qq_self,         'key': '_tabot_mn_cb_muted_qq_self'         });
_mod_cbs.append({'fnc': _tabot_cb_fnc_muted,            'flt': _tabot_cb_flt_muted_qq_all,          'key': '_tabot_mn_cb_muted_qq_all'          });
_mod_cbs.append({'fnc': _tabot_cb_fnc_unmuted,          'flt': _tabot_cb_flt_unmuted_qq_self,       'key': '_tabot_mn_cb_unmuted_qq_self'       });
_mod_cbs.append({'fnc': _tabot_cb_fnc_unmuted,          'flt': _tabot_cb_flt_unmuted_qq_all,        'key': '_tabot_mn_cb_unmuted_qq_all'        });
_mod_cbs.append({'fnc': _tabot_cb_fnc_joingroup,        'flt': _tabot_cb_flt_joingroup_qq,          'key': '_tabot_mn_cb_joingroup_qq'          });
_mod_cbs.append({'fnc': _tabot_cb_fnc_joingroup,        'flt': _tabot_cb_flt_joingroup_tg,          'key': '_tabot_mn_cb_joingroup_tg'          });
_mod_cbs.append({'fnc': _tabot_cb_fnc_leavegroup,       'flt': _tabot_cb_flt_leavegroup_qq_self,    'key': '_tabot_mn_cb_leavegroup_qq_self'    });
_mod_cbs.append({'fnc': _tabot_cb_fnc_leavegroup,       'flt': _tabot_cb_flt_leavegroup_qq_kick,    'key': '_tabot_mn_cb_leavegroup_qq_kick'    });
_mod_cbs.append({'fnc': _tabot_cb_fnc_leavegroup,       'flt': _tabot_cb_flt_leavegroup_tg,         'key': '_tabot_mn_cb_leavegroup_tg'         });
_mod_cbs.append({'fnc': _tabot_cb_fnc_newmember,        'flt': _tabot_cb_flt_newmember_qq,          'key': '_tabot_mn_cb_newmember_qq'          });
_mod_cbs.append({'fnc': _tabot_cb_fnc_newmember,        'flt': _tabot_cb_flt_newmember_tg,          'key': '_tabot_mn_cb_newmember_tg'          });
_mod_cbs.append({'fnc': _tabot_cb_fnc_quitmember,       'flt': _tabot_cb_flt_quitmember_qqkick,     'key': '_tabot_mn_cb_quitmember_qqkick'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_quitmember,       'flt': _tabot_cb_flt_quitmember_qqquit,     'key': '_tabot_mn_cb_quitmember_qqquit'     });
_mod_cbs.append({'fnc': _tabot_cb_fnc_quitmember,       'flt': _tabot_cb_flt_quitmember_tg,         'key': '_tabot_mn_cb_quitmember_tg'         });
_mod_cbs.append({'fnc': _tabot_cb_fnc_migrate,          'flt': _tabot_cb_flt_migrate_tg,            'key': '_tabot_mn_cb_migrate_tg'            });
_mod_cbs.append({'fnc': _tabot_cb_fnc_invited,          'flt': _tabot_cb_flt_invited_qq,            'key': '_tabot_mn_cb_invited_qq'            });
_mod_cbs.append({'fnc': _tabot_cb_fnc_invited,          'flt': _tabot_cb_flt_invited_tg,            'key': '_tabot_mn_cb_invited_tg'            });

_mod_cbs.append({'fnc': _tabot_cb_fnc_help,             'flt': _tabot_cb_flt_help_qq,               'key': '_tabot_mn_cb_help_qq'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_help,             'flt': _tabot_cb_flt_help_tg,               'key': '_tabot_mn_cb_help_tg'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_ping,             'flt': _tabot_cb_flt_ping_qq,               'key': '_tabot_mn_cb_ping_qq'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_ping,             'flt': _tabot_cb_flt_ping_tg,               'key': '_tabot_mn_cb_ping_tg'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_reload,           'flt': _tabot_cb_flt_reload_qq,             'key': '_tabot_mn_cb_reload_qq'             });
_mod_cbs.append({'fnc': _tabot_cb_fnc_reload,           'flt': _tabot_cb_flt_reload_tg,             'key': '_tabot_mn_cb_reload_tg'             });
_mod_cbs.append({'fnc': _tabot_cb_fnc_save,             'flt': _tabot_cb_flt_save_qq,               'key': '_tabot_mn_cb_save_qq'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_save,             'flt': _tabot_cb_flt_save_tg,               'key': '_tabot_mn_cb_save_tg'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_stop,             'flt': _tabot_cb_flt_stop_qq,               'key': '_tabot_mn_cb_stop_qq'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_stop,             'flt': _tabot_cb_flt_stop_tg,               'key': '_tabot_mn_cb_stop_tg'               });
_mod_cbs.append({'fnc': _tabot_cb_fnc_params,           'flt': _tabot_cb_flt_params_qq,             'key': '_tabot_mn_cb_params_qq'             });
_mod_cbs.append({'fnc': _tabot_cb_fnc_params,           'flt': _tabot_cb_flt_params_tg,             'key': '_tabot_mn_cb_params_tg'             });





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
    logger.info('Tabot Manager Stopped');
    return;
