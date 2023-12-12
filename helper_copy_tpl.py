'''
Created on 2023年12月12日

@author: lenovo
'''
from distutils.dir_util import copy_tree
import os
from pathlib import Path
import re
import shutil
import sys


BASE_DIR = Path(__file__).resolve().parent

ptn_secret = re.compile("""^SECRET_KEY\s+=\s+['"]([^'"]+)['"]$""", re.M)

def get_settings():
    fpath = BASE_DIR.parent / BASE_DIR / 'tpls' / 'settings.py'
    with open(fpath, 'r') as fp:
        return fp.read()

def get_secret_key(project_name):
    fpath = BASE_DIR.parent / project_name / project_name/ 'settings.py'
    with open(fpath, 'r') as fp:
        content = fp.read()
        return ptn_secret.search(content).groups()[0]

def do_copy(project_name):
    src_dir = BASE_DIR / 'tpls' / 'base'
    dst_dir = BASE_DIR.parent / project_name / 'base'
    
    if not os.path.lexists(dst_dir):
        copy_tree(str(src_dir), str(dst_dir))
        
    settings = get_settings()
    secret_key = get_secret_key(project_name)
    settings = settings.replace('PROJECT_NAME_TPL', project_name)
    settings = settings.replace('SECRET_KEY_TPL', secret_key)
    # print(settings)
    fpath = BASE_DIR.parent / project_name / project_name / 'settings.py'
    # print(fpath)
    with open(fpath, 'w') as fp:
        fp.write(settings)
    
    dst = str(BASE_DIR.parent / project_name)
    src = BASE_DIR / 'tpls'
     
    shutil.copy(str(src / "mm.bat"), dst)
    shutil.copy(str(src / "push.bat"), dst)
    shutil.copy(str(src / "pull.bat"), dst)
    shutil.copy(str(src / ".gitignore"), dst)
    print('done!')
    
    
if __name__ == '__main__':
    print(sys.argv)    
    do_copy('my_operation')