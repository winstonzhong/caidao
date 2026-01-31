'''
Created on 2024 Oct 26

@author: Winston
'''
import array
import json
import os
import platform
import random
import socket
import struct
import subprocess
import threading
import time


class IcmpScan(object):

    def __init__(self, ip_list, timeout=3):
        self.ips = ip_list
        self.__data = struct.pack('d', time.time())  # 需要发送的数据
        self.__id = random.randint(1000, 65535)
        self.timeout = timeout
        self.socket = self.rawSocket
        self.finished = False
    
    @classmethod
    def 得到套接字(cls, timeout=3):
        try:
            s = socket.socket(socket.AF_INET, 
                                 socket.SOCK_RAW, 
                                 socket.getprotobyname("icmp")
                                 )
            s.settimeout(timeout)
            return s
        except PermissionError as e:
            import os
            import sys
            if os.name == 'posix':  # Linux/Mac
                raise PermissionError(
                    "创建原始套接字需要 root 权限。\n"
                    "解决方案:\n"
                    "1. 使用 sudo 运行: sudo python your_script.py\n"
                    "2. 赋予 Python 权限: sudo setcap cap_net_raw+ep $(which python)\n"
                    f"3. 当前用户: {os.getlogin()}, UID: {os.getuid()}"
                ) from e
            raise
    
    @property
    def rawSocket(self):
        try:
            Sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
            Sock.settimeout(self.timeout)
        except:
            Sock = self.rawSocket
        return Sock
    
    @classmethod
    def inCksum(cls, packet):
        if len(packet) & 1:
            packet = packet + '\0'
        words = array.array('h', packet)
        total = 0
        for word in words:
            total += (word & 0xffff)
        total = (total >> 16) + (total & 0xffff)
        total = total + (total >> 16)
        return (~total) & 0xffff
    
    @classmethod
    def 测试数据(cls):
        return struct.pack('d', time.time())

    @classmethod
    def 随机ID(cls):
        return random.randint(1000, 65535)
    
    @classmethod
    def create_packet(cls, ID):
        header = struct.pack('bbHHh', 8, 0, 0, ID, 0)
        data = cls.测试数据()
        packet = header + data
        chkSum = cls.inCksum(packet)
        header = struct.pack('bbHHh', 8, 0, chkSum, ID, 0)
        return header + data

    def recv_packet(self):
        while 1:
            try:
                recv_packet, addr = self.socket.recvfrom(1024)
                type, code, checksum, packet_ID, sequence = struct.unpack("bbHHh", recv_packet[20:28])
                if packet_ID == self.__id:
                    ttl = struct.unpack("!BBHHHBBHII", recv_packet[:20])[5]
                    print(f"检测到存活设备: {addr[0]}  ttl: {ttl}")
            except:
                if self.finished:
                    break

    @classmethod
    def 创建数据包(cls):
        ID = cls.随机ID()
        header = struct.pack('bbHHh', 8, 0, 0, ID, 0)
        data = cls.测试数据()
        packet = header + data
        chkSum = cls.inCksum(packet)
        header = struct.pack('bbHHh', 8, 0, chkSum, ID, 0)
        return header + data, ID


    @classmethod
    def 接收数据(cls, 套接字, ID):
        recv_packet, addr = 套接字.recvfrom(1024)
        r = struct.unpack("bbHHh", recv_packet[20:28])
        d = {
            'type':r[0],
            'code':r[1],
            'checksum':r[2],
            'packet_ID':r[3],
            'sequence':r[4],
            }
        print(json.dumps(d, indent=3))
        result = d.get('packet_ID') == ID
        if result:
            ttl = struct.unpack("!BBHHHBBHII", recv_packet[:20])[5]
            print(f"检测到存活设备: {addr[0]}  ttl: {ttl}")
        return result
    
    @classmethod
    def 检测设备状态(cls, ip, use_ping_fallback=True):
        """
        检测设备是否存活
        
        Args:
            ip: IP 地址
            use_ping_fallback: 权限不足时是否使用系统 ping 命令作为备选
        
        Returns:
            bool: 设备是否存活
        """
        try:
            s = cls.得到套接字()
            packet, ID = cls.创建数据包()
            s.sendto(packet, (ip, 0))
            try:
                return cls.接收数据(s, ID)
            except TimeoutError:
                return False
        except PermissionError:
            if use_ping_fallback and os.name == 'posix':
                # Linux/Mac 无权限时使用系统 ping 命令
                return cls._ping_with_system_command(ip)
            raise
    
    @classmethod
    def _ping_with_system_command(cls, ip, timeout=3):
        """
        使用系统 ping 命令检测（无需 root 权限）
        
        Returns:
            bool: 设备是否存活
        """
        import subprocess
        import platform
        
        system = platform.system().lower()
        
        if system == 'linux':
            # Linux: -c 次数, -W 超时秒数
            cmd = ['ping', '-c', '1', '-W', str(timeout), ip]
        elif system == 'darwin':  # macOS
            # Mac: -c 次数, -t 超时秒数
            cmd = ['ping', '-c', '1', '-t', str(timeout), ip]
        else:
            # Windows: -n 次数, -w 超时毫秒
            cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout + 2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
        

    def start(self):
        random.shuffle(self.ips)  # 乱序一下地址
        packet = self.create_packet()
        time_space = 1 / 1000
        t = threading.Thread(target=self.recv_packet,)
        t.start()
        for i, ip in enumerate(self.ips):
            try:
                self.socket.sendto(packet, (ip, 0))
                time.sleep(time_space)
            except socket.timeout:
                break
            except:
                pass
        self.finished = True
        time.sleep(self.timeout + 1)
        self.socket.close()
        t.join()


if __name__ == '__main__':
    ip_list = ['172.16.0.' + str(i) for i in range(1, 255)]
    icmp_scan = IcmpScan(ip_list)
    icmp_scan.start()
