# -*- coding: utf-8 -*-

"""
@author: NerdRage
@mail: dengj@nysoftland.com.cn
@software: PyCharm
@file: main_2021_10_27.py
@time: 2021/12/1 10:12
"""

import os
import time

import wx
import threading
import pythoncom

from 人机交互 import Thread_gnss





class Windows(wx.Frame, wx.App):  # 程序主窗口
    def __init__(self, panel):
        wx.Frame.__init__(self, panel, title='GNSS串口通信', size=(1100, 800), style=wx.DEFAULT_FRAME_STYLE)
        self.InitUI()
        self.threads = []
        self.panel = panel

    def InitUI(self):
        self.icon = wx.Icon(name="image/img.png", type=wx.BITMAP_TYPE_PNG)
        self.SetIcon(self.icon)
        self.panel = wx.Panel(self)

        # 主窗口
        self.log = wx.TextCtrl(self.panel, -1, "", pos=(20, 20), size=(800, 400), style=wx.TE_RICH | wx.TE_MULTILINE)

        self.Text1 = wx.StaticText(self.panel, -1, '串口选择:', pos=(830, 20), style=wx.ALIGN_RIGHT)
        self.combox1 = wx.ComboBox(self.panel, -1, value='COM1O:USB-SERIAL', choices=[''], pos=(830, 40),
                                   size=(190, 20))

        self.Text2 = wx.StaticText(self.panel, -1, '波特率:', pos=(830, 70), style=wx.ALIGN_RIGHT)
        self.combox2 = wx.ComboBox(self.panel, -1, value='115200', choices=[''], pos=(890, 70), size=(130, 20))

        self.Text3 = wx.StaticText(self.panel, -1, '停止位:', pos=(830, 110), style=wx.ALIGN_RIGHT)
        self.combox3 = wx.ComboBox(self.panel, -1, value='1', choices=['2', '3'], pos=(890, 110), size=(130, 20))

        self.Text4 = wx.StaticText(self.panel, -1, '数据位:', pos=(830, 150), style=wx.ALIGN_RIGHT)
        self.combox4 = wx.ComboBox(self.panel, -1, value='8', choices=['1', '2', '4'], pos=(890, 150), size=(130, 20))

        self.Text5 = wx.StaticText(self.panel, -1, '奇偶校验:', pos=(830, 190), style=wx.ALIGN_RIGHT)
        self.combox5 = wx.ComboBox(self.panel, -1, value='有', choices=['无'], pos=(890, 190), size=(130, 20))

        self.Text6 = wx.StaticText(self.panel, -1, '串口操作:', pos=(830, 220), style=wx.ALIGN_RIGHT)

        self.Button = wx.Button(self.panel, -1, '◎ 打开串口', pos=(890, 220), size=(130, 20))
        # self.Bind(wx.EVT_BUTTON, self.Mysql, self.Button)

        self.saveButton0 = wx.Button(self.panel, -1, '保存窗口', pos=(830, 250), size=(90, 20))
        self.deleteButton1 = wx.Button(self.panel, -1, '清除接收', pos=(940, 250), size=(90, 20))

        self.checkbox1 = wx.CheckBox(self.panel, id=-1, label=u'16进制显示', pos=(830, 270), size=(110, 18))
        self.checkbox2 = wx.CheckBox(self.panel, id=-1, label=u'白底黑字', pos=(940, 270), size=(110, 18))
        self.checkbox3 = wx.CheckBox(self.panel, id=-1, label=u'RTS', pos=(830, 290), size=(110, 18))
        self.checkbox4 = wx.CheckBox(self.panel, id=-1, label=u'DTR', pos=(940, 290), size=(110, 18))
        self.checkbox5 = wx.CheckBox(self.panel, id=-1, label=u'时间戳（以换行回车断帧）', pos=(830, 310), size=(180, 18))

        # 下半部分
        self.main2 = wx.TextCtrl(self.panel, -1, "", pos=(20, 450), size=(900, 200), style=wx.TE_RICH | wx.TE_MULTILINE)

        self.sendButton0 = wx.Button(self.panel, -1, '绘制曲线_ngss', pos=(940, 450), size=(120, 40))
        self.Bind(wx.EVT_BUTTON, self.startThreads, self.sendButton0)

        self.delete_sendButton1 = wx.Button(self.panel, -1, '绘制曲线_IMU', pos=(940, 520), size=(120, 40))
        # self.Bind(wx.EVT_BUTTON, self.startThreads1, self.sendButton0)
        self.delete_sendButton2 = wx.Button(self.panel, -1, '绘制曲线_IMU', pos=(940, 520), size=(120, 40))
        # self.Bind(wx.EVT_BUTTON, self.startThreads2, self.sendButton0)
        self.delete_sendButton3 = wx.Button(self.panel, -1, '绘制曲线_IMU', pos=(940, 520), size=(120, 40))
        # self.Bind(wx.EVT_BUTTON, self.startThreads3, self.sendButton0)

        self.checkbox6 = wx.CheckBox(self.panel, id=-1, label=u'定时发送', pos=(20, 670), size=(80, 18))
        self.checkbox7 = wx.CheckBox(self.panel, id=-1, label=u'16进制发送', pos=(20, 690), size=(110, 18))
        self.checkbox8 = wx.CheckBox(self.panel, id=-1, label=u'发送新行', pos=(110, 690), size=(180, 18))

        self.Text7 = wx.StaticText(self.panel, -1, '周期:', pos=(110, 670), style=wx.ALIGN_RIGHT)
        self.zhouqi = wx.TextCtrl(self.panel, -1, "1000", pos=(140, 670), size=(60, 20),
                                  style=wx.TE_RICH | wx.TE_MULTILINE)
        self.Text8 = wx.StaticText(self.panel, -1, 'ms', pos=(200, 670), style=wx.ALIGN_RIGHT)

        # 进度条
        self.gauge = wx.Gauge(self.panel, wx.ID_ANY, pos=(250, 670), size=(400, 20), style=wx.GA_HORIZONTAL)

        self.open_file = wx.Button(self.panel, -1, '打开文件', pos=(650, 670), size=(120, 40))
        self.send_file = wx.Button(self.panel, -1, '发送文件', pos=(780, 670), size=(120, 40))
        self.stop_send = wx.Button(self.panel, -1, '停止发送', pos=(910, 670), size=(120, 40))

    def startThreads(self, event):  # 从池中删除线程

        thread = Thread_gnss(window=self)
        thread.start()
        time.sleep(1)
        # img = wx.Image('pic.png',wx.BITMAP_TYPE_PNG).Rescale(900,200).ConvertToBitmap()
        # self.bmp1 = wx.StaticBitmap(self.panel, -1, img)  #转化为wx.StaticBitmap()形式   pos(20, 450)
        # self.bmp1.SetBitmap(self.panel,-1,pos = (20, 450))
        # main()
        image_speed = wx.Image('pic_TS.png', wx.BITMAP_TYPE_PNG)
        temp_speed = image_speed.ConvertToBitmap()
        self.pic1 = wx.StaticBitmap(parent=self, id=1, bitmap=temp_speed, pos=(20, 450),
                                    size=(450, 200), style=0, )

        #
        image_weiyi = wx.Image('pic_WS.png', wx.BITMAP_TYPE_PNG)
        temp = image_weiyi.ConvertToBitmap()
        self.pic2 = wx.StaticBitmap(parent=self, id=1, bitmap=temp, pos=(470, 450),
                                    size=(450, 200), style=0, )

    # def startThreads1(self,event):
    #     t
    #
    # def Mysql(self,event):
    #     thread = Thread_main_mysql(window=self)
    #     thread.start()

    def StopThreads(self):  # 从池中删除线程
        while self.threads:
            thread = self.threads[0]
            thread.stop()
            self.threads.remove(thread)

    def LogMessage(self, msg):
        self.log.AppendText(msg)  # 更新实时扫描信息

    def Setvalue(self, gauge):
        self.gauge.SetValue(gauge)


if __name__ == '__main__':
    app = wx.App()
    Frame = Windows(panel=None)
    Frame.Show()
    app.MainLoop()
