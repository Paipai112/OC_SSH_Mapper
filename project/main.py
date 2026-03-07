import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import base64
import webbrowser
import threading
import socket
import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException
import time
import pystray
from PIL import Image, ImageDraw

# 配置文件路径
CONFIG_FILE = "openclaw_forward_config.json"
# 环境变量名
PASSWORD_ENV_VAR = "OPENCLAW_SSH_PASSWORD"

# 默认配置
DEFAULT_CONFIG = {
    "ssh_host": "",          # 服务器公网IP
    "ssh_port": 22,          # SSH端口
    "ssh_user": "root",      # SSH用户名
    "local_port": 18789,     # 本地端口
    "remote_port": 18789,    # 服务器OpenClaw端口
    "remember_password": False,
    "encrypted_password": "" # 加密后的密码
}

class OpenClawSSHForwarder:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenClaw SSH 转发工具")
        self.root.geometry("450x420")  # 拉长窗口，显示完整文字
        self.root.resizable(True, True)  # 允许自由拉伸
        
        # 加载配置
        self.config = self.load_config()
        # SSH转发相关变量
        self.forward_thread = None
        self.ssh_client = None
        self.forward_server = None
        self.is_running = False
        self.lock = threading.Lock()
        
        # 系统托盘相关
        self.tray = None
        self.tray_icon = None
        
        # 构建UI
        self.build_ui()
        
        # 关键：添加窗口关闭钩子（改为隐藏窗口）
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # 创建系统托盘
        self.create_tray()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # 补充缺失的配置项
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            messagebox.warning("配置加载失败", f"使用默认配置：{str(e)}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.error("配置保存失败", str(e))
    
    def encrypt_password(self, password):
        """简单加密密码（Base64）"""
        if not password:
            return ""
        return base64.b64encode(password.encode("utf-8")).decode("utf-8")
    
    def decrypt_password(self, encrypted_pwd):
        """解密密码"""
        if not encrypted_pwd:
            return ""
        try:
            return base64.b64decode(encrypted_pwd.encode("utf-8")).decode("utf-8")
        except:
            return ""
    
    def build_ui(self):
        """构建界面"""
        # 样式
        style = ttk.Style()
        style.configure("TLabel", font=("微软雅黑", 10))
        style.configure("TEntry", font=("微软雅黑", 10))
        style.configure("TButton", font=("微软雅黑", 10))
        
        # 网格布局配置
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        
        # 1. 服务器IP
        ttk.Label(self.root, text="服务器公网IP：").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.ssh_host_entry = ttk.Entry(self.root)
        self.ssh_host_entry.insert(0, self.config["ssh_host"])
        self.ssh_host_entry.grid(row=0, column=1, padx=10, pady=8, sticky="we")
        
        # 2. SSH端口
        ttk.Label(self.root, text="SSH端口：").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.ssh_port_entry = ttk.Entry(self.root)
        self.ssh_port_entry.insert(0, self.config["ssh_port"])
        self.ssh_port_entry.grid(row=1, column=1, padx=10, pady=8, sticky="we")
        
        # 3. SSH用户名
        ttk.Label(self.root, text="SSH用户名：").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        self.ssh_user_entry = ttk.Entry(self.root)
        self.ssh_user_entry.insert(0, self.config["ssh_user"])
        self.ssh_user_entry.grid(row=2, column=1, padx=10, pady=8, sticky="we")
        
        # 4. 本地端口
        ttk.Label(self.root, text="本地端口：").grid(row=3, column=0, padx=10, pady=8, sticky="e")
        self.local_port_entry = ttk.Entry(self.root)
        self.local_port_entry.insert(0, self.config["local_port"])
        self.local_port_entry.grid(row=3, column=1, padx=10, pady=8, sticky="we")
        
        # 5. 远程端口
        ttk.Label(self.root, text="远程端口：").grid(row=4, column=0, padx=10, pady=8, sticky="e")
        self.remote_port_entry = ttk.Entry(self.root)
        self.remote_port_entry.insert(0, self.config["remote_port"])
        self.remote_port_entry.grid(row=4, column=1, padx=10, pady=8, sticky="we")
        
        # 6. 密码
        ttk.Label(self.root, text="SSH密码：").grid(row=5, column=0, padx=10, pady=8, sticky="e")
        self.password_entry = ttk.Entry(self.root, show="*")
        # 填充密码（环境变量 > 记住的密码）
        env_pwd = os.environ.get(PASSWORD_ENV_VAR, "")
        if env_pwd:
            self.password_entry.insert(0, env_pwd)
        elif self.config["remember_password"]:
            self.password_entry.insert(0, self.decrypt_password(self.config["encrypted_password"]))
        self.password_entry.grid(row=5, column=1, padx=10, pady=8, sticky="we")
        
        # 7. 记住密码
        self.remember_pwd_var = tk.BooleanVar(value=self.config["remember_password"])
        self.remember_pwd_check = ttk.Checkbutton(
            self.root, text="记住密码", variable=self.remember_pwd_var
        )
        self.remember_pwd_check.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        
        # 8. 操作按钮
        self.start_btn = ttk.Button(self.root, text="启动转发", command=self.start_forward)
        self.start_btn.grid(row=7, column=0, columnspan=2, padx=10, pady=15, sticky="we")
        
        self.stop_btn = ttk.Button(self.root, text="停止转发", command=self.stop_forward, state="disabled")
        self.stop_btn.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky="we")
        
        # 状态标签
        self.status_label = ttk.Label(self.root, text="状态：未连接", foreground="gray")
        self.status_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5)
    
    def create_tray_icon(self):
        """创建简单的托盘图标（无需外部图片）"""
        # 创建一个简单的红色圆形图标
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.ellipse((10, 10, 54, 54), fill=(255, 0, 0))
        return image
    
    def create_tray(self):
        """创建系统托盘"""
        # 创建托盘图标
        self.tray_icon = self.create_tray_icon()
        
        # 定义托盘菜单
        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self.show_window),
            pystray.MenuItem("退出程序", self.on_exit)
        )
        
        # 创建托盘
        self.tray = pystray.Icon(
            "OpenClaw转发工具",
            self.tray_icon,
            "OpenClaw SSH 转发工具",
            menu
        )
        
        # 启动托盘线程
        threading.Thread(target=self.tray.run, daemon=True).start()
    
    def hide_window(self):
        """隐藏窗口到托盘"""
        self.root.withdraw()  # 隐藏窗口
    
    def show_window(self, icon=None, item=None):
        """从托盘显示窗口"""
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 置顶窗口
        self.root.focus_force()  # 获取焦点
    
    def check_port_available(self, port):
        """检查端口是否可用，若占用则尝试释放"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
            return True
        except:
            # 尝试强制释放端口
            self.release_port(port)
            time.sleep(0.5)
            # 再次检查
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                return True
            except:
                return False
    
    def release_port(self, port):
        """强制释放指定端口"""
        try:
            # 创建临时socket，设置SO_LINGER强制关闭
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x00\x00\x00\x00')
            s.bind(("127.0.0.1", port))
            s.close()
        except:
            pass
    
    def handle_forward(self, client_socket, ssh_transport, remote_host, remote_port):
        """处理单个转发连接，使用双线程实现全双工通信"""
        try:
            # 建立SSH通道到服务器目标端口
            chan = ssh_transport.open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                client_socket.getsockname()
            )
            if chan is None:
                client_socket.close()
                return

            # 定义两个方向的转发函数
            def forward_local_to_remote():
                """本地 -> 服务器"""
                try:
                    while self.is_running:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        chan.send(data)
                except:
                    pass
                finally:
                    chan.close()

            def forward_remote_to_local():
                """服务器 -> 本地"""
                try:
                    while self.is_running:
                        data = chan.recv(1024)
                        if not data:
                            break
                        client_socket.send(data)
                except:
                    pass
                finally:
                    client_socket.close()

            # 启动两个线程分别处理两个方向
            t1 = threading.Thread(target=forward_local_to_remote, daemon=True)
            t2 = threading.Thread(target=forward_remote_to_local, daemon=True)
            t1.start()
            t2.start()

            # 等待两个线程都结束
            t1.join()
            t2.join()

        except Exception as e:
            pass
        finally:
            try:
                client_socket.close()
            except:
                pass
            try:
                chan.close()
            except:
                pass
    
    def forward_ssh(self):
        """SSH本地端口转发核心逻辑（和命令行-L一致）"""
        with self.lock:
            if self.is_running:
                return
        
        try:
            # 获取配置
            ssh_host = self.ssh_host_entry.get().strip()
            ssh_port = int(self.ssh_port_entry.get().strip())
            ssh_user = self.ssh_user_entry.get().strip()
            local_port = int(self.local_port_entry.get().strip())
            remote_port = int(self.remote_port_entry.get().strip())
            password = self.password_entry.get().strip()
            
            # 基础校验
            if not ssh_host:
                raise ValueError("服务器公网IP不能为空")
            if not self.check_port_available(local_port):
                raise ValueError(f"本地端口 {local_port} 已被占用，且无法自动释放，请更换端口")
            
            # 更新配置
            self.config["ssh_host"] = ssh_host
            self.config["ssh_port"] = ssh_port
            self.config["ssh_user"] = ssh_user
            self.config["local_port"] = local_port
            self.config["remote_port"] = remote_port
            self.config["remember_password"] = self.remember_pwd_var.get()
            
            # 保存密码（如果勾选记住）
            if self.config["remember_password"]:
                self.config["encrypted_password"] = self.encrypt_password(password)
            else:
                self.config["encrypted_password"] = ""
            
            # 保存配置
            self.save_config()
            
            # 创建SSH客户端
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接SSH
            self.root.after(0, lambda: self.status_label.config(text="状态：正在连接...", foreground="blue"))
            self.ssh_client.connect(
                hostname=ssh_host,
                port=ssh_port,
                username=ssh_user,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            with self.lock:
                self.is_running = True
            
            # 创建本地监听socket（关键：设置SO_LINGER确保关闭时释放端口）
            self.forward_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.forward_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 设置SO_LINGER，强制关闭时立即释放端口
            self.forward_server.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x01\x00\x00\x00')
            self.forward_server.bind(("127.0.0.1", local_port))
            self.forward_server.listen(5)
            
            # 更新状态
            self.root.after(0, lambda: self.status_label.config(text="状态：转发成功", foreground="green"))
            self.root.after(0, lambda: self.start_btn.config(state="disabled"))
            self.root.after(0, lambda: self.stop_btn.config(state="normal"))
            
            # 自动打开浏览器
            web_url = f"http://localhost:{local_port}"
            webbrowser.open(web_url)
            
            # 循环接受本地连接并转发
            while self.is_running:
                try:
                    # 设置超时，避免阻塞无法退出
                    self.forward_server.settimeout(0.5)
                    client, addr = self.forward_server.accept()
                    # 启动线程处理单个连接
                    threading.Thread(
                        target=self.handle_forward,
                        args=(client, self.ssh_client.get_transport(), "127.0.0.1", remote_port),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue  # 超时仅用于检测是否需要退出
                except Exception as e:
                    if self.is_running:
                        raise e
                    else:
                        break
                
        except ValueError as e:
            self.root.after(0, lambda: messagebox.showerror("参数错误", str(e)))
            self.root.after(0, lambda: self.status_label.config(text="状态：参数错误", foreground="red"))
        except AuthenticationException:
            self.root.after(0, lambda: messagebox.showerror("认证失败", "SSH密码错误或用户名错误"))
            self.root.after(0, lambda: self.status_label.config(text="状态：认证失败", foreground="red"))
        except SSHException as e:
            self.root.after(0, lambda: messagebox.showerror("SSH错误", f"连接失败：{str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="状态：SSH错误", foreground="red"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("未知错误", str(e)))
            self.root.after(0, lambda: self.status_label.config(text="状态：运行错误", foreground="red"))
        finally:
            # 强制清理所有资源
            self.cleanup_resources()
            # 恢复UI状态
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
            if not self.status_label["text"].startswith("状态：已停止"):
                self.root.after(0, lambda: self.status_label.config(text="状态：已断开", foreground="gray"))
    
    def start_forward(self):
        """启动转发"""
        self.forward_thread = threading.Thread(target=self.forward_ssh, daemon=True)
        self.forward_thread.start()
    
    def stop_forward(self):
        """停止转发（强制清理）"""
        self.root.after(0, lambda: self.status_label.config(text="状态：正在停止...", foreground="orange"))
        self.cleanup_resources()
        self.root.after(0, lambda: self.status_label.config(text="状态：已停止", foreground="gray"))
        self.root.after(0, lambda: self.start_btn.config(state="normal"))
        self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
    
    def cleanup_resources(self):
        """强制清理所有资源，释放端口"""
        with self.lock:
            self.is_running = False
        
        # 1. 关闭SSH连接
        try:
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
        except:
            pass
        
        # 2. 关闭监听socket（强制释放端口）
        try:
            if self.forward_server:
                # 发送空连接触发accept退出
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                local_port = int(self.local_port_entry.get().strip())
                s.connect(("127.0.0.1", local_port))
                s.close()
            time.sleep(0.1)
            if self.forward_server:
                self.forward_server.close()
                self.forward_server = None
        except:
            pass
        
        # 3. 释放端口
        try:
            local_port = int(self.local_port_entry.get().strip())
            self.release_port(local_port)
        except:
            pass
    
    def on_exit(self, icon=None, item=None):
        """彻底退出程序"""
        # 停止转发
        if self.is_running:
            self.cleanup_resources()
        # 停止托盘
        if self.tray:
            self.tray.stop()
        # 销毁窗口
        self.root.destroy()

if __name__ == "__main__":
    # 解决tkinter和pystray的线程兼容问题
    import multiprocessing
    multiprocessing.freeze_support()
    
    root = tk.Tk()
    app = OpenClawSSHForwarder(root)
    root.mainloop()