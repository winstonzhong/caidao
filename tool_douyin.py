import re

ptn_url_suffix = re.compile(
    r'mime_type=([a-z_0-9]+)',
    flags=re.IGNORECASE,
)


def 得到视频后缀(url):
    '''
    >>> 得到视频后缀('https://v3-web.douyinvod.com/dc7277b976396a8a34fd5f2fe60fcab6/67dbeeec/video/tos/cn/tos-cn-ve-0015c800/4a64aae2eeaf4cd8a0b24df32a61039e/?a=6383&ch=26&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C3&cv=1&br=648&bt=648&cs=0&ds=3&ft=AJkeU_TERR0s~dC52Dv2Nc0iPMgzbLKJxO1U_4~fCjV9Nv7TGW&mime_type=video_mp4&qs=0&rc=ZTVmM2hmZ2ZnaTRpOzk8ZUBpam51cmQ6ZjM1ODMzNGkzM0BjYjUuLmFiNl4xMl5jNV81YSMxXmxkcjRva21gLS1kLS9zcw%3D%3D&btag=c0000e00030000&cquery=100o_100w_100B_100D_102u&dy_q=1742455694&l=202503201528148FD1EBC239B6CF01CA6C&__vid=7021722422260911390')
    '.mp4'
    '''
    # mime_type=video_mp4
    match = ptn_url_suffix.search(url)
    if match:
        return f".{match.group(1).lower().rsplit('_',maxsplit=1)[1]}"




if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
