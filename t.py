from helper_net import get_with_random_agent

url = 'https://www.xiaohongshu.com/explore/6539175b000000002201f4d4'
# url = 'https://www.xiaohongshu.com/explore/65390c75000000001f0386a0'
url = 'https://www.xiaohongshu.com/explore/6520c2c6000000002301825c'

resp = get_with_random_agent(url)
content = resp.content.decode()

txt = '<meta name="og:title"'

print(txt in content)