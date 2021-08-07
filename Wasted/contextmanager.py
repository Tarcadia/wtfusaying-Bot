

# wordlist = topickeywords(contextsensor, tid, count)
# 计算contextsensor的tid所指的topic下前count个关键词
def topickeywords(cs : dict, tid : int, count : int = 3):
    _vals = sorted(cs['topics'][tid]['vec'].items(), key = lambda x : x[1], reverse = True);
    _ans = _vals[0 : min(count, len(_vals))];
    return _ans;