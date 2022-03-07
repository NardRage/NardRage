import threading

import pandas as pd
import pythoncom
from geopy.distance import geodesic
import datetime
import pymysql
import wx
from datetime import datetime
import matplotlib.pyplot as plt  # 引入绘图库
from pandas import DataFrame

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

config = {
    'host': '121.37.144.88',
    'port': 3306,
    'user': 'root',
    'passwd': '202214829dj!',
    'db': 'DJ',
    'charset': 'utf8',

}


# 提取数据
def readdata():
    '''1、用python实现串口通信'''

    '''a、GNSS串口通信'''
    data = GNSS_data()
    '''b、IMU串口通信'''
    # data =IMU_data()
    '''2、用python实现以太网通信'''
    # data =Ethernet()
    return


# GNSS
def judge_status(type):
    if type == 'A':  # 有效
        return True
    else:  # 无效
        return False


def judge_mode(type, wrong):
    if type == wrong:  # 无效
        return False
    else:  # 有效
        return True


def judge_cs(line):
    cs_j = line.split('*')[1].split('[')[0]
    cs = line.split('*')[0].split('$')[1]
    ACII = [ord(i) for i in cs]
    num = ACII[0] ^ ACII[1]
    for i in ACII[2:]:
        num = num ^ i

    if hex(num)[2:] == cs_j:
        return True
    else:
        return False


def judge_type(line, line_list):
    if line_list[0] == '$GNRMC':  # 1
        if judge_status(line_list[2]) != True:
            return False
        # 验证定位模式
        if judge_mode(line_list[12], 'N') != True:
            return False
        # 验证校研和
        if judge_cs(line) != True:
            return False
        return True

    elif line_list[0] == '$GNGGA':  # 2
        # 验证定位模式
        if judge_mode(line_list[6], '0') != True:
            return False
        # 验证校研和
        if judge_cs(line) != True:
            return False
        return True

    elif line_list[0] == '$GNGSA':  # 3
        # 验证定位模式
        if judge_mode(line_list[2], '1') != True:
            return False
        # 验证校研和
        if judge_cs(line) != True:
            return False
        return True

    elif line_list[0] == '$GPGSV':  # 4
        if judge_cs(line) != True:
            return False
        return True

    elif line_list[0] == '$GBGSV':  # 5
        if judge_cs(line) != True:
            return False
        return True


def choose_line(choosedata):
    for i in choosedata:
        if i.split(',')[0] == '$GNRMC':
            if i.split(',')[4] == 'N':
                lat = float(i.split(',')[3][0:2]) + float(i.split(',')[3][2:]) / 60
            else:
                lat = -1 * (float(i.split(',')[3][0:2]) + float(i.split(',')[3][2:]) / 60)
            if i.split(',')[6] == 'E':
                lon = float(i.split(',')[5][0:3]) + float(i.split(',')[5][3:]) / 60
            else:
                lon = -1 * (float(i.split(',')[5][0:3]) + float(i.split(',')[5][3:]) / 60)

            time = datetime.strptime(i.split('[')[1].split(']')[0], '%Y-%m-%d %H:%M:%S.%f')

            return lon, lat, time
        elif i.split(',')[0] == '$GNGGA':
            if i.split(',')[3] == 'N':
                lat = float(i.split(',')[2][0:2]) + float(i.split(',')[2][2:]) / 60
            else:
                lat = -1 * (float(i.split(',')[2][0:2]) + float(i.split(',')[2][2:]) / 60)
            if i.split(',')[5] == 'E':
                lon = float(i.split(',')[4][0:3]) + float(i.split(',')[4][3:]) / 60
            else:
                lon = -1 * (float(i.split(',')[4][0:3]) + float(i.split(',')[4][3:]) / 60)

            time = datetime.strptime(i.split('[')[1].split(']')[0], '%Y-%m-%d %H:%M:%S.%f')

            return lon, lat, time

    return False, False, False


def comput_dis(effective_data, i):
    # 选择有经纬度的行  提取经纬度 时间
    lon1, lat1, time1 = choose_line(effective_data[i])
    lon2, lat2, time2 = choose_line(effective_data[i + 1])

    #  计算距离
    if lon1 != False and lon2 != False:
        dis = geodesic((lat1, lon1), (lat2, lon2)).m
        speed = dis / abs(time2 - time1).total_seconds()
    else:
        return False, False, False
    return dis, speed, time1


def comput_GNSS_speedweiyi(effective_data):
    speed_time = []  # 速度的y值
    weiyi_time = []  # 位移的y值
    time_time = []  # 时间值

    for i, m in enumerate(effective_data[:-1]):
        dis, speed, time = comput_dis(effective_data, i)
        if dis != False:
            speed_time += [speed]
            weiyi_time += [dis]
            time_time += [time]

    return speed_time, weiyi_time, time_time


# global data_RMC, data_GSV, data_GSA, data_GGA


def tiqudata(effective_data):
    data_RMC = []
    data_GSV = []
    data_GSA = []
    data_GGA = []

    for i in effective_data:
        for j in i:
            line = j.split(',')
            # ?
            try:
                if line[0] == '$GNRMC':
                    data_RMC += [[line[0], line[7], line[8],
                                  line[12]]]  # 分别为    标识(label)   地面速率 （spd）    地面航向（cog）  模式(model)

                elif line[0] == '$GPGSV' or line[0] == '$GBGSV':
                    data_GSV += [[line[0], line[3], line[4], line[5], line[6], line[7]]]
                    # 分别为    标识(label)    本系统可见卫星的总数NoSv      第一到第四颗卫星的卫星号sv1_sv4   第一到第四颗卫星的仰角elv1_elv4    第一到第四颗卫星的方位角az1_az4   第一到第四颗卫星的载躁比con1_cno4
                elif line[0] == '$GNGSA':
                    data_GSA += [[line[0], line[3], line[4], line[5], line[6]]]
                    # 分别为    标识(label)    	参与定位的卫星号 sv1_sv12   	位置精度因子PDOP    	水平精度因子HDOP   	垂向精度因子VDOP

                elif line[0] == '$GNGGA':
                    data_GGA += [[line[0], line[7], line[8], line[9], line[11], line[13]]]
                    # 分别为    标识(label)  	参与定位的卫星数量(NoSV)    水平精度因子HDOP	  	椭球高msl    	海平面分离度Altref    	差分校正时延（s） 非差分为空DiffAge
            except:
                continue
    data_RMC = [[' ' if k == '' else k for k in i] for i in data_RMC]
    data_GSV = [[' ' if k == '' else k for k in i] for i in data_GSV]
    data_GSA = [[' ' if k == '' else k for k in i] for i in data_GSA]
    data_GGA = [[' ' if k == '' else k for k in i] for i in data_GGA]

    return data_RMC, data_GSV, data_GSA, data_GGA


def read_GNSS():
    path = './原始数据/GNSS/202108101400-GNSS原始数据.txt'

    effective_data = []
    temp = []  # 临时存放

    # judge_cs('$PDTINFO,*62[')
    with open(path, "r") as f:  # 打开文件
        data = f.readlines()  # 读取文件
        for i in data:
            line = i.strip('\n')
            line_list = line.split('*')[0].split(',')

            if line_list[0] == '$GNRMC':
                if temp != []:
                    effective_data += [temp]
                temp = []
            if judge_type(line, line_list):  # 判断是否有效
                temp += [line]

        # 画图
        # 计算速度位移值  绘图数据
        speed_time, weiyi_time, time = comput_GNSS_speedweiyi(effective_data)  # 画图的

        # 这个地方需要存到mysql中
        # 提取信息
        #   # 存储的
        plt.figure(figsize=(4, 2))
        plt.plot(time, speed_time, '-')
        # plt.show()
        # plt.plot(time, speed_time, '-')
        plt.title('GNSS时间速度图')
        plt.savefig('pic_TS.png')
        # plt.show()
        plt.cla()
        plt.plot(time, weiyi_time, '-')
        plt.title('GNSS时间位移图')
        # plt.show()
        plt.savefig('pic_WS.png')
        # tiqudata(effective_data)

    return effective_data


def GNSS_data():
    path = './原始数据/GNSS/'
    # 数据读取
    data = read_GNSS()

    return


def comput_IMU_speedweiyi(df):
    speed_time = []
    weiyi_time = []
    time = []
    for index, row in df.iterrows():
        # print(index,row,len(df)-1,df.loc[index+1][0])
        if index == len(df) - 1:
            continue
        speed_time += [((float(row[1]) - float(df.loc[index + 1][1])) ** 2 + (
                float(row[2]) - float(df.loc[index + 1][2])) ** 2 + (
                                float(row[3]) - float(df.loc[index + 1][3])) ** 2) ** 0.5 * \
                       abs(row[0] - df.loc[index + 1][0]).total_seconds()
                       ]
        weiyi_time += [((float(row[1]) - float(df.loc[index + 1][1])) ** 2 + (
                float(row[2]) - float(df.loc[index + 1][2])) ** 2 + (
                                float(row[3]) - float(df.loc[index + 1][3])) ** 2) ** 0.5 * \
                       (abs(row[0] - df.loc[index + 1][0]).total_seconds()) ** 2
                       ]
        time += [row[0]]

    return speed_time, weiyi_time, time


def read_IMU():
    path = './原始数据\IMU/202108101400-IMU原始数据.txt'

    effective_data = []
    temp = []  # 临时存放

    # judge_cs('$PDTINFO,*62[')
    with open(path, "r") as f:  # 打开文件
        data = f.readlines()  # 读取文件
        num = 0
        for i in data:
            num += 1
            if num > 2:
                # print(i)
                line = i.split()
                # print(line)
                effective_data += [
                    [datetime.strptime(line[1], '%H:%M:%S.%f'), line[2], line[3], line[4], line[8], line[9], line[10]]]
                # 分别是  Time(s)   ax(g)	ay(g)	az(g)      	AngleX(deg)	AngleY(deg)	AngleZ(deg)
        # 数据清洗
        dp = DataFrame(effective_data)
        #  去除缺失值
        dp = dp.dropna()
        #  去重复值
        dp = dp.drop_duplicates()
        # b, a = signal.butter(8, 0.8, 'lowpass')  # 配置滤波器 8 表示滤波器的阶数
        # filtedData = signal.filtfilt(b, a, dp)
        # print(dp)
        # 计算速度位移值  绘图数据
        speed_time, weiyi_time, time = comput_IMU_speedweiyi(dp)

        # 画图
        plt.plot(time, speed_time, '-')
        plt.title('IMU时间速度图')
        plt.show()
        plt.plot(time, weiyi_time, '-')
        plt.title('IMU速传时间位移图')
        plt.show()

    return


def comput_Ethernet_speedweiyi(df):
    speed_time = []
    weiyi_time = []
    time = []
    time_0 = 0
    for index, row in df.iterrows():
        if index == len(df) - 1:
            continue
        speed_time = [float(row[0]) - float(df.loc[index + 1][0]) * 10 / 1000]
        weiyi_time = [float(row[0]) - float(df.loc[index + 1][0]) * (10 / 1000) ** 2]
        time_0 += 10
        time += [time_0]

    return speed_time, weiyi_time, time


def read_Ethernet():
    path = './原始数据\速传Data/chazhi-2022-03-05 17_48_50_910.txt'

    effective_data = []
    temp = []  # 临时存放

    # judge_cs('$PDTINFO,*62[')
    with open(path, "r") as f:  # 打开文件
        data = f.readlines()  # 读取文件
        num = 0
        for i in data:
            num += 1
            if num > 1:
                # print(i)
                line = i.split()
                # print(line)
                effective_data += [
                    [line[0], line[1], line[2], line[3]]]
                # 分别是  速传的速度值、第二列是雷达的速度值、第三列是这两个速度的插值，第四列是差值百分比
    # 数据清洗
    dp = DataFrame(effective_data)
    #  去除缺失值
    dp = dp.dropna()
    #  去重复值
    dp = dp.drop_duplicates()
    # 计算速度位移值  绘图数据
    speed_time, weiyi_time, time = comput_Ethernet_speedweiyi(dp)  # 计算速传的速度和位移

    plt.plot(time, speed_time, '-')
    plt.title('速传时间速度图')
    plt.show()
    plt.plot(time, weiyi_time, '-')
    plt.title('速传时间位移图')
    plt.show()
    return dp



def IMU_data():
    data = read_IMU()

    return


def comput_leida_speedweiyi(df):
    speed_time = []
    weiyi_time = []
    time = []
    time_0 = 0
    for index, row in df.iterrows():
        if index == len(df) - 1:
            continue
        # print(row)
        try:
            speed_time += [float(row[1]) - float(df.loc[index + 1][1]) * 10 / 1000]
            weiyi_time += [float(row[1]) - float(df.loc[index + 1][1]) * (10 / 1000) ** 2]
            time_0 += 10
            time += [time_0]

        except:
            continue

    return speed_time, weiyi_time, time


def leida_data():
    path = './原始数据\速传Data/chazhi-2022-03-05 17_48_50_910.txt'

    effective_data = []
    temp = []  # 临时存放

    # judge_cs('$PDTINFO,*62[')
    with open(path, "r") as f:  # 打开文件
        data = f.readlines()  # 读取文件
        num = 0
        for i in data:
            num += 1
            if num > 1:
                # print(i)
                line = i.split()
                # print(line)
                effective_data += [
                    [line[0], line[1], line[2], line[3]]]
                # 分别是  速传的速度值、第二列是雷达的速度值、第三列是这两个速度的插值，第四列是差值百分比
    # 数据清洗
    dp = DataFrame(effective_data)
    #  去除缺失值
    dp = dp.dropna()
    #  去重复值
    dp = dp.drop_duplicates()
    # 计算速度位移值  绘图数据
    speed_time, weiyi_time, time = comput_leida_speedweiyi(dp)  # 计算速传的速度和位移
    plt.figure(figsize=(4, 2))
    plt.plot(time, speed_time, '-')
    plt.title('雷达时间速度图')
    plt.savefig('pic_leida1.png')
    plt.cla()
    # plt.show()
    plt.plot(time, weiyi_time, '-')
    plt.title('雷达时间位移图')
    plt.savefig('pic_leida2.png')
    # plt.show()
    return


#  数据预处理模块
def data_preprocessing():
    return


# 界面
def interface():
    return


def main():
    '''一、提取数据'''
    readdata()

    '''二、数据预处理模块'''
    data_preprocessing()

    '''三、存储和显示模块'''
    interface()  # 界面


def to_MySQL_ngss():
    effective_data = read_GNSS()
    MySQL_conn = pymysql.connect(**config)
    data_RMC, data_GSV, data_GSA, data_GGA = tiqudata(effective_data)

    cursor_RMC = MySQL_conn.cursor()
    for value in data_RMC:
        sql_list = [str(value[0]), str(value[1]), str(value[2]), str(value[3])]

        sql = 'insert into ngss_GNRMC (label,spd,cog,model) value (%s,%s,%s,%s)'
        cursor_RMC.execute(sql, (sql_list[0], sql_list[1], sql_list[2], sql_list[3]))
    MySQL_conn.commit()
    print('ok')

    cursor_GSV = MySQL_conn.cursor()
    for value in data_GSV:
        sql_list = [str(value[0]), str(value[1]), str(value[2]), str(value[3]), str(value[4]), str(value[5])]
        sql = 'insert into ngss_GPGSV (lable, NoSv, sv1_sv4, elv1_elv4, `az1~az4`, con1_cno4) value (%s,%s,%s,%s,%s,%s)'
        cursor_RMC.execute(sql, (sql_list[0], sql_list[1], sql_list[2], sql_list[3], sql_list[4], sql_list[5]))
    MySQL_conn.commit()
    print('ok2')
    cursor_GGA = MySQL_conn.cursor()
    for value in data_GGA:
        sql_list = [str(value[0]), str(value[1]), str(value[2]), str(value[3]), str(value[4]), str(value[5]),
                    str(value[6])]
        sql = 'insert into ngss_GNGGA (lable, NoSV, HDOP, msl, Altref, s, DiffAge) value (%s,%s,%s,%s,%s,%s,%s)'
        cursor_RMC.execute(sql,
                           (sql_list[0], sql_list[1], sql_list[2], sql_list[3], sql_list[4], sql_list[5], sql_list[6]))

    print('ok3')
    MySQL_conn.commit()
    cursor_GSA = MySQL_conn.cursor()
    for value in data_GSA:
        sql_list = [str(value[0]), str(value[1]), str(value[2]), str(value[3])]
        sql = 'insert into ngss_GNGSA (lable, sv1_sv12, PDOP, VDOP) value (%s,%s,%s,%s)'
        cursor_RMC.execute(sql, (sql_list[0], sql_list[1], sql_list[2], sql_list[3]))
    print('ok4')
    MySQL_conn.commit()
    cursor_RMC.close()
    cursor_GSA.close()
    cursor_GGA.close()
    cursor_GSV.close()


class Thread_gnss(wx.Frame, threading.Thread):
    def __init__(self, window):
        pythoncom.CoInitialize()
        threading.Thread.__init__(self)
        self.window = window  # 继承窗口类

    def run(self):
        # gauae = 0
        # wx.CallAfter(self.window.Setvalue, gauae)  # 更新进度条
        # to_MySQL_ngss()
        read_GNSS()
        MySQL_conn = pymysql.connect(**config)
        cursor_RMC = MySQL_conn.cursor()
        cursor_RMC.execute('select * from ngss_GNRMC')
        cursor_RMC.execute('select * from ngss_GNGSA')
        cursor_RMC.execute('select * from ngss_GNGGA')
        cursor_RMC.execute('select * from ngss_GPGSV')
        values = cursor_RMC.fetchall()
        for value in values:
            msg = str(value) + '\n'
            wx.CallAfter(self.window.LogMessage, msg)
        cursor_RMC.close()
        MySQL_conn.close()


# if __name__ == '__main__':
#     main()
class Thread_main_imu(wx.Frame, threading.Thread):
    def __init__(self, window):
        pythoncom.CoInitialize()
        threading.Thread.__init__(self)
        self.window = window  # 继承窗口类

    def run(self):
        # to_MySQL()
        read_IMU()
        MySQL_conn = pymysql.connect(**config)
        cursor_RMC = MySQL_conn.cursor()
        cursor_RMC.execute('select * from IMU')
        values = cursor_RMC.fetchall()
        for value in values:
            msg = str(value) + '\n'
            wx.CallAfter(self.window.LogMessage, msg)
        cursor_RMC.close()
        MySQL_conn.close()

        # gauae = 0
        # wx.CallAfter(self.window.Setvalue, gauae)  # 更新进度条


class Thread_main_eth(wx.Frame, threading.Thread):
    def __init__(self, window):
        pythoncom.CoInitialize()
        threading.Thread.__init__(self)
        self.window = window  # 继承窗口类

    def run(self):
        read_Ethernet()

        MySQL_conn = pymysql.connect(**config)
        cursor_RMC = MySQL_conn.cursor()
        cursor_RMC.execute('select * from Ethernet')
        values = cursor_RMC.fetchall()
        for value in values:
            msg = str(value) + '\n'
            wx.CallAfter(self.window.LogMessage, msg)
        cursor_RMC.close()
        MySQL_conn.close()


class Thread_main_leida(wx.Frame, threading.Thread):
    def __init__(self, window):
        pythoncom.CoInitialize()
        threading.Thread.__init__(self)
        self.window = window  # 继承窗口类

    def run(self):
        # to_MySQL()
        leida_data()
        MySQL_conn = pymysql.connect(**config)
        cursor_RMC = MySQL_conn.cursor()
        cursor_RMC.execute('select * from leida')
        values = cursor_RMC.fetchall()
        for value in values:
            msg = str(value) + '\n'
            wx.CallAfter(self.window.LogMessage, msg)
        cursor_RMC.close()
        MySQL_conn.close()
