import subprocess
import platform
import re

def is_connected_to_specific_lan(unique_identifier: str, identifier_type: str = "dns") -> bool:
    """
    判断设备是否连接到特定局域网
    
    参数:
        unique_identifier: 局域网的唯一标识（DNS服务器IP、网关IP或特定IP）
        identifier_type: 标识类型，可选值为 "dns"（默认）、"gateway" 或 "ip"
    
    返回:
        bool: 如果连接到指定局域网返回True，否则返回False
    """
    try:
        if identifier_type == "dns":
            # 获取当前网络的DNS服务器列表
            system = platform.system().lower()
            dns_servers = []
            
            if system == "windows":
                result = subprocess.check_output("ipconfig /all", shell=True).decode("utf-8", errors="ignore")
                dns_pattern = re.compile(r"DNS 服务器[\s:]+([\d\.]+)")
                dns_servers = dns_pattern.findall(result)
            elif system == "linux":
                try:
                    with open("/etc/resolv.conf", "r") as f:
                        content = f.read()
                        dns_pattern = re.compile(r"nameserver\s+([\d\.]+)")
                        dns_servers = dns_pattern.findall(content)
                except Exception:
                    # 备选方法：使用nmcli命令
                    result = subprocess.check_output("nmcli dev show", shell=True).decode("utf-8", errors="ignore")
                    dns_pattern = re.compile(r"IP4.DNS\[\d+\]:\s+([\d\.]+)")
                    dns_servers = dns_pattern.findall(result)
            elif system == "darwin":  # macOS
                result = subprocess.check_output("scutil --dns", shell=True).decode("utf-8", errors="ignore")
                dns_pattern = re.compile(r"nameserver\s+:\s+([\d\.]+)")
                dns_servers = dns_pattern.findall(result)
            
            return unique_identifier in dns_servers
            
        elif identifier_type == "gateway":
            # 获取当前网络的网关
            system = platform.system().lower()
            gateway = ""
            
            if system == "windows":
                result = subprocess.check_output("route print", shell=True).decode("utf-8", errors="ignore")
                gateway_pattern = re.compile(r"0.0.0.0\s+0.0.0.0\s+([\d\.]+)")
                match = gateway_pattern.search(result)
                if match:
                    gateway = match.group(1)
            elif system == "linux" or system == "darwin":
                result = subprocess.check_output("netstat -rn", shell=True).decode("utf-8", errors="ignore")
                gateway_pattern = re.compile(r"0.0.0.0\s+([\d\.]+)")
                match = gateway_pattern.search(result)
                if match:
                    gateway = match.group(1)
            
            return unique_identifier == gateway
            
        elif identifier_type == "ip":
            # 检查特定IP是否可达
            system = platform.system().lower()
            ping_cmd = ["ping", "-c", "1", "-W", "1"] if system != "windows" else ["ping", "-n", "1", "-w", "1000"]
            ping_cmd.append(unique_identifier)
            
            result = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
            
        else:
            raise ValueError("不支持的标识类型，请使用 'dns', 'gateway' 或 'ip'")
            
    except Exception as e:
        print(f"检查局域网连接时出错: {e}")
        return False

# 示例用法
if __name__ == "__main__":
    # 检查是否连接到使用特定DNS服务器的局域网
    print(is_connected_to_specific_lan("8.8.8.8", "dns"))
    
    # 检查网关是否匹配
    print(is_connected_to_specific_lan("192.168.1.1", "gateway"))
    
    # 检查特定IP是否可达
    print(is_connected_to_specific_lan("192.168.1.100", "ip"))
