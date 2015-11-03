from copy import copy, deepcopy

def Combine(Main_Dict, *Dicts, **kwargs):
    '''Easily combine multiple nested dicts to re-use common elements.
    If a key in the Main_Dict already exists, it wont be overwritten by
    the ones being combined into it. Infinite recursion is allowed and
    will be handeled properly.
    usage = Combine(Main_Dict, *Dicts_with_common_elements)'''
    if "Seen" not in kwargs:
        kwargs["Seen"] = list(Main_Dict)
        kwargs["Seen"].extend(Dicts)
    if "Copy" not in kwargs:
        kwargs["Copy"] = "ref"
        
    for Dict in Dicts:
        for key in Dict:
            
            #if the key already exists
            if key in Main_Dict:
                
                #if the entry in both the main dict and the common dict is
                #a dict, then we merge entries from it into the main dict
                if (isinstance(Dict[key], dict) and
                    isinstance(Main_Dict[key], dict) and
                    Dict[key] not in kwargs["Seen"]):
                    
                    kwargs["Seen"].append(Main_Dict[key])
                    kwargs["Seen"].append(Dict[key])
                    Combine(Main_Dict[key], Dict[key], **kwargs)
            else:
                if kwargs["Copy"].lower() == "deep":
                    Main_Dict[key] = deepcopy(Dict[key])
                elif kwargs["Copy"].lower() == "shallow":
                    Main_Dict[key] = copy(Dict[key])
                else:
                    Main_Dict[key] = Dict[key]
        
    return(Main_Dict)
