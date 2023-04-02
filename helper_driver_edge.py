'''
Created on 2023年3月7日

@author: lenovo
'''
import os
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent.parent

sys.path.append(str(BASE_DIR / 'caidao'))



from tool_env import OS_WIN



if OS_WIN:
    from msedge.selenium_tools import Edge, EdgeOptions
    DRIVER_PATH = r'E:\迅雷下载\edgedriver_win64\msedgedriver.exe'
    user_data_dir = r'd:\edge'
else:
    user_data_dir = r"user-data-dir=/home/winston/.config/edge/"

if not os.path.lexists(user_data_dir):
    os.makedirs(user_data_dir)    


def get_driver(headless=False):
    edge_options = EdgeOptions()
    
    # print(edge_options.page_load_strategy)

    if headless:
        edge_options.add_argument('--headless')

    edge_options.use_chromium = True    
    
    edge_options.add_argument("user-data-dir=d:\\edge"); 
    
    # edge_options.add_argument("profile-directory=Profile 1");
    
    driver = Edge(options = edge_options, executable_path = DRIVER_PATH)
    
    return driver

