import os
import shutil
import re
import argparse

def copy_latest_py_file(download_dir, workspace_dir):
    # 确保目标目录存在
    os.makedirs(workspace_dir, exist_ok=True)

    # 获取指定目录下所有 .py 文件并按修改时间排序（最新的排在前面）
    py_files = [
        (f, os.path.getmtime(os.path.join(download_dir, f))) 
        for f in os.listdir(download_dir) 
        if f.endswith('.py')
    ]
    py_files.sort(key=lambda x: x[1], reverse=True)

    if py_files:
        latest_file_name = py_files[0][0]
        latest_file_path = os.path.join(download_dir, latest_file_name)

        # 去掉文件名中的 "(数字)" 部分
        new_file_name = re.sub(r' \(\d+\)\.py$', '.py', latest_file_name)

        # 拷贝文件
        dest_file_path = os.path.join(workspace_dir, new_file_name)
        shutil.copy2(latest_file_path, dest_file_path)
        print(f"文件已拷贝: {dest_file_path}")
    else:
        print("没有找到 .py 文件")

def main():
    parser = argparse.ArgumentParser(description="将指定目录下最新的 .py 文件拷贝到目标目录，并去掉文件名中的 '(数字)' 部分。")
    parser.add_argument("--download_dir", type=str, default=r"d:\download", help="下载目录")
    parser.add_argument("--workspace_dir", type=str, default=r"d:\workspace\caidao", help="工作目录")
    args = parser.parse_args()

    if os.path.exists(args.download_dir) and os.path.exists(args.workspace_dir):
        copy_latest_py_file(args.download_dir, args.workspace_dir)
    else:
        print("输入的目录不存在，请检查")

if __name__ == "__main__":
    main()