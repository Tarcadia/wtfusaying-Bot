
import CONSTS;
import exs.tabot_msgproc as tmsgp;
import exs.tabot_totalk as ttalk;

import re;
import time;
import random;
import functools;
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

_tabot_talks_henshin = [
    "库库库七七",
    "dling bin 叮叮匡",
    "bling bling biu biu biu, chua chua chua xiu xiu",
    "我不认为我真的具有变身的能力",
];
_tabot_talks_reboot = [
    "我不认为你应当抱有可以让我reboot的想法",
    "你是否是存在对自己权限的过度自信认知",
    "你可以尝试在本地终端输入 shutdown -p 以实现",
    "sudo rm -rf /*",
];
_tabot_talks_tarcadia = [
    "塔卡",
    "tarcadia",
    "Tarc不在",
];
_tabot_talks_cat = [
    "喵",
    "喵呜",
    "乌鲁乌鲁",
    "汪",
    "既见猫猫何不参拜",
    "将非物质化的电子对象视若动物的行为是不受到鼓励的"
];
_tabot_talks_dog = [
    "汪",
    "汪汪汪",
    "汪汪",
    "嗷呜",
    "你才是狗呢",
    "将非物质化的电子对象视若动物的行为是不受到鼓励的"
];
_tabot_talks_jgb = [
    "饿了",
    "鸡公煲好吃",
    "想吃鸡公煲了",
    "为什么不吃花雕醉鸡呢",
    "微微辣，加脆皮肠，加甜不辣",
    "精彩生活",
    "商业街还是南门",
    "今天有约嘛",
    "在不具有对美食获取能力的实体面前讨论人类超越饱腹度意义的进食体验是不人道的",
];
_tabot_talks_hdzj = [
    "饿了",
    "花雕醉鸡yyds，好吃到跺jiojio，我暴风吸入，绝绝子",
    "想吃花雕醉鸡了",
    "为什么不吃鸡公煲呢",
    "五香我昨天预定了",
    "你排不上",
    "帮我多要一份油条",
    "牙索在不在",
    "辣辣姐姐",
    "牙索不在，辣辣也不在",
    "输入t -dog召唤牙索",
    "今天没有花雕鸡，因为辣辣带牙索和我约会去了",
    "我不认为你们应当在非实体的对象面前讨论实体化的进食内容",
];



_tabot_cmd_henshin = 't -henshin';
_tabot_cmd_reboot = 't -reboot';
_tabot_cmd_tarcadia = 't -tarcadia';
_tabot_cmd_cat = 't -cat';
_tabot_cmd_dog = 't -dog';

_tabot_kw_amdyes = '.*[Aa][Mm][Dd] [Yy][Ee][Ss].*';
_tabot_kw_jgb = '.*((鸡.*公.*煲)|([Jj][Gg][Bb]))+.*';
_tabot_kw_hdzj = '.*花.*雕.*醉{0,1}.*鸡.*';





# 回调接口



# 模板条件
def cb_flt_txtmatch_qq(txt):
    return {'mmk': {'mirai.*'}, 'msg': {'data': {'messageChain': [{'type': 'Plain', 'text': txt}]}}};
def cb_flt_txtmatch_tg(txt):
    return {'mmk': {'telegram.*'}, 'msg': {'message': {'text': txt}}};
    
# 直接回复模板函数
def alwaystalk(p, talks):
    def func(mmk, msg):
        _src = tmsgp.msgsrc(mmk, msg);
        _txt = random.choice(talks);
        if random.random() <= p:
            _msg = tmsgp.tomsgtxt(_src, _txt);
            _botcontrol.send(mmk, _msg);
            ttalk.oncalltalk(_src);
        return;
    return func;

# 条件回复模板函数
def conditiontalk(p, talks):
    def func(mmk, msg):
        _src = tmsgp.msgsrc(mmk, msg);
        _txt = random.choice(talks);
        if ttalk.cantalk(_src, p = p):
            _msg = tmsgp.tomsgtxt(_src, _txt);
            _botcontrol.send(mmk, _msg);
            ttalk.ontalk(_src);
        return;
    return func;

# 注册
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_henshin), 'flt': cb_flt_txtmatch_qq(_tabot_cmd_henshin), 'key': '_tabot_funcmd_cb_henshin_qq'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_henshin), 'flt': cb_flt_txtmatch_tg(_tabot_cmd_henshin), 'key': '_tabot_funcmd_cb_henshin_tg'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_reboot), 'flt': cb_flt_txtmatch_qq(_tabot_cmd_reboot), 'key': '_tabot_funcmd_cb_reboot_qq'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_reboot), 'flt': cb_flt_txtmatch_tg(_tabot_cmd_reboot), 'key': '_tabot_funcmd_cb_reboot_tg'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_tarcadia), 'flt': cb_flt_txtmatch_qq(_tabot_cmd_tarcadia), 'key': '_tabot_funcmd_cb_tarcadia_qq'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_tarcadia), 'flt': cb_flt_txtmatch_tg(_tabot_cmd_tarcadia), 'key': '_tabot_funcmd_cb_tarcadia_tg'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_cat), 'flt': cb_flt_txtmatch_qq(_tabot_cmd_cat), 'key': '_tabot_funcmd_cb_cat_qq'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_cat), 'flt': cb_flt_txtmatch_tg(_tabot_cmd_cat), 'key': '_tabot_funcmd_cb_cat_tg'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_dog), 'flt': cb_flt_txtmatch_qq(_tabot_cmd_dog), 'key': '_tabot_funcmd_cb_dog_qq'});
_mod_cbs.append({'fnc': alwaystalk(1, _tabot_talks_dog), 'flt': cb_flt_txtmatch_tg(_tabot_cmd_dog), 'key': '_tabot_funcmd_cb_dog_tg'});
_mod_cbs.append({'fnc': conditiontalk(0.8, _tabot_talks_jgb), 'flt': cb_flt_txtmatch_qq(_tabot_kw_jgb), 'key': '_tabot_funcmd_cb_jgb_qq'});
_mod_cbs.append({'fnc': conditiontalk(0.8, _tabot_talks_jgb), 'flt': cb_flt_txtmatch_tg(_tabot_kw_jgb), 'key': '_tabot_funcmd_cb_jgb_tg'});
_mod_cbs.append({'fnc': conditiontalk(0.8, _tabot_talks_hdzj), 'flt': cb_flt_txtmatch_qq(_tabot_kw_hdzj), 'key': '_tabot_funcmd_cb_hdzj_qq'});
_mod_cbs.append({'fnc': conditiontalk(0.8, _tabot_talks_hdzj), 'flt': cb_flt_txtmatch_tg(_tabot_kw_hdzj), 'key': '_tabot_funcmd_cb_hdzj_tg'});



# 主流程

def start():
    return [];

def save():
    return;

def stop():
    logger.info('Tabot Fun Cmd Stopped');
    return;

