from copy import copy, deepcopy

def combine(maindict, *dicts, **kwargs):
    '''combines multiple nested dicts to re-use common elements.
    If a key in the maindict already exists, it wont be overwritten by
    the ones being combined into it. Infinite recursion is allowed and
    is handeled properly.
    
    usage = combine(maindict, *dicts_with_common_elements)

    Returns the maindict
    '''
    seen = kwargs.get('seen')
    if seen is None:
        seen = set((id(maindict),))
        
    for d in dicts:
        seen.add(id(d))
        for i in d:
            #if the key already exists
            if i in maindict:
                #if the entry in both the main dict and
                #the common dict is a dict, then we merge
                #entries from it into the main dict
                if (isinstance(d[i], dict) and
                    isinstance(maindict[i], dict) and
                    id(d[i]) not in seen):
                    
                    seen.add(id(maindict[i]))
                    seen.add(id(d[i]))
                    combine(maindict[i], d[i], seen = seen)
            else:
                maindict[i] = d[i]
                
    return maindict
