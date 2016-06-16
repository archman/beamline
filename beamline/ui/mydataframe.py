"""Subclass of DataFrame, which is generated by wxFormBuilder."""

import wx
from . import appui


# Implementing DataFrame
class MyDataFrame(appui.DataFrame):
    def __init__(self, parent, data):
        appui.DataFrame.__init__(self, parent)

        self._show_data(data)

    # Handlers for DataFrame events.
    def copy_btnOnButtonClick(self, event):
        input_text = self.data_rtc.GetValue()
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(input_text))
            wx.TheClipboard.Close()

        dlg = wx.MessageDialog(self,
                               "Copy text to clipboard now, paste everywhere.",
                               "Data Copy Warning",
                               style=wx.ICON_WARNING | wx.OK | wx.CENTER)
        if dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()

    def exit_btnOnButtonClick(self, event):
        self.Close(True)

    def _show_data(self, data):
        self.data_rtc.WriteText(data)
