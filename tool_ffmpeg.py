'''
Created on 2023年12月27日

@author: lenovo
'''
import re
import subprocess

from tool_env import is_number


ptn_line = re.compile('(\d{2}):(\d{2}).(\d{3})')

def to_seconds(line):
    '''
    >>> to_seconds('02:28.400') == 148.4
    True
    >>> to_seconds(148.11) == 148.11
    True
    '''
    if not is_number(line):
        l = ptn_line.match(line).groups()
        line = int(l[0]) * 60 + int(l[1]) + int(l[2]) / 1000
    return line

def to_timestr(seconds):
    '''
    >>> to_timestr(148.4) == '02:28.400'
    True
    '''
    return '%02d:%02d.%s' % (seconds //  60, int(seconds) % 60, ('%.03f' % seconds)[-3:])

    

def trim_audio(fpath_input, fpath_output, start=0, end=0):
    start_seconds = to_seconds(start)
    end_seconds = to_seconds(end)
    duration = end_seconds - start_seconds
    subprocess.Popen(
        f'''ffmpeg  -i "{fpath_input}" -ss {start_seconds} -t {duration} "{fpath_output}" -y''', 
        shell=True)



if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))