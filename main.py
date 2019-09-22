#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import webbrowser
import socket
import pyperclip
import requests
import threading
import tkinter.messagebox

from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from ipaddress import ip_address
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from multiprocessing.pool import ThreadPool


class Port():
    def __init__(self, start, end, ports, filter, button, process, treeview):
        socket.setdefaulttimeout(0.5)
        self.start = start.strip()
        self.end = end.strip()
        self.ports = ports.strip()
        self.filter = filter
        self.button = button
        self.process = process
        self.treeview = treeview
        self.thread = 0
        self.timeout = 0
        self.check = []
        self.checkports = []
        self.result = []
        self.all_count = 0
        self.cur_count = 0
        config_json = self.get_config()
        self.thread = config_json[0]["thread"]
        self.timeout = config_json[0]["timeout"]

    def get_config(self):
        config_file = open("./config.txt", "r")
        config_json = json.loads(config_file.read())
        config_file.close()
        return config_json

    def write_config(self):
        config_json = self.get_config()
        config_json[1]["start"] = self.start
        config_json[1]["end"] = self.end
        config_json[1]["ports"] = self.ports
        config_json[1]["filter"] = self.filter
        config_file = open("./config.txt", "w")
        config_file.write(str(config_json).replace("'", '"'))
        config_file.close()

    def clear_tree(self):
        items = self.treeview.get_children()
        for item in items:
            self.treeview.delete(item)

    def get_request(self, host):
        req = requests.get(host, headers={"user-agent": UserAgent().chrome}, timeout=self.timeout)
        req.encoding = requests.utils.get_encodings_from_content(req.text)
        return req

    def get_detail(self, host, port):
        link = "http://" + host + ":" + str(port)
        req = self.get_request(link)
        source = req.text
        status_code = str(req.status_code)
        soup = BeautifulSoup(source, "lxml")
        try:
            title = soup.title.string
        except:
            title = "no title"
        return title, source, status_code

    def get_all_ports(self):
        temp_split = self.ports.split(",")
        for temp in temp_split:
            if "-" in temp:
                start = temp.split("-")[0]
                end = temp.split("-")[1]
                for index in range(int(start), int(end) + 1):
                    self.checkports.append(str(index))
            else:
                self.checkports.append(temp)

    def get_all_host(self):
        start = ip_address(self.start)
        end = ip_address(self.end)
        while start <= end:
            self.check.append(str(start))
            start += 1

    def set_status(self, status):
        self.button["text"] = status

    def get_ip_banner(self, host, port):
        try:
            sock = socket.socket()
            sock.connect((host, int(port)))
            sock.send(b"hi\n")
            answer = sock.recv(1024)
            sock.close()
        except:
            return "no banner"
        return str(answer)

    def print_treeview(self, status_code, host, port, title, banner):
        self.result.append("{}|{}|{}|{}|{}".format(status_code, host, port, title, banner))
        self.treeview.insert("", len(self.result), values=(len(self.result), status_code, host, port, title, banner))

    def get_open_ports(self, host_and_port):
        if self.button["text"] == "Running":
            host = host_and_port.split(":")[0]
            port = host_and_port.split(":")[1]
            try:
                sock = socket.socket(2, 1)
                res = sock.connect_ex((host, int(port)))
                if res == 0:
                    title, source, status_code = self.get_detail(host, port)
                    banner = self.get_ip_banner(host, port)
                    if self.filter:
                        if self.filter in source:
                            self.print_treeview(status_code, host, port, title, banner)
                    else:
                        self.print_treeview(status_code, host, port, title, banner)
                sock.close()
            except:
                pass
        self.cur_count += 1
        sp_1 = "当前程序的进度：  {:.2f}%"
        self.process["text"] = sp_1.format(self.cur_count / self.all_count * 100, str(len(self.result)))

    def exploit_host(self):
        temp_host = []
        for host in self.check:
            for port in self.checkports:
                temp_host.append("{}:{}".format(host, port))
        self.all_count = len(temp_host)
        pool = ThreadPool(processes=self.thread)
        pool.map(self.get_open_ports, temp_host)
        pool.close()
        pool.join()

    def excute(self):
        try:
            self.process["text"] = "当前程序的进度：  00.00%"
            self.button["text"] = "Running"
            self.get_all_ports()
            self.get_all_host()
            self.clear_tree()
            self.all_count = len(self.check)
            self.write_config()
            self.exploit_host()
            self.button["text"] = "Start"
            tkinter.messagebox.showinfo("提示", "程序运行完成!")
        except:
            self.button["text"] = "Start"
            tkinter.messagebox.showerror("错误", "输入框信息填写错误!")


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.window_init()
        self.create_menu()
        self.create_tabs()
        self.create_widgets()
        self.pack(expand=YES, fill=BOTH, padx=10, pady=10)

    def window_init(self):
        self.master.title("PortScan By xyuan0")
        tw, th = self.master.maxsize()
        w, h = int(tw / 2), int(th / 2)
        x, y = int(tw / 4), int(th / 4)
        self.master.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def create_menu(self):
        menu_bar = Menu(self.master)
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="配置", command=self.callback_open_config)
        file_menu.add_command(label="退出", command=sys.exit)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        tools_menu = Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="纯真", command=self.callback_open_chunzhen)
        menu_bar.add_cascade(label="工具", menu=tools_menu)
        self.master.config(menu=menu_bar)

    def callback_open_config(self):
        os.system("notepad ./config.txt")

    def callback_open_chunzhen(self):
        pass

    def create_tabs(self):
        tab_control = ttk.Notebook(self.master)
        self.tab_1 = ttk.Frame(tab_control)
        tab_control.add(self.tab_1, text="第一页")
        tab_control.pack(expand=1, fill="both")

    def create_widgets(self):
        self.create_widgets_1()

    def bind_treeview_port(self, event):
        for item in self.treeview_port.selection():
            item_text = self.treeview_port.item(item, "values")
            rel_link = "http://{}:{}/".format(item_text[2], item_text[3])
            pyperclip.copy(rel_link)
            webbrowser.open(rel_link)
            break

    def get_config(self):
        config_file = open("./config.txt", "r")
        config_json = json.loads(config_file.read())
        config_file.close()
        return config_json

    def create_widgets_1(self):
        config_json = self.get_config()
        frame = ttk.LabelFrame(self.tab_1, text="功能：端口探测机器")
        frame.grid(column=0, row=0, padx=2, pady=8)
        label_startip = ttk.Label(frame, text="请输入起始地址：")
        label_startip.grid(column=0, row=0, sticky="W")
        self.ipt_startip = ttk.Entry(frame, width=15)
        self.ipt_startip.grid(column=1, row=0, sticky="W")
        self.ipt_startip.insert(END, config_json[1]["start"])
        label_endip = ttk.Label(frame, text="请输入结束地址：")
        label_endip.grid(column=0, row=1, sticky="W")
        self.ipt_endip = ttk.Entry(frame, width=15)
        self.ipt_endip.grid(column=1, row=1, sticky="W")
        self.ipt_endip.insert(END, config_json[1]["end"])
        label_ports = ttk.Label(frame, text="请输入扫描端口：")
        label_ports.grid(column=0, row=3, sticky="W")
        self.ipt_ports = ttk.Entry(frame, width=15)
        self.ipt_ports.grid(column=1, row=3, sticky="W")
        self.ipt_ports.insert(END, config_json[1]["ports"])
        label_filter = ttk.Label(frame, text="请输入过滤语句：")
        label_filter.grid(column=0, row=4, sticky="W")
        self.ipt_filter = ttk.Entry(frame, width=15)
        self.ipt_filter.grid(column=1, row=4, sticky="W")
        self.ipt_filter.insert(END, config_json[1]["filter"])
        self.label_process = ttk.Label(frame, text="当前程序的进度：  00.00%")
        self.label_process.grid(column=0, row=5, columnspan=2, sticky="W")
        pil_image = Image.open("./static/images/frame_1.gif")
        image_bg = ImageTk.PhotoImage(image=pil_image)
        self.button_port = Button(frame, text="Start", image=image_bg, width=100, height=185,
                                  command=self.callback_port_scan)
        self.button_port.image = image_bg
        self.button_port.grid(column=0, row=6, columnspan=2, sticky="WE")
        columns = ("#", "状态", "地址", "端口", "标题", "回显")
        self.treeview_port = ttk.Treeview(frame, show="headings", height=15, columns=columns)
        self.treeview_port.column("#", width=30, anchor='w')
        self.treeview_port.column("状态", width=40, anchor='w')
        self.treeview_port.column("地址", width=90, anchor='w')
        self.treeview_port.column("端口", width=50, anchor='w')
        self.treeview_port.column("标题", width=80, anchor='w')
        self.treeview_port.column("回显", width=126, anchor='w')
        self.treeview_port.heading("#", text="#", anchor='w')
        self.treeview_port.heading("状态", text="状态", anchor='w')
        self.treeview_port.heading("地址", text="地址", anchor='w')
        self.treeview_port.heading("端口", text="端口", anchor='w')
        self.treeview_port.heading("标题", text="标题", anchor='w')
        self.treeview_port.heading("回显", text="回显", anchor='w')
        self.treeview_port.bind("<ButtonRelease-1>", self.bind_treeview_port)
        vbar = ttk.Scrollbar(frame, orient=VERTICAL, command=self.treeview_port.yview)
        self.treeview_port.configure(yscrollcommand=vbar.set)
        self.treeview_port.grid(column=3, row=0, rowspan=7, sticky="NW")
        vbar.grid(column=4, row=0, rowspan=7, sticky="NS")
        for child in frame.winfo_children(): child.grid_configure(padx=3, pady=1)

    def use_port_scan(self):
        start = self.ipt_startip.get()
        end = self.ipt_endip.get()
        ports = self.ipt_ports.get()
        filter = self.ipt_filter.get()
        self.class_port = Port(start, end, ports, filter, self.button_port, self.label_process, self.treeview_port)
        self.class_port.excute()

    def callback_port_scan(self):
        if self.button_port["text"] == "Start":
            thread = threading.Thread(target=self.use_port_scan, )
            thread.setDaemon(True)
            thread.start()
        else:
            self.class_port.set_status("Stoping")
            tkinter.messagebox.showinfo("提示", "程序正在停止中,请稍后!")


if __name__ == "__main__":
    # pyinstaller --noconsole --onefile main.py
    app = Application()
    app.mainloop()
