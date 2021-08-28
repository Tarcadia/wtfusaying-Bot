
import CONSTS;

import re;
import logging;

VERSION = 'v20210823';
CONFIG = './config/tabot_totalk.json';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(fmt='\033[0m%(asctime)s \033[1;34m[%(levelname)s]\033[0;36m[%(name)s]\033[0m >> %(message)s', datefmt='%H:%M');
logger_ch.setFormatter(logger_formatter);
if not logger.hasHandlers():
    logger.addHandler(logger_ch);
logger.info('Tabot To Talk - ex Loaded');

# 数据记录：
# chatkey = '<mmk>.<cid>';                      // 用于跨接口的标识语境
# cid = '<g|p|c><xxxxxx>';                      // 用于同一个接口内跨类型的标识语境

# contexts = dict[chatkey]{contextsensor};      // 记录聊天上下文的contextsensor模块
# wordlinks = wordlinksensor;                   // 学习的结果，将会文件存储
# 

# 接口函数

#保存
def save():
    return;
