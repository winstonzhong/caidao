'''
Created on 2023年12月27日

@author: lenovo
'''
import re
import subprocess

from tool_env import is_number


ptn_line = re.compile('(\d{2}):(\d{2}).(\d{2,3})')

def to_seconds(line):
    '''
    >>> to_seconds('02:28.400') == 148.4
    True
    >>> to_seconds(148.11) == 148.11
    True
    >>> to_seconds('00:00.10') == 0.1
    True
    >>> to_seconds('00:00:03,700') == 3.7
    True
    >>> to_seconds('01:00:03,700') == 3603.7
    True
    '''
    if not is_number(line):
        l = line.split(':')
        l.reverse()
        total = 0
        for i, x in enumerate(l):
            if i == 0:
                s, ms = re.split('[,\.]+',x)
                total += int(s) + float(f'0.{ms}')
            else:
                total += int(x) * (60 ** i)
        return total
    return line

def to_timestr(seconds):
    '''
    >>> to_timestr(148.4) == '02:28.400'
    True
    '''
    return '%02d:%02d.%s' % (seconds //  60, int(seconds) % 60, ('%.03f' % seconds)[-3:])


def to_timestr_with_hour(seconds):
    '''
    >>> to_timestr_with_hour(148.4) == '00:02:28,400'
    True
    >>> to_timestr_with_hour(148.004) == '00:02:28,004'
    True
    >>> to_timestr_with_hour(148.04) == '00:02:28,040'
    True
    '''
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s =  seconds % 60
    ms = seconds - int(seconds)
    return '%02d:%02d:%02d,%s' % (h, m, s, f'{ms:.3f}'[2:])
    

def add_seconds_to_timestr(txt, seconds):
    return to_timestr(to_seconds(txt) +  seconds)

    

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