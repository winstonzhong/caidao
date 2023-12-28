'''
Created on 2023年12月27日

@author: lenovo
'''
import re
import subprocess


ptn_line = re.compile('(\d{2}):(\d{2}).(\d{3})')

def to_seconds(line):
    '''
    >>> to_seconds('02:28.400') == 148.4
    True
    '''
    l = ptn_line.match(line).groups()
    return int(l[0]) * 60 + int(l[1]) + int(l[2]) / 1000



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