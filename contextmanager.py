

# wordlist = topickeywords(contextsensor, tid, count)
# 计算contextsensor的tid所指的topic下前count个关键词
def topickeywords(cs : dict, tid : int, count : int = 3):
    _keys = [_k for _k in cs['topics'][tid]['vec']];
    _vals = [cs['topics'][tid]['vec'][_k] for _k in cs['topics'][tid]['vec']];
    _keys = [_keys[sorted(_vals).index(_)] for _ in _vals];
    return _keys[0 : count - 1];