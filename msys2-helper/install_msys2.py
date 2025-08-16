import os
import sys
import ctypes
import winreg
import subprocess
import threading
import urllib.request
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# 版本信息
__version__ = "1.0.0"
__author__ = "lllckkkkkkk"
__description__ = "MSYS2 C++ 开发环境自动化安装和配置工具"

# 全局变量
msys2_install_path = ""
download_url = "https://mirrors.tuna.tsinghua.edu.cn/msys2/distrib/msys2-x86_64-latest.exe"
installer_filename = "msys2-x86_64-latest.exe"

def require_admin():
    """检查并申请管理员权限"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

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

def change_mirror_source(status_label):
    """修改MSYS2镜像源为清华大学镜像"""
    global msys2_install_path
    
    # 如果没有设置MSYS2路径，先让用户选择
    if not msys2_install_path:
        if not select_msys2_path(status_label):
            return False
    
    try:
        # 构造mirrorlist文件路径
        mirrorlist_dir = os.path.join(msys2_install_path, "etc", "pacman.d")
        
        if not os.path.exists(mirrorlist_dir):
            update_status(status_label, f"找不到镜像源配置目录: {mirrorlist_dir}", True)
            return False
        
        # 查找所有mirrorlist文件
        import glob
        mirrorlist_files = glob.glob(os.path.join(mirrorlist_dir, "mirrorlist*"))
        
        if not mirrorlist_files:
            update_status(status_label, "未找到镜像源配置文件", True)
            return False
        
        update_status(status_label, f"找到 {len(mirrorlist_files)} 个镜像源配置文件")
        
        # 备份和修改每个mirrorlist文件
        for mirrorlist_file in mirrorlist_files:
            try:
                # 创建备份
                backup_file = mirrorlist_file + ".backup"
                if not os.path.exists(backup_file):
                    import shutil
                    shutil.copy2(mirrorlist_file, backup_file)
                    update_status(status_label, f"已备份: {os.path.basename(mirrorlist_file)}")
                
                # 读取原文件内容
                with open(mirrorlist_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换镜像源
                import re
                # 匹配 http://mirror.msys2.org/ 或 https://mirror.msys2.org/
                new_content = re.sub(
                    r'https?://mirror\.msys2\.org/',
                    'https://mirrors.tuna.tsinghua.edu.cn/msys2/',
                    content
                )
                
                # 写入修改后的内容
                with open(mirrorlist_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                update_status(status_label, f"✓ 已更新: {os.path.basename(mirrorlist_file)}")
                
            except Exception as e:
                update_status(status_label, f"修改 {os.path.basename(mirrorlist_file)} 失败: {str(e)}", True)
                return False
        
        update_status(status_label, "镜像源已成功切换到清华大学镜像！")
        update_status(status_label, "建议运行 pacman -Sy 更新软件包数据库")
        return True
        
    except Exception as e:
        update_status(status_label, f"修改镜像源失败: {str(e)}", True)
        return False

def run_in_thread(function, status_label):
    """在单独线程中运行函数，避免UI冻结"""
    thread = threading.Thread(target=function, args=(status_label,))
    thread.daemon = True
    thread.start()

def reset_vscode(status_label):
    """重置VS Code配置"""
    try:
        import shutil
        
        # VS Code配置路径
        vscode_config_path = os.path.expanduser(r'~\AppData\Roaming\Code')
        vscode_extensions_path = os.path.expanduser(r'~\.vscode')
        
        # 检查路径是否存在
        paths_to_remove = []
        if os.path.exists(vscode_config_path):
            paths_to_remove.append(('用户配置', vscode_config_path))
        if os.path.exists(vscode_extensions_path):
            paths_to_remove.append(('扩展配置', vscode_extensions_path))
        
        if not paths_to_remove:
            update_status(status_label, "未找到VS Code配置文件，可能VS Code未安装或已重置")
            return True
        
        # 直接删除VS Code配置
        for desc, path in paths_to_remove:
            if os.path.exists(path):
                update_status(status_label, f"正在删除{desc}: {path}")
                shutil.rmtree(path, ignore_errors=True)
                
                # 验证删除是否成功
                if os.path.exists(path):
                    update_status(status_label, f"警告: {desc}可能未完全删除", True)
                else:
                    update_status(status_label, f"✓ {desc}已成功删除")
        
        update_status(status_label, "VS Code重置完成！")
        return True
        
    except Exception as e:
        update_status(status_label, f"重置VS Code配置失败: {str(e)}", True)
        return False

def confirm_vscode_reset():
    """确认VS Code重置操作"""
    message = """此操作将会删除以下VS Code配置：
    
• 用户设置和首选项
• 所有已安装的扩展
• 工作区配置
• 快捷键设置
• 主题和颜色配置

删除后无法恢复，是否确定要重置VS Code配置？"""
    
    return messagebox.askyesno("确认重置VS Code", message, icon='warning')


def show_about():
    """显示关于对话框"""
    about_text = f"""C++ 安装助手 v{__version__}

{__description__}

作者: {__author__}

功能特性:
• 自动下载和安装 MSYS2
• 配置环境变量
• 切换到清华大学镜像源
• 安装 C++ 开发工具链
• 安装图形开发库 (Qt6, OpenCV)
• 生成 VSCode 配置文件
• 重置 VSCode 配置

© 2025 版权所有"""
    
    messagebox.showinfo("关于", about_text)

######################### pkg-config -> VSCode 配置 相关函数 #########################
def get_pkg_config_info(packages, status_label):
    """获取 pkg-config 对应包的 cflags 和 libs"""
    pkg_info = {}
    try:
        update_status(status_label, f"正在运行 pkg-config: {' '.join(packages)}")
        cflags = subprocess.check_output(['pkg-config', '--cflags'] + packages, universal_newlines=True, stderr=subprocess.STDOUT).strip()
        libs = subprocess.check_output(['pkg-config', '--libs'] + packages, universal_newlines=True, stderr=subprocess.STDOUT).strip()
        pkg_info['cflags'] = cflags
        pkg_info['libs'] = libs
        update_status(status_label, 'pkg-config 查询完成')
    except subprocess.CalledProcessError as e:
        output = getattr(e, 'output', str(e))
        update_status(status_label, f"pkg-config 失败: {output}", True)
    except Exception as e:
        update_status(status_label, f"pkg-config 异常: {e}", True)
    return pkg_info

def convert_to_windows_path(path):
    """将 Linux 风格路径转换为 Windows 风格路径，并简化路径"""
    path = path.replace('/', '\\')
    return os.path.normpath(path)

def create_task_json(gcc_path, packages, pkg_info):
    """生成 tasks.json 的 dict 结构"""
    args = [
        "-fdiagnostics-color=always",
        "-g",
        "${file}",
        "-o",
        "${fileDirname}\\${fileBasenameNoExtension}.exe"
    ]

    added_libs = set()
    cflags = pkg_info.get('cflags', '')
    libs = pkg_info.get('libs', '')

    if cflags:
        for flag in cflags.split():
            args.append(convert_to_windows_path(flag))

    if libs:
        for flag in libs.split():
            if flag.startswith('-l') and flag not in added_libs:
                args.append(flag)
                added_libs.add(flag)
            else:
                args.append(convert_to_windows_path(flag))

    task = {
        "version": "2.0.0",
        "tasks": [
            {
                "type": "cppbuild",
                "label": "C/C++: g++.exe 生成活动文件",
                "command": gcc_path,
                "args": args,
                "options": {"cwd": "${fileDirname}"},
                "problemMatcher": ["$gcc"],
                "group": {"kind": "build", "isDefault": True},
                "detail": "调试器生成的任务。"
            }
        ]
    }
    return task

def get_gcc_path(libs, status_label):
    """通过 libs 路径推断 g++ 的路径"""
    update_status(status_label, "推断 g++ 路径...")
    lib_path = None
    for flag in libs.split():
        if flag.startswith('-L'):
            lib_path = flag[2:]
            break

    if not lib_path:
        raise RuntimeError('未找到 -L 参数中的库路径.')

    bin_dir = os.path.normpath(os.path.join(lib_path, '..', 'bin'))
    gcc_path = os.path.normpath(os.path.join(bin_dir, 'g++.exe'))
    if os.path.exists(gcc_path):
        update_status(status_label, f"找到 g++: {gcc_path}")
        return gcc_path
    else:
        raise RuntimeError(f"g++ 未在推断路径找到: {gcc_path}")

def create_c_cpp_properties_json(cflags, gcc_path):
    include_list = ["${workspaceFolder}/**"]
    
    if cflags:
        for flag in cflags.split():
            if flag.startswith('-I'):
                include_path = convert_to_windows_path(flag[2:])
                include_list.append(os.path.join(include_path, '**'))

    cpp_properties = {
        "configurations": [
            {
                "name": "Win32",
                "includePath": include_list,
                "defines": ["_DEBUG", "UNICODE", "_UNICODE"],
                "compilerPath": gcc_path,
                "cStandard": "c17",
                "cppStandard": "gnu++17",
                "intelliSenseMode": "windows-gcc-x64"
            }
        ],
        "version": 4
    }
    return cpp_properties

def save_to_tasks_json(task_dict, target_dir, status_label):
    task_file = os.path.join(target_dir, ".vscode", "tasks.json")
    try:
        os.makedirs(os.path.join(target_dir, ".vscode"), exist_ok=True)
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_dict, f, ensure_ascii=False, indent=4)
        update_status(status_label, f"任务配置已保存到 {task_file}")
    except Exception as e:
        update_status(status_label, f"保存 tasks.json 失败: {e}", True)

def save_to_c_cpp_properties_json(cpp_dict, target_dir, status_label):
    cpp_file = os.path.join(target_dir, ".vscode", "c_cpp_properties.json")
    try:
        os.makedirs(os.path.join(target_dir, ".vscode"), exist_ok=True)
        with open(cpp_file, 'w', encoding='utf-8') as f:
            json.dump(cpp_dict, f, ensure_ascii=False, indent=4)
        update_status(status_label, f"c_cpp_properties.json 已保存到 {cpp_file}")
    except Exception as e:
        update_status(status_label, f"保存 c_cpp_properties.json 失败: {e}", True)

def generate_vscode_configs(target_dir, packages, status_label):
    try:
        update_status(status_label, f"开始为包生成配置: {', '.join(packages)}")
        pkg_info = get_pkg_config_info(packages, status_label)
        libs = pkg_info.get('libs', '')
        cflags = pkg_info.get('cflags', '')
        if not libs:
            update_status(status_label, "未获取到 libs 信息，无法继续", True)
            return False
        gcc_path = get_gcc_path(libs, status_label)
        task_dict = create_task_json(gcc_path, packages, pkg_info)
        cpp_dict = create_c_cpp_properties_json(cflags, gcc_path)
        save_to_tasks_json(task_dict, target_dir, status_label)
        save_to_c_cpp_properties_json(cpp_dict, target_dir, status_label)
        update_status(status_label, "VSCode 配置生成完成")
        return True
    except Exception as e:
        update_status(status_label, f"生成配置失败: {e}", True)
        return False

######################### 结束 pkg-config 相关函数 #########################

def create_gui():
    """创建图形用户界面"""
    
    # 申请管理员权限
    require_admin()
    
    # 创建主窗口
    root = tk.Tk()
    root.title(f"C++ 安装助手 v{__version__}")
    root.geometry("400x660")
    root.resizable(False, False)
    
    # 创建样式
    style = ttk.Style()
    style.configure("TButton", padding=10, font=('Arial', 10))
    style.configure("TFrame", padding=10)
    
    # 创建主框架
    main_frame = ttk.Frame(root, style="TFrame")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 创建标题
    title_label = tk.Label(main_frame, text=f"C++ 安装助手 v{__version__}", font=('Arial', 16, 'bold'))
    title_label.pack(pady=10)
    
    # 创建按钮
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    # 创建状态标签
    status_frame = ttk.LabelFrame(main_frame, text="执行状态")
    status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    status_label = tk.Label(status_frame, text="准备就绪", anchor="w", justify=tk.LEFT, wraplength=460)
    status_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 下载并安装MSYS2按钮
    download_install_btn = ttk.Button(button_frame, text="[步骤 1] 下载并安装软件",
                                      command=lambda: run_in_thread(lambda label: download_msys2(label) and install_msys2(label), status_label))
    download_install_btn.pack(fill=tk.X, pady=5)
    
    # 设置环境变量按钮
    set_env_btn = ttk.Button(button_frame, text="[步骤 2] 设置环境变量",
                            command=lambda: run_in_thread(set_path_environment, status_label))
    set_env_btn.pack(fill=tk.X, pady=5)
    
    # 切换镜像源按钮
    change_mirror_btn = ttk.Button(button_frame, text="[步骤 2.5] 切换到清华镜像源",
                                  command=lambda: run_in_thread(change_mirror_source, status_label))
    change_mirror_btn.pack(fill=tk.X, pady=5)
    
    # 安装基础开发工具链按钮
    install_toolchain_btn = ttk.Button(button_frame, text="[步骤 3] 安装基础C++开发工具链",
                                     command=lambda: run_in_thread(install_toolchain, status_label))
    install_toolchain_btn.pack(fill=tk.X, pady=5)
    
    # 安装图形开发工具按钮
    install_graphics_btn = ttk.Button(button_frame, text="[步骤 4] 安装图形开发工具",
                                   command=lambda: run_in_thread(install_graphics_tools, status_label))
    install_graphics_btn.pack(fill=tk.X, pady=5)
    
    # 添加分隔线
    separator = ttk.Separator(button_frame, orient='horizontal')
    separator.pack(fill=tk.X, pady=10)

    # 生成 VSCode 配置按钮 (来自 TEMP.py 的功能)
    def open_generate_dialog():
        dialog = tk.Toplevel(root)
        dialog.title("生成运行配置")
        dialog.geometry("420x300")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="选择目标文件夹：").pack(anchor='w', padx=10, pady=(10,0))
        target_var = tk.StringVar(value=os.getcwd())
        entry = ttk.Entry(dialog, textvariable=target_var, width=60)
        entry.pack(padx=10, pady=5)

        def browse_folder():
            d = filedialog.askdirectory(title="选择目标文件夹", initialdir=target_var.get())
            if d:
                target_var.set(d)

        ttk.Button(dialog, text="浏览...", command=browse_folder).pack(padx=10, pady=5)

        ttk.Label(dialog, text="选择或输入 pkg-config 包（逗号或空格分隔）：").pack(anchor='w', padx=10, pady=(10,0))
        default_pkgs = 'opencv4 Qt6Concurrent Qt6Core Qt6DBus Qt6Gui Qt6Network Qt6OpenGL Qt6OpenGLWidgets Qt6Platform Qt6PrintSupport Qt6Sql Qt6Test Qt6Widgets Qt6Xml'
        pkg_var = tk.StringVar(value=default_pkgs)
        pkg_entry = ttk.Entry(dialog, textvariable=pkg_var, width=60)
        pkg_entry.pack(padx=10, pady=5)

        def on_generate():
            target = target_var.get().strip()
            if not target:
                messagebox.showerror("错误", "请先选择目标文件夹")
                return
            pkgs = [p for p in pkg_var.get().replace(',', ' ').split() if p]
            if not pkgs:
                messagebox.showerror("错误", "请至少指定一个 pkg-config 包名")
                return
            dialog.destroy()
            run_in_thread(lambda label: generate_vscode_configs(target, pkgs, label), status_label)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="生成", command=on_generate).pack(side=tk.RIGHT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)

    gen_vscode_btn = ttk.Button(button_frame, text="[工具] 生成运行配置",
                                command=open_generate_dialog)
    gen_vscode_btn.pack(fill=tk.X, pady=5)

    # VS Code重置按钮
    def reset_vscode_with_confirm():
        if confirm_vscode_reset():
            run_in_thread(reset_vscode, status_label)

    reset_vscode_btn = ttk.Button(button_frame, text="[工具] 重置VS Code配置",
                                 command=reset_vscode_with_confirm)
    reset_vscode_btn.pack(fill=tk.X, pady=5)
    
    # 关于按钮
    about_btn = ttk.Button(button_frame, text="关于",
                          command=show_about)
    about_btn.pack(fill=tk.X, pady=5)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    create_gui()