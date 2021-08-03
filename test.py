import sentencegenerator as sgen;
import log;


MODULE_NAME = 'Sentence Generator';
MODULE_VERSION = 'v20210803';

log.LoadModule(MODULE_NAME, MODULE_VERSION);


print(sgen.translate({"patten":"eDef", "sub":"手机", "obj":"复杂移动掌上终端设备"}));