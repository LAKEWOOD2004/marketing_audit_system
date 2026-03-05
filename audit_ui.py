# -*- coding: utf-8 -*-
"""
营销审计系统操作界面

使用方法：
1. 双击运行此脚本
2. 选择政策文件和配置文件
3. 点击开始审计按钮
4. 查看生成的报告
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import webbrowser
from pathlib import Path

class AuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("营销审计多智能体系统")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        self.policy_file = ""
        self.config_file = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        # 标题
        title_frame = tk.Frame(self.root, bg="#4472C4")
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(title_frame, text="营销审计多智能体系统", font=("微软雅黑", 16, "bold"), fg="white", bg="#4472C4")
        title_label.pack(pady=10)
        
        # 主内容
        content_frame = tk.Frame(self.root, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 政策文件选择
        policy_frame = tk.Frame(content_frame)
        policy_frame.pack(fill=tk.X, pady=10)
        
        policy_label = tk.Label(policy_frame, text="政策文件：", font=("微软雅黑", 10))
        policy_label.pack(side=tk.LEFT, padx=10)
        
        self.policy_entry = tk.Entry(policy_frame, width=40, font=("微软雅黑", 10))
        self.policy_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        
        policy_btn = tk.Button(policy_frame, text="选择", command=self.select_policy_file, 
                             bg="#4472C4", fg="white", font=("微软雅黑", 9))
        policy_btn.pack(side=tk.LEFT, padx=10)
        
        # 配置文件选择
        config_frame = tk.Frame(content_frame)
        config_frame.pack(fill=tk.X, pady=10)
        
        config_label = tk.Label(config_frame, text="配置文件：", font=("微软雅黑", 10))
        config_label.pack(side=tk.LEFT, padx=10)
        
        self.config_entry = tk.Entry(config_frame, width=40, font=("微软雅黑", 10))
        self.config_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        
        config_btn = tk.Button(config_frame, text="选择", command=self.select_config_file, 
                             bg="#4472C4", fg="white", font=("微软雅黑", 9))
        config_btn.pack(side=tk.LEFT, padx=10)
        
        # 操作按钮
        button_frame = tk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        audit_btn = tk.Button(button_frame, text="开始审计", command=self.start_audit, 
                            bg="#548235", fg="white", font=("微软雅黑", 12, "bold"), 
                            width=15, height=2)
        audit_btn.pack(side=tk.LEFT, padx=20)
        
        demo_btn = tk.Button(button_frame, text="运行演示", command=self.run_demo, 
                            bg="#0070C0", fg="white", font=("微软雅黑", 12, "bold"), 
                            width=15, height=2)
        demo_btn.pack(side=tk.LEFT, padx=20)
        
        open_output_btn = tk.Button(button_frame, text="查看报告", command=self.open_output_folder, 
                                bg="#7030A0", fg="white", font=("微软雅黑", 12, "bold"), 
                                width=15, height=2)
        open_output_btn.pack(side=tk.LEFT, padx=20)
        
        # 状态显示
        status_frame = tk.Frame(content_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(status_frame, text="就绪", font=("微软雅黑", 10), fg="#333")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 底部信息
        info_frame = tk.Frame(self.root, bg="#f0f0f0")
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        info_label = tk.Label(info_frame, text="版本：1.0.0 | 基于智谱AI GLM-4", font=("微软雅黑", 9), fg="#666", bg="#f0f0f0")
        info_label.pack(pady=5)
    
    def select_policy_file(self):
        filetypes = [
            ("Word文档", "*.docx"),
            ("Word旧版", "*.doc"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        file_path = filedialog.askopenfilename(
            title="选择政策文件",
            filetypes=filetypes,
            initialdir=str(Path(__file__).parent / "data" / "input")
        )
        if file_path:
            self.policy_file = file_path
            self.policy_entry.delete(0, tk.END)
            self.policy_entry.insert(0, file_path)
    
    def select_config_file(self):
        filetypes = [
            ("Excel文件", "*.xlsx"),
            ("Excel旧版", "*.xls"),
            ("CSV文件", "*.csv"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=filetypes,
            initialdir=str(Path(__file__).parent / "data" / "input")
        )
        if file_path:
            self.config_file = file_path
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, file_path)
    
    def start_audit(self):
        if not self.policy_file:
            messagebox.showerror("错误", "请选择政策文件")
            return
        if not self.config_file:
            messagebox.showerror("错误", "请选择配置文件")
            return
        
        self.status_label.config(text="正在审计...", fg="#0070C0")
        self.root.update()
        
        try:
            main_script = str(Path(__file__).parent / "main.py")
            cmd = [
                sys.executable,
                main_script,
                "--policy", self.policy_file,
                "--config", self.config_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))
            
            if result.returncode == 0:
                self.status_label.config(text="审计完成！", fg="#548235")
                messagebox.showinfo("成功", "审计完成！请查看报告文件夹")
                self.open_output_folder()
            else:
                error_msg = result.stderr or "审计失败"
                self.status_label.config(text="审计失败", fg="#FF0000")
                messagebox.showerror("错误", f"审计失败：\n{error_msg[:200]}")
                
        except Exception as e:
            self.status_label.config(text="运行错误", fg="#FF0000")
            messagebox.showerror("错误", f"运行错误：\n{str(e)}")
    
    def run_demo(self):
        self.status_label.config(text="运行演示...", fg="#0070C0")
        self.root.update()
        
        try:
            main_script = str(Path(__file__).parent / "main.py")
            cmd = [
                sys.executable,
                main_script,
                "--demo"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))
            
            if result.returncode == 0:
                self.status_label.config(text="演示完成！", fg="#548235")
                messagebox.showinfo("成功", "演示完成！请查看报告文件夹")
                self.open_output_folder()
            else:
                error_msg = result.stderr or "演示失败"
                self.status_label.config(text="演示失败", fg="#FF0000")
                messagebox.showerror("错误", f"演示失败：\n{error_msg[:200]}")
                
        except Exception as e:
            self.status_label.config(text="运行错误", fg="#FF0000")
            messagebox.showerror("错误", f"运行错误：\n{str(e)}")
    
    def open_output_folder(self):
        output_folder = str(Path(__file__).parent / "data" / "output")
        if os.path.exists(output_folder):
            webbrowser.open(output_folder)
        else:
            messagebox.showinfo("提示", "报告文件夹不存在，请先运行审计")

def main():
    root = tk.Tk()
    app = AuditApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
