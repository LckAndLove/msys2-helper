import os
import sys
import ctypes
import winreg
import subprocess
import threading
import urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import hashlib
import platform
import json
import uuid

# 导入配置文件
try:
    from auth_config import API_BASE_URL, VALIDATE_ENDPOINT, MAX_ATTEMPTS, TIMEOUT
    AUTH_API_URL = API_BASE_URL + VALIDATE_ENDPOINT
    MAX_AUTH_ATTEMPTS = MAX_ATTEMPTS
    REQUEST_TIMEOUT = TIMEOUT
except ImportError:
    # 如果配置文件不存在，使用默认值
    AUTH_API_URL = "http://localhost:5000/api/validate"
    MAX_AUTH_ATTEMPTS = 3
    REQUEST_TIMEOUT = 10

# 全局变量
msys2_install_path = ""
download_url = "https://mirrors.tuna.tsinghua.edu.cn/msys2/distrib/msys2-x86_64-latest.exe"
installer_filename = "msys2-x86_64-latest.exe"

# 授权相关全局变量
is_authorized = False
auth_attempts = 0

def require_admin():
    """检查并申请管理员权限"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

def get_machine_code():
    """生成机器码"""
    try:
        # 获取CPU信息
        cpu_info = platform.processor()
        
        # 获取主板序列号
        try:
            result = subprocess.run(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                  capture_output=True, text=True, shell=True)
            motherboard_serial = result.stdout.split('\n')[1].strip()
        except:
            motherboard_serial = "unknown"
        
        # 获取硬盘序列号
        try:
            result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                  capture_output=True, text=True, shell=True)
            disk_serial = result.stdout.split('\n')[1].strip()
        except:
            disk_serial = "unknown"
        
        # 获取MAC地址
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
        except:
            mac = "unknown"
        
        # 组合所有信息
        machine_info = f"{cpu_info}_{motherboard_serial}_{disk_serial}_{mac}"
        
        # 生成MD5哈希
        machine_code = hashlib.md5(machine_info.encode()).hexdigest()
        
        return machine_code
    except Exception as e:
        # 如果获取失败，使用备用方案
        fallback_info = f"{platform.system()}_{platform.machine()}_{os.environ.get('COMPUTERNAME', 'unknown')}"
        return hashlib.md5(fallback_info.encode()).hexdigest()

def validate_license(license_key):
    """验证授权码"""
    try:
        machine_code = get_machine_code()
        
        # 准备请求数据
        data = {
            "code": license_key.strip(),
            "machine_code": machine_code
        }
        
        # 发送POST请求
        request = urllib.request.Request(
            AUTH_API_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('status') == 'success':
                return True, result.get('message', '授权成功')
            else:
                return False, result.get('message', '授权失败')
                
    except urllib.error.URLError as e:
        return False, f"网络连接失败: {str(e)}"
    except json.JSONDecodeError:
        return False, "服务器响应格式错误"
    except Exception as e:
        return False, f"验证失败: {str(e)}"

def show_auth_interface(overlay_content, overlay, status_label_main=None):
    """在主窗口上显示授权界面"""
    global auth_attempts, is_authorized
    
    # 清空遮罩层内容
    for widget in overlay_content.winfo_children():
        widget.destroy()
    
    # 标题
    title_label = tk.Label(overlay_content, text="🔒 软件授权验证", 
                          font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
    title_label.pack(pady=20)
    
    # 说明文本
    info_label = tk.Label(overlay_content, text="请输入您的授权码以继续使用软件", 
                         font=('Arial', 12), fg='#bdc3c7', bg='#2c3e50')
    info_label.pack(pady=10)
    
    # 授权码输入框架
    input_frame = tk.Frame(overlay_content, bg='#2c3e50')
    input_frame.pack(pady=20)
    
    # 授权码标签
    license_label = tk.Label(input_frame, text="授权码：", 
                           font=('Arial', 12), fg='white', bg='#2c3e50')
    license_label.pack(anchor=tk.W)
    
    # 授权码输入框
    license_entry = tk.Entry(input_frame, font=('Arial', 12), width=30, 
                           relief=tk.FLAT, bd=5, highlightthickness=2)
    license_entry.pack(pady=5, ipady=5)
    license_entry.focus()
    
    # 状态标签
    status_label = tk.Label(overlay_content, text="", font=('Arial', 10), 
                          fg='#e74c3c', bg='#2c3e50')
    status_label.pack(pady=10)
    
    # 按钮框架
    button_frame = tk.Frame(overlay_content, bg='#2c3e50')
    button_frame.pack(pady=20)
    
    def on_validate():
        global auth_attempts, is_authorized
        
        license_key = license_entry.get().strip()
        if not license_key:
            status_label.config(text="请输入授权码", fg='#e74c3c')
            return
        
        status_label.config(text="正在验证授权码...", fg='#f39c12')
        overlay.update()
        
        # 验证授权码
        success, message = validate_license(license_key)
        
        if success:
            is_authorized = True
            status_label.config(text="授权成功！", fg='#27ae60')
            # 延迟销毁遮罩层并更新主状态
            def remove_overlay():
                overlay.destroy()
                if status_label_main:
                    status_label_main.config(text="授权验证成功，可以开始使用软件")
            overlay.after(1000, remove_overlay)
        else:
            auth_attempts += 1
            remaining = MAX_AUTH_ATTEMPTS - auth_attempts
            
            if remaining > 0:
                status_label.config(text=f"{message} (剩余尝试次数: {remaining})", fg='#e74c3c')
                license_entry.delete(0, tk.END)
                license_entry.focus()
            else:
                status_label.config(text="授权失败次数过多，程序将退出", fg='#e74c3c')
                overlay.after(2000, lambda: sys.exit(1))
    
    def on_cancel():
        sys.exit(0)
    
    # 确定按钮
    validate_btn = tk.Button(button_frame, text="验证授权", 
                           command=on_validate, 
                           font=('Arial', 12, 'bold'), 
                           bg='#3498db', fg='white', 
                           relief=tk.FLAT, padx=20, pady=8,
                           activebackground='#2980b9', activeforeground='white')
    validate_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # 取消按钮
    cancel_btn = tk.Button(button_frame, text="取消", 
                         command=on_cancel, 
                         font=('Arial', 12, 'bold'), 
                         bg='#e74c3c', fg='white', 
                         relief=tk.FLAT, padx=20, pady=8,
                         activebackground='#c0392b', activeforeground='white')
    cancel_btn.pack(side=tk.LEFT)
    
    # 回车键绑定
    overlay.bind('<Return>', lambda e: on_validate())
    overlay.focus_set()

def update_status(status_label, message, is_error=False):
    """更新状态标签"""
    color = "red" if is_error else "green"
    status_label.config(text=message, fg=color)
    status_label.update()

def download_msys2(status_label):
    """下载MSYS2安装程序"""
    if os.path.exists(installer_filename):
        update_status(status_label, "安装程序已存在，跳过下载")
        return True
    
    update_status(status_label, "正在下载MSYS2安装程序...")
    try:
        urllib.request.urlretrieve(download_url, installer_filename, 
                                 lambda count, block_size, total_size: 
                                 update_status(status_label, f"下载中: {count * block_size / total_size:.1%}"))
        update_status(status_label, "下载完成！")
        return True
    except Exception as e:
        update_status(status_label, f"下载失败: {str(e)}", True)
        return False

def install_msys2(status_label):
    """启动MSYS2安装程序"""
    if not os.path.exists(installer_filename):
        update_status(status_label, "安装程序不存在，请先下载", True)
        return False
    
    update_status(status_label, "启动安装程序，请完成安装向导...")
    try:
        process = subprocess.Popen(installer_filename, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        process.wait()  # 等待安装程序完成
        update_status(status_label, "MSYS2安装完成！")
        return True
    except Exception as e:
        update_status(status_label, f"安装失败: {str(e)}", True)
        return False

def add_to_system_path(new_paths, status_label):
    """添加路径到系统PATH环境变量"""
    try:
        reg_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
            with winreg.OpenKey(hkey, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as env_key:
                value, _ = winreg.QueryValueEx(env_key, "Path")
                current_paths = value.split(";")
                
                # 检查路径是否已经存在
                paths_added = []
                for path in reversed(new_paths):
                    if path not in current_paths:
                        current_paths.insert(0, path)
                        paths_added.append(path)
                
                if not paths_added:
                    update_status(status_label, "环境变量已包含所有需要的路径")
                    return True
                
                # 写入新的PATH值
                new_value = ";".join(current_paths)
                winreg.SetValueEx(env_key, "Path", 0, winreg.REG_EXPAND_SZ, new_value)
                
                update_status(status_label, f"已添加以下路径到环境变量：\n{'; '.join(paths_added)}")
                return True
    except Exception as e:
        update_status(status_label, f"设置环境变量失败: {str(e)}", True)
        return False

def select_msys2_path(status_label):
    """选择MSYS2安装路径"""
    global msys2_install_path
    # 如果已设置并有效，直接返回
    if msys2_install_path and os.path.exists(os.path.join(msys2_install_path, 'usr', 'bin', 'pacman.exe')):
        update_status(status_label, f"使用已保存的MSYS2路径：{msys2_install_path}")
        return True
    # 从环境变量 PATH 检测 MSYS2 安装路径
    for p in os.environ.get('PATH', '').split(';'):
        p_norm = p.strip('"')
        lower_p = p_norm.lower()
        if lower_p.endswith(os.path.join('usr', 'bin').lower()) or lower_p.endswith(os.path.join('ucrt64', 'bin').lower()):
            candidate = os.path.normpath(os.path.join(p_norm, os.pardir, os.pardir))
            if os.path.exists(os.path.join(candidate, 'usr', 'bin', 'pacman.exe')):
                msys2_install_path = candidate
                update_status(status_label, f"从环境变量找到MSYS2路径：{msys2_install_path}")
                return True
     
    # 默认安装路径
    default_path = r"C:\msys64"
    
    # 如果默认路径存在，直接使用
    if os.path.exists(default_path):
        msys2_install_path = default_path
        update_status(status_label, f"找到MSYS2安装路径：{msys2_install_path}")
        return True
    
    # 打开文件对话框让用户选择
    selected_dir = filedialog.askdirectory(title="请选择MSYS2安装目录")
    if not selected_dir:
        update_status(status_label, "未选择MSYS2安装路径", True)
        return False
    
    msys2_install_path = selected_dir
    update_status(status_label, f"MSYS2安装路径：{msys2_install_path}")
    return True

def set_path_environment(status_label):
    """设置PATH环境变量"""
    global msys2_install_path
    
    # 用户选择MSYS2安装路径
    if not select_msys2_path(status_label):
        return False
    
    # 构建需要添加的路径
    ucrt64_bin = os.path.join(msys2_install_path, "ucrt64", "bin").replace("/", "\\")
    usr_bin = os.path.join(msys2_install_path, "usr", "bin").replace("/", "\\")
    
    # 检查路径是否存在
    paths_to_add = []
    if os.path.exists(ucrt64_bin):
        paths_to_add.append(ucrt64_bin)
    if os.path.exists(usr_bin):
        paths_to_add.append(usr_bin)
    
    if not paths_to_add:
        update_status(status_label, "未找到有效的MSYS2子目录，请检查安装路径", True)
        return False
    
    # 添加路径到环境变量
    return add_to_system_path(paths_to_add, status_label)

def run_pacman_command(command, status_label):
    """运行pacman命令"""
    global msys2_install_path
    
    # 如果没有设置MSYS2路径，先让用户选择
    if not msys2_install_path:
        if not select_msys2_path(status_label):
            return False
    
    # 构造pacman路径
    pacman_path = os.path.join(msys2_install_path, "usr", "bin", "pacman.exe")
    
    # 检查pacman是否存在
    if not os.path.exists(pacman_path):
        update_status(status_label, f"找不到pacman: {pacman_path}", True)
        return False
    
    update_status(status_label, f"运行命令: {command}")
    
    # 运行pacman命令
    try:
        process = subprocess.Popen(
            [pacman_path] + command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # 读取输出并更新状态
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                update_status(status_label, output.strip())
        
        # 等待进程完成
        return_code = process.wait()
        if return_code == 0:
            update_status(status_label, "命令执行成功!")
            return True
        else:
            stderr = process.stderr.read()
            update_status(status_label, f"命令执行失败: {stderr}", True)
            return False
    except Exception as e:
        update_status(status_label, f"执行命令时出错: {str(e)}", True)
        return False

def install_toolchain(status_label):
    """安装基础开发工具链"""
    command = ["-S", "--needed", "--noconfirm", "base-devel", "mingw-w64-ucrt-x86_64-toolchain"]
    return run_pacman_command(command, status_label)

def install_graphics_tools(status_label):
    """安装图形开发库与构建工具"""
    command = ["-S", "--noconfirm", "mingw-w64-ucrt-x86_64-qt6-base", 
               "mingw-w64-ucrt-x86_64-opencv", "mingw-w64-ucrt-x86_64-cmake", "git"]
    return run_pacman_command(command, status_label)

def run_in_thread(function, status_label):
    """在单独线程中运行函数，避免UI冻结"""
    thread = threading.Thread(target=function, args=(status_label,))
    thread.daemon = True
    thread.start()

def create_gui():
    """创建图形用户界面"""
    global is_authorized
    
    # 申请管理员权限
    require_admin()
    
    # 创建主窗口
    root = tk.Tk()
    root.title("C++ 安装助手")
    root.geometry("500x400")
    root.resizable(False, False)
    
    # 创建样式
    style = ttk.Style()
    style.configure("TButton", padding=10, font=('Arial', 10))
    style.configure("TFrame", padding=10)
    
    # 创建主框架
    main_frame = ttk.Frame(root, style="TFrame")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 创建标题
    title_label = tk.Label(main_frame, text="C++ 安装助手", font=('Arial', 16, 'bold'))
    title_label.pack(pady=10)
    
    # 创建按钮
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    # 创建状态标签
    status_frame = ttk.LabelFrame(main_frame, text="执行状态")
    status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    status_label = tk.Label(status_frame, text="准备就绪", anchor="w", justify=tk.LEFT, wraplength=460)
    status_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 创建遮罩层
    overlay = tk.Frame(root, bg='#2c3e50', bd=0)
    overlay.place(x=0, y=0, relwidth=1, relheight=1)
    
    # 遮罩层内容
    overlay_content = tk.Frame(overlay, bg='#2c3e50')
    overlay_content.place(relx=0.5, rely=0.5, anchor='center')
    
    # 遮罩层标题
    overlay_title = tk.Label(overlay_content, text="🔒 软件需要授权验证", 
                           font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
    overlay_title.pack(pady=20)
    
    # 遮罩层说明
    overlay_info = tk.Label(overlay_content, text="请点击下方按钮进行授权验证", 
                          font=('Arial', 12), fg='#bdc3c7', bg='#2c3e50')
    overlay_info.pack(pady=10)
    
    # 授权按钮
    def start_auth():
        show_auth_interface(overlay_content, overlay, status_label)
    
    auth_btn = tk.Button(overlay_content, text="开始授权验证", 
                        command=start_auth, 
                        font=('Arial', 12, 'bold'), 
                        bg='#3498db', fg='white', 
                        relief=tk.FLAT, padx=20, pady=10,
                        activebackground='#2980b9', activeforeground='white')
    auth_btn.pack(pady=20)
    
    # 功能按钮（初始时禁用）
    def protected_command(func):
        """保护的命令，只有授权后才能执行"""
        def wrapper(*args, **kwargs):
            if not is_authorized:
                messagebox.showerror("错误", "请先完成授权验证")
                return
            return func(*args, **kwargs)
        return wrapper
    
    # 下载并安装MSYS2按钮
    download_install_btn = ttk.Button(button_frame, text="[步骤 1] 下载并安装软件",
                                      command=protected_command(lambda: run_in_thread(lambda label: download_msys2(label) and install_msys2(label), status_label)))
    download_install_btn.pack(fill=tk.X, pady=5)
    
    # 设置环境变量按钮
    set_env_btn = ttk.Button(button_frame, text="[步骤 2] 设置环境变量",
                            command=protected_command(lambda: run_in_thread(set_path_environment, status_label)))
    set_env_btn.pack(fill=tk.X, pady=5)
    
    # 安装基础开发工具链按钮
    install_toolchain_btn = ttk.Button(button_frame, text="[步骤 3] 安装基础C++开发工具链",
                                     command=protected_command(lambda: run_in_thread(install_toolchain, status_label)))
    install_toolchain_btn.pack(fill=tk.X, pady=5)
    
    # 安装图形开发工具按钮
    install_graphics_btn = ttk.Button(button_frame, text="[步骤 4] 安装图形开发工具",
                                   command=protected_command(lambda: run_in_thread(install_graphics_tools, status_label)))
    install_graphics_btn.pack(fill=tk.X, pady=5)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    create_gui()