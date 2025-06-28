# blender_ipython.py
import bpy
import sys


sys.path.append(r'C:\Users\Winston\AppData\Roaming\Python\Python311\site-packages')

#bpy.ops.wm.addon_enable(module='autorig_pro')

from IPython.terminal.embed import InteractiveShellEmbed

# 启动 IPython 嵌入式 shell
ipshell = InteractiveShellEmbed(banner1="Blender + IPython 交互环境")
ipshell()