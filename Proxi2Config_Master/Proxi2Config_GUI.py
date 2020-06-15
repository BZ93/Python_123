import wx

#wxpython GUI图形化编程 https://www.cnblogs.com/morries123/p/8568666.html
class mainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600,400))
        #控制台文本显示窗口 wxPython控件学习之wx.TextCtrl https://www.cnblogs.com/ankier/archive/2012/09/17/2689364.html
        self.logger_input = wx.TextCtrl(self, pos=(3, 5), size=(420, 60), style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        self.logger_output = wx.TextCtrl(self, pos=(3, 67), size=(577, 290), style=wx.TE_MULTILINE | wx.TE_READONLY)
        #定义文件选择按钮，并绑定选择文件事件
        button = wx.Button(self, -1, "Decode PROXI", pos=(426, 5), size=(154,60))
        button.Bind(wx.EVT_BUTTON, self.decode_proxi_button)

    def decode_proxi_button(self, event):
        value = '0x' + str(self.logger_input.GetValue()).replace(' ', ',0x')
        #以数字 0 作为十进制整数的开头，就会报 SyntaxError 异常 SyntaxError: leading zeros in decimal integer literals are not permitted

        try:
        #Engine Variant
            engine_type_b = str(bin(eval(value)[68])).replace('0b','').rjust(8, '0')[0:4] # rjust()用法 https://www.runoob.com/python/att-string-rjust.html
            engine_type = int(eval('0b' + engine_type_b)) 
            engine_type_list = ['0 = Invalid', '1 = Not used', '2 = Not used','3 = 1.4L Mair 140cv/170cv (1.4L I4 MULTIAIR TURBO ENGINE)','4 = Not used',
                             '5 = 1.6L Fam B 120cv (1.6L I4 B ECO TURBO DIESEL ENG )','6 = 2.0L Fam B TD VGT 140cv/170cv (2.0L I4 TURBO DIESEL ENGINE)',
                             '7 = 2.4L Tiger Shark 187cv (2.4L I4 MULTIAIR ENGINE)','8 = Not used','9 = Not used','10 = Not used (226&521 1.8 ETorque 140hp)',
                             '11 = Not used (226&521 do not use)','12 = 2.0L TS 163 cv (2.0L DUAL VVT E100 ENGINE)',
                             '13 = 1.3L GSET4 130cv/150cv/180cv/180cv flex/190cv eAWD/225cv eAWD/240cv eAWD (1.3L I4 TURBO MAIR DI or TURBO PHEV ENGINE)',
                             '14 = 2.0L GMET4 252cv (2.0L I4 DOHC DI TURBO ENGINE)','15 = 1.5L GSET4 130hp (1.5L I4 DOHC TURBO MHEV ENGINE)']
            self.logger_output.AppendText('>>>Car_Configuration_3(Byte_66) Engine_Type_Variant is \n' + '   ' + engine_type_list[engine_type] +'\n')
        #Final Ratio
            final_ratio_b = str(bin(eval(value)[96])).replace('0b','').rjust(8, '0')[-5:-1]
            final_ratio = int(eval('0b' + final_ratio_b))
            self.logger_output.AppendText('>>>Powertrain_Configuration_3(Byte_94)Final_Ratio is \n' + '   ' + str(final_ratio) +'\n')
        #Gear Box Type Variant
            gear_box_b = str(bin(eval(value)[102])).replace('0b','').rjust(8, '0')[0:-3]
            gear_box = int(eval('0b' + gear_box_b))
            gear_box_list = ['0 = Invalid', '1 = AISIN', '2 = C635 MTX (C630 for M4)', '3 = DDCT 725','4 = 948 TE', '5 = DDCT6']
            self.logger_output.AppendText('>>>Chassis_Configuration_3(Byte_100)Gear_Box_Type_Variant is \n' + '   ' + gear_box_list[gear_box] +'\n')
        except:
            self.logger_output.AppendText('>>>Input is incorrect, please check and re-input! \n')

if __name__ == '__main__':
    app = wx.App()
    frame = mainFrame(None, 'Proxi2Config')
    frame.Show()
    app.MainLoop()
