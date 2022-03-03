from re import search

def include_lines(text, include_list):
    lines=text.splitlines()
    included=[]
    for line in lines:
        bInclude=False
        for include in include_list:
            if search(include,line):
                bInclude=True
                break
        if bInclude:
            included.append(line)
    new_text = '\n'.join(map(str,included))
    return new_text
    
def exclude_lines(text, exclude_list):
    lines=text.splitlines()
    remaining=[]
    for line in lines:
        bExclude=False
        for exclude in exclude_list:
            if search(exclude,line):
                bExclude=True
        if bExclude:
            pass
        else:
            remaining.append(line)
    new_text = '\n'.join(map(str,remaining))
    return new_text
    
def extract_token(line,separator,token_num):
    tokens = line.split(separator)
    token = tokens[token_num]
    return token

def trim_token(token):
    trimmed_token=token.strip()
    return trimmed_token

if __name__ == '__main__':
    
    text="100% 10/10 [00:00<00:00, 32.54it/s]\n" \
         "Shape of Overall Pandas DataFrame: (23858, 9)\n" \
         "100% 10/10 [00:01<00:00,  5.81it/s]\n" \
         "100% 10/10 [00:00<00:00, 1822.03it/s]\n" \
         "Exported: wd/generated_ev_data/metadata.json\n" \
         "Task status: wd/generated_ev_data/task_ev_data_generate_status.json\n"

    selected_lines = include_lines(text,['generate'])
    selected_line = exclude_lines(selected_lines,['metadata'])
    token = extract_token(selected_line,'/',2)
    clean_token = trim_token(token)
    
    print(clean_token)