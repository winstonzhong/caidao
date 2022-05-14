# -*- coding: utf8 -*-
import random
raw ='''
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)
Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36
'''
# Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36
#Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)

agent_list = raw.strip().splitlines()

def pick_one_agent():
    agent = random.choice(agent_list)
    # print('using:', agent)
    return agent

if __name__ == '__main__':
    for x in agent_list:
        if not x or not x.strip(): 
            print(x)
    print(pick_one_agent())