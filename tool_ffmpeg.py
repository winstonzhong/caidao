'''
Created on 2023年12月27日

@author: lenovo
'''
import os
import re
import subprocess
from tool_env import is_number
from tool_file import change_suffix


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
    >>> to_seconds('05:03') == 303
    True
    >>> to_seconds('8.8s') == 8.8
    True
    '''
    if not is_number(line):
        l = line.split(':')
        l.reverse()
        total = 0
        for i, x in enumerate(l):
            if i == 0:
                tmp = re.split('[,\.]+',x)
                if len(tmp) == 2:
                    s, ms = re.split('[,\.]+',x)
                    ms = ms.lower()
                    if ms.endswith('s'):
                        ms = ms[:-1]
                    total += int(s) + float(f'0.{ms}')
                elif len(tmp) == 1:
                    total += int(tmp[0])
                else:
                    raise ValueError
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
    process = subprocess.Popen(
        f'''ffmpeg  -i "{fpath_input}" -ss {start_seconds} -t {duration} "{fpath_output}" -y''', 
        shell=True)
    process.wait()
    
def trim_video(fpath_input, fpath_output, start=0, end=0):
    return trim_audio(fpath_input, fpath_output, start, end)

def concat_mp4s(video_txt, fpath_dst):
    process = subprocess.Popen(
        f'''ffmpeg -f concat -i "{video_txt}" -c copy "{fpath_dst}" -y''', 
        shell=True)
    process.wait()

def split_mp4(fpath_mp4, dir_dst, fps=30):
    if not os.path.lexists(dir_dst):
        os.makedirs(dir_dst)
    process = subprocess.Popen(
        f'''ffmpeg -i {fpath_mp4} -vf fps={fps} {dir_dst}/%d.png''', 
        shell=True)
    process.wait()

# ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -strict experimental output.mp4
# ffmpeg -i input_vid.mp4 -itsoffset 00:00:05.0 -i input_audio.wav -vcodec copy -acodec copy output.mp4
# ffmpeg -i input_vid.mp4 -itsoffset 00:00:05.0 -i input_audio.wav -vcodec libx264 -acodec libmp3lame output.mp4
# ffmpeg.exe -i .\test.wav  -i video.mp4 -ss 0:0 -t 1.60 o4.mp4 -y
def merge_mp4_wav(fpath_mp4, fpath_wav, fpath_dst, seconds):
    process = subprocess.Popen(
        f'''ffmpeg -i  {fpath_wav}  -i  {fpath_mp4}  -ss 0:0 -t {seconds:.3f} {fpath_dst} -y''',
        shell=True)
    process.wait()


# ffmpeg.exe -i .\p1_hurt.mp4 -vn -ar 44100 -ac 2 -ab 192k -f mp3 p1_hurt.mp3
def extract_mp3(fpath_mp4, fpath_mp3=None):
    fpath_mp3 = change_suffix(fpath_mp4, 'mp3') if fpath_mp3 is None else fpath_mp3
    process = subprocess.Popen(
        f'''ffmpeg -i  {fpath_mp4}  -vn -ar 44100 -ac 2 -ab 192k -f mp3 {fpath_mp3} -y''',
        shell=True)
    process.wait()

# ffmpeg -i video.mkv -acodec pcm_s16le -ac 2 audio.wav
def extract_wav(fpath_mp4, fpath_wav=None):
    fpath_wav = change_suffix(fpath_mp4, 'wav') if fpath_wav is None else fpath_wav
    process = subprocess.Popen(
        f'''ffmpeg -i  {fpath_mp4}  -vn -acodec pcm_s16le -ac 2 {fpath_wav} -y''',
        shell=True)
    process.wait()

def opus2wav(fpath, fpath_wav=None):
    fpath_wav = change_suffix(fpath, 'wav') if fpath_wav is None else fpath_wav

    process = subprocess.Popen(
        f'''ffmpeg  -i  {fpath}  -ac 1  -acodec pcm_s16le   {fpath_wav} -y''',
        shell=True)
    process.wait()


# def amr2mp3(input_path, output_path):
#     import ffmpy
#     ff = ffmpy.FFmpeg(inputs={input_path: None}, outputs={output_path: None})
#     ff.run()

    # ffmpeg -i input.amr -ab 192k output.mp3
def amr2mp3(fpath, fpath_output=None):
    fpath_output = change_suffix(fpath, 'mp3') if fpath_output is None else fpath_output
    process = subprocess.Popen(
        f'''ffmpeg -i {fpath} -ab 192k {fpath_output} -y''',
        shell=True)
    process.wait()


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))