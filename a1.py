# -*- coding: utf-8 -*-

"""
-------------------------------------------------
   File Name：     a1
   Description :   
   Author :       admin
   date：          2022/3/5
-------------------------------------------------
   Change Activity:
                   2022/3/5 22:43: 
-------------------------------------------------
"""
import wx

class Frame(wx.Frame):
    """Frame class that displays an image."""

    def __init__(self, image, parent=None, id=-1,
                 pos=wx.DefaultPosition,
                 title='Hello, wxPython!'):
        """Create a Frame instance and display image."""

        temp = image.ConvertToBitmap()
        size = temp.GetWidth(), temp.GetHeight()
        wx.Frame.__init__(self, parent, id, title, pos, size)
        self.bmp = wx.StaticBitmap(parent=self, bitmap=temp)


class App(wx.App):
    """Application class."""

    def OnInit(self):
        image = wx.Image('pic.png', wx.BITMAP_TYPE_PNG)
        self.frame = Frame(image)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


def main():
    app = App()
    app.MainLoop()


if __name__ == '__main__':
    main()