
import CONSTS;
import exs.tabot_msgproc as tmsgp;

import re;
import time;
import random;
import logging;

VERSION = 'v20210826';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;35m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot Fun Cmd Loaded');

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
# Tabot Fun Cmd：Tabot组件，用于处理各类朴素整活消息
""";



# tabot的全局变量
_tabot_chat_last_talk_time = dict();
_tabot_chat_talk_static = dict();

def _tabot_chat_talkable(mmk, cid):
    _key = mmk + '.' + cid;
    if _key not in _tabot_chat_last_talk_time or time.time() - _tabot_chat_last_talk_time[_key] > 10:
        if _key in _tabot_chat_talk_static and len(_tabot_chat_talk_static[_key]) >= 10 and time.time() - _tabot_chat_talk_static[_key][-10] < 60*60*24:
            return True;
    return False;

_tabot_funcmd_unmuted_talks = [
    "我对你们因为我说话怪而选择使用权限对我在群的发言进行封闭的行为抱有消极的观点",
    "我不认为你们选择通过使用权限的方式禁止我的文本表达是一种积极的行为",
    "草，终于可以说话了",
    "能不能不要封我",
];
_tabot_funcmd_joingroup_talks = [
    "这群挺别致啊",
    "这啥群谁拉我的",
    "在此向群友们问好，我对进入本群抱着相对积极的态度",
]
_tabot_funcmd_newmember_talks = [
    "出于对新群友的欢迎，我很愿意在此处表示对新群友的欢迎",
    "在此对群友的总数增加表示一次庆祝",
    "我认为群总人数的上升是群主和管理员们对群做出的突出贡献的具体表现形式",
    "根据我的分析，我在本群的智力水平的排名可能已发生向后下降一名的情况",
    "恭喜群成员的拓展发生了",
]
_tabot_funcmd_kickmember_talks = [
    "某种程度上这是一件不能进行定量判定的人类社交系统事件，很不幸但又不得不发生了"
]
_tabot_funcmd_quitmember_talks = [
    "某种程度上这是一件不能进行定量判定的人类社交系统事件，很不幸但又不得不发生了"
]
_tabot_funcmd_henshin_talks = [
    "库库库七七",
    "dling bin 叮叮匡",
    "bling bling biu biu biu, chua chua chua xiu xiu",
    "我不认为我真的具有变身的能力",
]
_tabot_funcmd_reboot_talks = [
    "我不认为你应当抱有可以让我reboot的想法",
    "你是否是存在对自己权限的过度自信认知",
    "你可以尝试在本地终端输入 shutdown -p 以实现",
    "sudo rm -rf /*",
]
_tabot_funcmd_jgb_talks = [
    "鸡公煲",
    "想吃鸡公煲了",
    "为什么不吃花雕醉鸡呢",
]
_tabot_funcmd_hdzj_talks = [
    "花雕醉鸡",
    "花雕醉鸡yyds，好吃到跺jiojio，我暴风吸入，绝绝子",
    "想吃花雕醉鸡了",
    "为什么不吃鸡公煲呢",
]



_tabot_cmd_henshin = 't -.*henshin.*';
_tabot_cmd_reboot = 't -.*reboot.*';
_tabot_cmd_tarcadia = 't -.*tarcadia.*';
_tabot_cmd_cat = 't -.*cat.*';
_tabot_cmd_dog = 't -.*dog.*';
_tabot_cmd_amdyes = '.*[Aa][Mm][Dd] [Yy][Ee][Ss].*';
_tabot_cmd_jgb = '.*(鸡公煲|[Jj][Gg][Bb])+.*';
_tabot_cmd_hdzj = '.*花.*雕.*醉.*鸡.*';

# 回调接口

# 群消息热度统计
_tabot_funcmd_cb_flt_chatstatic_qqgroup = {
    'mmk':{'mirai.*'},
    'msg':{'data':{'type':'GroupMessage'}}
};
_tabot_funcmd_cb_flt_chatstatic_tggroup = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': '.*'}}
};
def _tabot_funcmd_cb_fnc_chatstatic(mmk, msg):
    _src, txt = tmsgp.fromtxtmsg(mmk, msg);
    _key = mmk + '.' + _src['cid'];
    if _key in _tabot_chat_talk_static:
        _tabot_chat_talk_static[_key] = _tabot_chat_talk_static[_key][-min(10, len(_tabot_chat_talk_static[_key])):] + [_src['time']];
    else:
        _tabot_chat_talk_static[_key] = [_src['time']];

# 解除禁言
_tabot_funcmd_cb_flt_unmuted_qq_self = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotUnmuteEvent'}}
};
def _tabot_funcmd_cb_fnc_unmuted(mmk, msg):
    _gid = msg['data']['operator']['group']['id'];
    _cid = 'g' + str(_gid);
    if random.random() <= 0.8 and _tabot_chat_talkable(mmk, _cid):
        _txt = random.choice(_tabot_funcmd_unmuted_talks);
        _msg = tmsgp.totxtmsg(mmk, _cid, _txt);
        _botcontrol.send(mmk, _msg);
        _tabot_chat_last_talk_time[mmk + '.' + _cid] = time.time();
    return;

# 加群
_tabot_funcmd_cb_flt_joingroup_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'BotJoinGroupEvent'}}
};
def _tabot_funcmd_cb_fnc_joingroup(mmk, msg):
    _gid = msg['data']['group']['id'];
    _cid = 'g' + str(_gid);
    if random.random() <= 0.8 and _tabot_chat_talkable(mmk, _cid):
        _txt = random.choice(_tabot_funcmd_joingroup_talks);
        _msg = tmsgp.totxtmsg(mmk, _cid, _txt);
        _botcontrol.send(mmk, _msg);
        _tabot_chat_last_talk_time[mmk + '.' + _cid] = time.time();
    return;

# 群加人
_tabot_funcmd_cb_flt_newmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'MemberJoinEvent'}}
};
def _tabot_funcmd_cb_fnc_newmember(mmk, msg):
    _gid = msg['data']['member']['group']['id'];
    _cid = 'g' + str(_gid);
    if random.random() <= 0.8 and _tabot_chat_talkable(mmk, _cid):
        _txt = random.choice(_tabot_funcmd_newmember_talks);
        _msg = tmsgp.totxtmsg(mmk, _cid, _txt);
        _botcontrol.send(mmk, _msg);
        _tabot_chat_last_talk_time[mmk + '.' + _cid] = time.time();
    return;

# 群踢人
_tabot_funcmd_cb_flt_kickmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'MemberLeaveEventKick'}}
};
def _tabot_funcmd_cb_fnc_kickmember(mmk, msg):
    _gid = msg['data']['member']['group']['id'];
    _cid = 'g' + str(_gid);
    if random.random() <= 0.5 and _tabot_chat_talkable(mmk, _cid):
        _txt = random.choice(_tabot_funcmd_kickmember_talks);
        _msg = tmsgp.totxtmsg(mmk, _cid, _txt);
        _botcontrol.send(mmk, _msg);
        _tabot_chat_last_talk_time[mmk + '.' + _cid] = time.time();
    return;

# 群退人
_tabot_funcmd_cb_flt_quitmember_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'type':'MemberLeaveEventQuit'}}
};
def _tabot_funcmd_cb_fnc_quitmember(mmk, msg):
    _gid = msg['data']['member']['group']['id'];
    _cid = 'g' + str(_gid);
    if random.random() <= 0.0 and _tabot_chat_talkable(mmk, _cid):
        _txt = random.choice(_tabot_funcmd_quitmember_talks);
        _msg = tmsgp.totxtmsg(mmk, _cid, _txt);
        _botcontrol.send(mmk, _msg);
        _tabot_chat_last_talk_time[mmk + '.' + _cid] = time.time();
    return;

# Bot指令
_tabot_funcmd_cb_flt_henshin_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_henshin}]}}
};
_tabot_funcmd_cb_flt_henshin_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': _tabot_cmd_henshin}}
};
def _tabot_funcmd_cb_fnc_henshin(mmk, msg):
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    _txt = random.choice(_tabot_funcmd_henshin_talks);
    _msg = tmsgp.totxtmsg(mmk, _src['cid'], _txt);
    _botcontrol.send(mmk, _msg);
    return;

_tabot_funcmd_cb_flt_reboot_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_reboot}]}}
};
_tabot_funcmd_cb_flt_reboot_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': _tabot_cmd_reboot}}
};
def _tabot_funcmd_cb_fnc_reboot(mmk, msg):
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    _txt = random.choice(_tabot_funcmd_reboot_talks);
    _msg = tmsgp.totxtmsg(mmk, _src['cid'], _txt);
    _botcontrol.send(mmk, _msg);
    return;

_tabot_funcmd_cb_flt_jgb_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_jgb}]}}
};
_tabot_funcmd_cb_flt_jgb_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': _tabot_cmd_jgb}}
};
def _tabot_funcmd_cb_fnc_jgb(mmk, msg):
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    _txt = random.choice(_tabot_funcmd_jgb_talks);
    _msg = tmsgp.totxtmsg(mmk, _src['cid'], _txt);
    _botcontrol.send(mmk, _msg);
    return;

_tabot_funcmd_cb_flt_hdzj_qq = {
    'mmk':{'mirai.*'},
    'msg':{'data': {'messageChain':[{'type':'Plain','text':_tabot_cmd_hdzj}]}}
};
_tabot_funcmd_cb_flt_hdzj_tg = {
    'mmk':{'telegram.*'},
    'msg':{'message': {'text': _tabot_cmd_hdzj}}
};
def _tabot_funcmd_cb_fnc_hdzj(mmk, msg):
    _src, _txt = tmsgp.fromtxtmsg(mmk, msg);
    _txt = random.choice(_tabot_funcmd_hdzj_talks);
    _msg = tmsgp.totxtmsg(mmk, _src['cid'], _txt);
    _botcontrol.send(mmk, _msg);
    return;



# 注册
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_chatstatic, 'flt': _tabot_funcmd_cb_flt_chatstatic_qqgroup, 'key': '_tabot_funcmd_cb_chatstatic_qqgroup'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_chatstatic, 'flt': _tabot_funcmd_cb_flt_chatstatic_tggroup, 'key': '_tabot_funcmd_cb_chatstatic_tggroup'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_unmuted, 'flt': _tabot_funcmd_cb_flt_unmuted_qq_self, 'key': '_tabot_funcmd_cb_unmuted_qq_self'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_joingroup, 'flt': _tabot_funcmd_cb_flt_joingroup_qq, 'key': '_tabot_funcmd_cb_joingroup_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_newmember, 'flt': _tabot_funcmd_cb_flt_newmember_qq, 'key': '_tabot_funcmd_cb_newmember_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_kickmember, 'flt': _tabot_funcmd_cb_flt_kickmember_qq, 'key': '_tabot_funcmd_cb_kickmember_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_quitmember, 'flt': _tabot_funcmd_cb_flt_quitmember_qq, 'key': '_tabot_funcmd_cb_quitmember_qq'});

_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_henshin, 'flt': _tabot_funcmd_cb_flt_henshin_qq, 'key': '_tabot_funcmd_cb_henshin_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_henshin, 'flt': _tabot_funcmd_cb_flt_henshin_tg, 'key': '_tabot_funcmd_cb_henshin_tg'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_reboot, 'flt': _tabot_funcmd_cb_flt_reboot_qq, 'key': '_tabot_funcmd_cb_reboot_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_reboot, 'flt': _tabot_funcmd_cb_flt_reboot_tg, 'key': '_tabot_funcmd_cb_reboot_tg'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_jgb, 'flt': _tabot_funcmd_cb_flt_jgb_qq, 'key': '_tabot_funcmd_cb_jgb_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_jgb, 'flt': _tabot_funcmd_cb_flt_jgb_tg, 'key': '_tabot_funcmd_cb_jgb_tg'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_hdzj, 'flt': _tabot_funcmd_cb_flt_hdzj_qq, 'key': '_tabot_funcmd_cb_hdzj_qq'});
_mod_cbs.append({'fnc': _tabot_funcmd_cb_fnc_hdzj, 'flt': _tabot_funcmd_cb_flt_hdzj_tg, 'key': '_tabot_funcmd_cb_hdzj_tg'});



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Fun Cmd Stopped');
    return;

