
import json;
import logging;

VERSION = 'v20210820';

logger = logging.getLogger(__name__);
logger.setLevel(logging.DEBUG);
logger_ch = logging.StreamHandler();
logger_ch.setLevel(logging.DEBUG);
logger_formatter = logging.Formatter(format='[%(asctime)s][%(name)s][%(levelname)s] >> %(message)s', datefmt='%Y%m%d-%H%M%S');
logger_ch.setFormatter(logger_formatter);
logger.addHandler(logger_ch);
logger.info('Main Loaded');

def main():
    # 初始化API接口类（MessageManager）
    # 初始化BotControl
    # 注册各个messageprocess类的接口到BotControl
    # 启动Polling
    return;

if __name__ == '__main__':
    main()