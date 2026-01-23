import os

import psutil
import shutil


def get_disk_usage():
    """
    获取linx/windows系统磁盘使用情况

    Returns:
        dict: 包含各挂载点磁盘使用信息的字典，结构如下：
        {
            "/": {
                "total": "200.0 GB",    # 总容量
                "used": "80.5 GB",      # 已用容量
                "free": "110.5 GB",     # 可用容量
                "percent": "40.2%"      # 使用率
            },
            ...
        }
    """
    # 定义需要过滤掉的伪文件系统类型
    exclude_fstypes = {'tmpfs', 'sysfs', 'devtmpfs', 'proc', 'udev', 'overlay', 'squashfs'}
    disk_usage = {}

    try:
        # 获取所有磁盘分区信息
        partitions = psutil.disk_partitions(all=False)

        for partition in partitions:
            # 过滤掉不需要的文件系统类型
            if partition.fstype in exclude_fstypes:
                continue

            # 获取磁盘使用情况
            usage = psutil.disk_usage(partition.mountpoint)

            # 将字节转换为易读的格式（GB/MB）
            def format_size(bytes_size):
                """辅助函数：将字节转换为易读的存储单位"""
                size = shutil.disk_usage("/").total  # 仅为示例，实际用传入的bytes_size
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_size < 1024:
                        return f"{bytes_size:.1f} {unit}"
                    bytes_size /= 1024
                return f"{bytes_size:.1f} PB"

            # 构造该分区的使用信息
            disk_usage[partition.mountpoint] = {
                "total": format_size(usage.total),
                "used": format_size(usage.used),
                "free": format_size(usage.free),
                "percent": f"{usage.percent:.1f}%"
            }

    except Exception as e:
        print(f"获取磁盘使用信息失败: {str(e)}")
        return {}

    return disk_usage


def get_termux_disk_usage():
    """
    获取 Termux 环境下的磁盘使用情况
    适配安卓 Termux 的权限和文件系统特点
    """
    disk_usage = {}

    # 定义 Termux 中常用的存储路径
    # 根据你的实际情况调整路径
    storage_paths = [
        os.path.expanduser("~"),  # Termux 主目录
        "/sdcard",  # 手机内部存储
        "/sdcard/Android/data/com.termux/files/home"  # Termux 外部存储
    ]

    try:
        # 辅助函数：字节转换为易读格式
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_size < 1024:
                    return f"{bytes_size:.1f} {unit}"
                bytes_size /= 1024
            return f"{bytes_size:.1f} PB"

        # 遍历每个存储路径，获取可用信息
        for path in storage_paths:
            # 检查路径是否存在且可访问
            if os.path.exists(path) and os.access(path, os.R_OK):
                try:
                    # 获取磁盘使用信息
                    usage = shutil.disk_usage(path)
                    used_percent = (usage.used / usage.total) * 100

                    # 添加到结果字典
                    disk_usage[path] = {
                        "total": format_size(usage.total),
                        "used": format_size(usage.used),
                        "free": format_size(usage.free),
                        "percent": f"{used_percent:.1f}%"
                    }
                except Exception as e:
                    # 跳过无法访问的路径（如SD卡未挂载）
                    print(f"无法获取 {path} 的信息: {str(e)}")
                    continue

    except Exception as e:
        print(f"获取磁盘使用信息失败: {str(e)}")
        return {}

    return disk_usage


def get_termux_memory_usage():
    """
    获取 Termux 环境下的内存使用情况
    优先使用psutil，失败则解析/proc/meminfo（Termux兼容）
    """
    memory_info = {}

    # 辅助函数：字节转换
    def format_size(bytes_size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} PB"

    # 方案1：使用psutil（需要安装）
    try:
        # 获取内存信息
        mem = psutil.virtual_memory()
        memory_info = {
            "total": format_size(mem.total),
            "used": format_size(mem.used),
            "available": format_size(mem.available),
            "percent": f"{mem.percent:.1f}%",
            "free": format_size(mem.free)
        }
        return memory_info
    except ImportError:
        print("未安装psutil，尝试使用/proc/meminfo解析...")
    except Exception as e:
        print(f"psutil获取内存失败: {str(e)}")

    # 方案2：解析/proc/meminfo（Termux原生支持）
    try:
        meminfo_path = "/proc/meminfo"
        if not os.path.exists(meminfo_path):
            raise Exception("找不到/proc/meminfo文件")

        mem_data = {}
        with open(meminfo_path, 'r') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    # 提取数值（单位：KB）
                    num_str = value.strip().split()[0]
                    try:
                        mem_data[key] = int(num_str) * 1024  # 转换为字节
                    except:
                        continue

        # 计算核心内存指标
        total = mem_data.get('MemTotal', 0)
        free = mem_data.get('MemFree', 0)
        buffers = mem_data.get('Buffers', 0)
        cached = mem_data.get('Cached', 0)
        available = mem_data.get('MemAvailable', free + buffers + cached)
        used = total - available

        if total > 0:
            percent = (used / total) * 100
            memory_info = {
                "total": format_size(total),
                "used": format_size(used),
                "available": format_size(available),
                "percent": f"{percent:.1f}%",
                "free": format_size(free)
            }

    except Exception as e:
        print(f"解析/proc/meminfo失败: {str(e)}")

    return memory_info

def get_termux_sys_info():
    return {'disk_info': get_termux_disk_usage(),
            'mem_info': get_termux_memory_usage()
            }




# 测试函数
if __name__ == "__main__":
    x = get_termux_sys_info()
    print(x)