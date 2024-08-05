def parse_docstring(strategy_class):
    description = ""
    params = {}
    parsing_params = False
    docstring = strategy_class.__doc__
    if(docstring is None): return "NA",{}
    for l in docstring.split('\n'):
        l = l.strip()
        if(len(l) == 0): continue
        if(not parsing_params):
            if(l.startswith('description:')):
                description = l.replace('description:','').strip()
            elif(l.startswith('params')):
                parsing_params = True
        else:
            field = l.split(':')[0].strip()
            values = ':'.join(l.split(':')[1:]).strip()
            if(values[0]=='[' and values[-1]==']'):
                values = [_.strip() for _ in values[1:-1].split(',')]
            #print(field, values)
            params[field] = values
    return description, params