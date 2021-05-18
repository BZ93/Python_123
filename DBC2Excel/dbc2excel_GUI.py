#!/usr/bin/env python
import wx
import dbc2excel as d2e


class MyFrame(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600, 500))
        self.path = ''
        #self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        #self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        ##excel生成条件变量
        self.if_sig_desc = True
        self.if_sig_val_desc = True
        self.val_description_max_number = 70
        self.if_start_val = True
        self.if_recv_send = True
        self.if_asc_sort = True

        #静态文字
        self.quote = wx.StaticText(self, label="\n", pos=(420, 260))
        #控制台窗口
        self.logger = wx.TextCtrl(self, pos=(5, 300), size=(580, 130), style=wx.TE_MULTILINE | wx.TE_READONLY)

        # A button
        self.button =wx.Button(self, label="Excel Generation", pos=(10, 150),size=(200,100))
        self.Bind(wx.EVT_BUTTON, self.create_excel,self.button)
        # B button
        b = wx.Button(self,-1,u"Load *.dbc File",pos=(10, 20),size=(200,100))
        self.Bind(wx.EVT_BUTTON, self.select_file_button, b)
        # c button 增加图片
        #pic = wx.Image("./source/a.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        #c = wx.BitmapButton(self,-1,pic,pos=(250, 20),size=(290,150))
        #self.Bind(wx.EVT_BUTTON, self.select_file_button, b)

        #增加复选框
        #panel = wx.Panel(self)  # 创建画板，控件容器
        #信号描述
        HEIGHT = 25
        OFFSET = 20
        k = 1
        self.check1 = wx.CheckBox(self, -1, 'Signal Description', pos=(250, HEIGHT), size=(150, -1))
        self.Bind(wx.EVT_CHECKBOX, self.SigDescEvtCheckBox, self.check1)
        self.check1.Set3StateValue(True)

        self.check2 = wx.CheckBox(self, -1, 'Value Description', pos=(250, HEIGHT + k * OFFSET), size=(150, -1))
        self.Bind(wx.EVT_CHECKBOX, self.SigValDescEvtCheckBox, self.check2)
        self.check2.Set3StateValue(True)
        k += 1
        #最大信号值描述长度

        self.check3 = wx.CheckBox(self, -1, 'Initial Value', pos=(250, HEIGHT + k * OFFSET), size=(150, -1))
        self.Bind(wx.EVT_CHECKBOX, self.StartValEvtCheckBox, self.check3)
        self.check3.Set3StateValue(True)
        k += 1
        self.check4 = wx.CheckBox(self, -1, 'Transmitter and Receiver', pos=(250, HEIGHT + k * OFFSET), size=(200, -1))
        self.Bind(wx.EVT_CHECKBOX, self.RecvSndEvtCheckBox, self.check4)
        self.check4.Set3StateValue(True)
        k += 1
        self.check5 = wx.CheckBox(self, -1, 'Ascending (Uncheck for Decending)', pos=(250, HEIGHT + k * OFFSET), size=(250, -1))
        self.Bind(wx.EVT_CHECKBOX, self.SortEvtCheckBox, self.check5)
        self.check5.Set3StateValue(True)
        k += 1
        self.quote = wx.StaticText(self, label="Max Length of Value Description \n", pos=(250, HEIGHT + k * OFFSET), size = (220, 20))
        self.text1 = wx.TextCtrl(self, wx.ID_ANY, "70",pos=(480, HEIGHT + k * OFFSET), size=(50, 20), style=wx.TE_LEFT)
        #print(self.text1.Value)
        k += 1
        # Setting up the menu.
        filemenu = wx.Menu()
        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        # wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&关于"," Information about this program")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&文件") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        # Set events.
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.logger.AppendText("***Try uncheck above options if the conversion takes too long.***\nNothing can prevent system engineers from going forward!\n")

        self.Show(True)




    #响应事件
    def SigDescEvtCheckBox(self,event):
        self.if_sig_desc = not self.if_sig_desc
        #print(self.if_sig_desc)

    def SigValDescEvtCheckBox(self,event):
        self.if_sig_val_desc = not self.if_sig_val_desc
        #print(self.if_sig_val_desc)

    def StartValEvtCheckBox(self,event):
        self.if_start_val = not self.if_start_val
        #print(self.if_start_val)

    def RecvSndEvtCheckBox(self,event):
        self.if_recv_send = not self.if_recv_send
        #print(self.if_recv_send)
    def SortEvtCheckBox(self,event):
        self.if_asc_sort = not  self.if_asc_sort

    def OnAbout(self, e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "DBC2Excel Tool --- AS28", "关于", wx.OK)
        dlg.ShowModal()  # Show it
        dlg.Destroy()  # finally destroy it when finished.

    def OnExit(self, e):
        self.Close(True)  # Close the frame.

    def create_excel(self, event):
        self.logger.AppendText(" \nDBC file loaded successfully\n" )
        dbc = d2e.DbcLoad(self.path)
        self.logger.AppendText(" Generating Excel！Please wait... \n")
        if(str(self.text1.Value).isdigit()):
            self.val_description_max_number = int(self.text1.Value)
            #print(self.val_description_max_number)
        dbc.dbc2excel(self.path,self.if_sig_desc,self.if_sig_val_desc,self.val_description_max_number,self.if_start_val,self.if_recv_send,self.if_asc_sort)
        self.logger.AppendText(" Conversion is done successfully!\n")

    def select_file_button(self, event):
        filesFilter = "Dicom (*.dbc)|*.dbc|" "All files (*.*)|*.*"
        fileDialog = wx.FileDialog(self, message="Select a file", wildcard=filesFilter, style=wx.FD_OPEN)
        dialogResult = fileDialog.ShowModal()
        if dialogResult != wx.ID_OK:
            return
        self.path = fileDialog.GetPath()
        self.logger.SetLabel('>>>Loaded file：'+self.path)
    def OnEraseBack(self,event):
        dc = event.GetDC()
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        bmp = wx.Bitmap("a.jpg")
        dc.DrawBitmap(bmp, 0, 0)

    #################
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame(None, 'DBC2Excel Tool')
    app.MainLoop()
