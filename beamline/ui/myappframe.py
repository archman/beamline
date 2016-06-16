"""Subclass of MainFrame, which is generated by wxFormBuilder."""
# -*- coding: utf-8 -*-

import wx
import json
import time

from . import appui
from . import mylogframe
from . import mydataframe
from . import mychoiceframe

import felapps
from .. import lattice

MAXNROW = 65536  # max row number


# Implementing MyFrame
class MyAppFrame(appui.MainFrame):
    def __init__(self, parent, title):
        appui.MainFrame.__init__(self, parent)
        self.has_tree = False  # initial tree list stat, does not exist is False
        self.open_filename = None  # filename to open and read, also save filename
        self.saveas_filename = None  # saveas filename
        self.data = {}  # valid keys: 'lte', 'dict', 'json'
        self.log = [
        ]  # log list, item is a dict, k:v -> 'stat':stat, 'logstr':log
        self.tree_refresh_flag = None  # tree refresh flag
        self.data_refresh_flag = None  # data refresh flag
        self.path_as_title_flag = None  # show file path on title?
        self.title = title
        self.SetTitle(title)
        self.use_beamline = None  # choosed beamline keyword
        self.all_beamlines = None  # all beamline keywords could choose
        self.beamlines_dict = None  # dict element k:v -> beamline_name : list of elements
        self.lattice_instance = None  # lattice instance generated by lattice.Lattice class

        self.expand_all_flag = True  # expand all tree flag

        # update methods dict
        self._update_stat = {'open': self._update_open,
                             'save as': self._update_saveas,
                             'list tree': self._update_listtree, }

        # nodeview listctrl
        self.nodeview_lc.InsertColumn(0, "Value", wx.LIST_FORMAT_LEFT)
        self.nodeview_lc.InsertColumn(1, "Parameter", wx.LIST_FORMAT_LEFT)
        self.nodeview_lc.SetTextColour('#4A4A4A')
        self.nodeview_lc.SetColumnWidth(0, 200)
        self.nodeview_lc.SetColumnWidth(1, 200)

        self.idx = 0

        # search ctrl
        self.all_children = []
        self.found_items = []

    # Handlers for MyFrame events.
    def show_btnOnButtonClick(self, event):
        if self.open_filename is None:
            dlg = wx.MessageDialog(self,
                                   "File is not loaded, open now?",
                                   "File Loading Warning",
                                   style=wx.ICON_WARNING | wx.YES | wx.NO |
                                   wx.CENTER)
            if dlg.ShowModal() == wx.ID_YES:
                open_filename = self.open_file()
                if self.get_refresh_flag(open_filename):
                    self.has_tree = self.show_tree(self.has_tree)
            else:
                return
        elif not self.has_tree or self.tree_refresh_flag:
            self.has_tree = self.show_tree(self.has_tree)

    def generate_btnOnButtonClick(self, event):
        while self.open_filename is None:
            dlg = wx.MessageDialog(self,
                                   "Open valid data file first.",
                                   "Data Generation Warning",
                                   style=wx.ICON_WARNING | wx.YES_NO |
                                   wx.CENTER)
            if dlg.ShowModal() == wx.ID_YES:
                self.open_filename = self.open_file()
            else:
                return

        if self.data_refresh_flag:
            fn = self.open_filename
            if self.get_filetype(fn).lower() == 'json':
                data_json, data_lte = self.json2lte(fn)
                data_dict = self.read_json(fn)
            elif self.get_filetype(fn).lower() == 'lte':
                data_json, data_lte = self.lte2json(fn)
                data_dict = self.read_lte(fn)
            self.data['json'] = data_json
            self.data['lte'] = data_lte
            self.data['dict'] = data_dict
            self.data_refresh_flag = False
        else:
            return

    def exit_btnOnButtonClick(self, event):
        self.exit_app()

    def clear_btnOnButtonClick(self, event):
        self.has_tree = self.clear_tree()

    def treename_tcOnTextEnter(self, event):
        value = event.GetEventObject().GetValue()
        if value.isspace() or value == '':
            dlg = wx.MessageDialog(self,
                                   "Rootname should be non space.",
                                   "Input Warning",
                                   style=wx.ICON_INFORMATION | wx.OK |
                                   wx.CENTER)
            if dlg.ShowModal() == wx.ID_OK:
                event.GetEventObject().SetValue('GreatTree')

    def quit_mitemOnMenuSelection(self, event):
        self.exit_app()

    def about_mitemOnMenuSelection(self, event):
        try:
            from wx.lib.wordwrap import wordwrap
            info = wx.AboutDialogInfo()
            info.Name = "Lattice Viewer"
            info.Version = "0.1.0"
            info.Copyright = "(C) 2016 Tong Zhang, SINAP, CAS"
            info.Description = wordwrap(
                "This is application is created for showing the lattice elements "
                "and configurations in tree style.", 350, wx.ClientDC(self))
            info.Developers = ["Tong Zhang <zhangtong@sinap.ac.cn>", ]
            lt = "Lattice Viewer is free software; you can redistribute it " \
               + "and/or modify it under the terms of the GNU General Public " \
               + "License as published by the Free Software Foundation; " \
               + "either version 3 of the License, or (at your option) any "  \
               + "later version.\n"  \
               + "\nLattice Viewer is distributed in the hope that it will be " \
               + "useful, but WITHOUT ANY WARRANTY; without even the implied " \
               + "warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR " \
               + "PURPOSE. See the GNU General Public License for more details.\n"  \
               + "\nYou should have received a copy of the GNU General Public License " \
               + "along with Lattice Viewer; if not, write to the Free Software " \
               + "Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA"
            info.License = wordwrap(lt, 500, wx.ClientDC(self))
            wx.AboutBox(info)
        except:
            dial = wx.MessageDialog(self,
                                    "Cannot show about informaion, sorry!",
                                    "Unknown Error",
                                    style=wx.OK | wx.CANCEL | wx.ICON_ERROR |
                                    wx.CENTRE)
            if dial.ShowModal() == wx.ID_OK:
                dial.Destroy()

    def mainview_treeOnLeftDown(self, event):
        pt = event.GetPosition()
        item, flags = self.mainview_tree.HitTest(pt)
        if item and self.mainview_tree.ItemHasChildren(item):
            #child, cookie = self.mainview_tree.GetFirstChild(item)
            #child_list = []
            #while child.IsOk():
            #    child_list.append(child)
            #    child, cookie = self.mainview_tree.GetNextChild(item, cookie)
            self.show_data(item)
        event.Skip()

    def showlog_btnOnButtonClick(self, event):
        self.log_frame = mylogframe.MyLogFrame(self, self.log)
        self.log_frame.SetTitle('Log View')
        self.log_frame.Show()

    def open_mitemOnMenuSelection(self, event):
        newfilename = self.open_file()
        if self.get_refresh_flag(newfilename):
            self.has_tree = self.show_tree(self.has_tree)

    def saveas_mitemOnMenuSelection(self, event):
        self.saveas_filename = self.saveas_file()
    
    def search_ctrlOnCancelButton(self, event):
        self.search_ctrl.SetValue('')

    def search_ctrlOnText(self, event):
        mt = self.mainview_tree
        s_text = event.GetString().lower()

        all_children = self.all_children
        all_text = [mt.GetItemText(i).lower() for i in all_children]

        found_items = [child for i, child in enumerate(all_children)
                       if s_text in all_text[i]]
        self.found_items = found_items
        self.search_show_id = 0

        if found_items != []:
            item_to_sel = found_items[self.search_show_id]
            mt.ScrollTo(item_to_sel)
            mt.SelectItem(item_to_sel)
            self.show_data(item_to_sel)

    def search_ctrlOnTextEnter(self, event):
        if self.found_items == []:
            return

        mt = self.mainview_tree
        self.search_show_id += 1
        try:
            item_to_sel = self.found_items[self.search_show_id]
            mt.ScrollTo(item_to_sel)
            mt.SelectItem(item_to_sel)
            self.show_data(item_to_sel)
        except IndexError:
            self.search_show_id = 0
            item_to_sel = self.found_items[self.search_show_id]
            mt.ScrollTo(item_to_sel)
            mt.SelectItem(item_to_sel)
            self.show_data(item_to_sel)

    def next_bmpbtnOnButtonClick(self, event):
        mt = self.mainview_tree
        try:
            self.search_show_id += 1
            item_to_sel = self.found_items[self.search_show_id]
            mt.ScrollTo(item_to_sel)
            mt.SelectItem(item_to_sel)
            self.show_data(item_to_sel)
        except:
            pass

    def previous_bmpbtnOnButtonClick(self, event):
        mt = self.mainview_tree
        try:
            self.search_show_id -= 1
            item_to_sel = self.found_items[self.search_show_id]
            mt.ScrollTo(item_to_sel)
            mt.SelectItem(item_to_sel)
            self.show_data(item_to_sel)
        except:
            pass

    def nodeview_lcOnListColRightClick(self, event):
        print event.GetColumn()
        item = self.nodeview_lc.GetColumn(event.GetColumn())
        print item
        #obj.SetTextColour('RED')

    def nodeview_lcOnListItemSelected(self, event):
        self.idx = event.Index

    def nodeview_lcOnRightUp(self, event):
        x, y = event.GetX(), event.GetY()
        item, flags = self.nodeview_lc.HitTest((x, y))

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.nodeview_lc.Select(item)

        if not hasattr(self, 'popid1'):
            self.popid1 = wx.NewId()
            self.popid2 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.onPopOne, id=self.popid1)
            self.Bind(wx.EVT_MENU, self.onPopTwo, id=self.popid2)

        menu = wx.Menu()
        menu.Append(self.popid1, "Highlight")
        menu.Append(self.popid2, "Edit")
        self.PopupMenu(menu)
        menu.Destroy()

    def onPopOne(self, event):
        idx = self.idx
        item = self.nodeview_lc.GetItem(idx)
        item.SetTextColour('RED')
        font = item.GetFont()
        font.SetWeight(wx.BOLD)
        item.SetFont(font)
        self.nodeview_lc.SetItemBackgroundColour(idx, 'YELLOW')
        self.nodeview_lc.SetItem(item)
        #col1_text = item.Text
        #col2_text = self.nodeview_lc.GetItemText(idx, 1)
        #print("{0:<2d} {1:<10s} {2:<10s}".format(idx, col1_text, col2_text))

    def onPopTwo(self, event):
        self.nodeview_lc.EditLabel(self.idx)

    def reopen_mitemOnMenuSelection(self, event):
        if self.open_filename is not None:
            self.has_tree = self.show_tree(self.has_tree, force_update=True)

    def lte_mitemOnMenuSelection(self, event):
        if self.data_refresh_flag:
            dlg = wx.MessageDialog(self,
                                   "Data changed, push 'Generate' to refresh.",
                                   "Data Refresh Warning",
                                   style=wx.ICON_WARNING | wx.OK | wx.CENTER)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.Destroy()
                return

        if self.data.has_key('lte'):
            content_to_show = self.data['lte']
        else:
            content_to_show = "!DATA NOT GENERATED, PUSH GENERATE BUTTON FIRST!"
        self.view_lte_frame = mydataframe.MyDataFrame(self, content_to_show)
        self.view_lte_frame.SetTitle('String View')
        self.view_lte_frame.Show()

    def raw_mitemOnMenuSelection(self, event):
        if self.data_refresh_flag:
            dlg = wx.MessageDialog(self,
                                   "Data changed, push 'Generate' to refresh.",
                                   "Data Refresh Warning",
                                   style=wx.ICON_WARNING | wx.OK | wx.CENTER)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.Destroy()
                return

        if self.data.has_key('json'):
            content_to_show = self.data['json']
        else:
            content_to_show = "!DATA NOT GENERATED, PUSH GENERATE BUTTON FIRST!"
        self.view_raw_frame = mydataframe.MyDataFrame(self, content_to_show)
        self.view_raw_frame.SetTitle('String View')
        self.view_raw_frame.Show()

    def dict_mitemOnMenuSelection(self, event):
        if self.data_refresh_flag:
            dlg = wx.MessageDialog(self,
                                   "Data changed, push 'Generate' to refresh.",
                                   "Data Refresh Warning",
                                   style=wx.ICON_WARNING | wx.OK | wx.CENTER)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.Destroy()
                return

        if self.data.has_key('dict'):
            content_to_show = str(self.data['dict'])
        else:
            content_to_show = "!DATA NOT GENERATED, PUSH GENERATE BUTTON FIRST!"
        self.view_dict_frame = mydataframe.MyDataFrame(self, content_to_show)
        self.view_dict_frame.SetTitle('Dict View')
        self.view_dict_frame.Show()

    def bl_mitemOnMenuSelection(self, event):
        if self.data_refresh_flag:
            dlg = wx.MessageDialog(self,
                                   "Data changed, push 'Generate' to refresh.",
                                   "Data Refresh Warning",
                                   style=wx.ICON_WARNING | wx.OK | wx.CENTER)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.Destroy()
                return

        bl_info_dict = self.get_beamlines()
        self.bl_choice_frame = mychoiceframe.MyChoiceFrame(self, bl_info_dict)
        self.bl_choice_frame.SetTitle('Choose Beamline')
        self.bl_choice_frame.Show()

    def expand_mitemOnMenuSelection(self, event):
        self.expand_all_flag = True
        self.mainview_tree.ExpandAll()

    def collapse_mitemOnMenuSelection(self, event):
        self.expand_all_flag = False
        self.mainview_tree.CollapseAll()

    def pt_mitemOnMenuSelection(self, event):
        obj = self.pt_mitem
        self.path_as_title_flag = obj.IsChecked()
        if self.path_as_title_flag:
            self.set_title()
        else:
            self.SetTitle(self.title)

    # user-defined methods
    def set_title(self):
        if self.path_as_title_flag and self.open_filename is not None:
            self.SetTitle(self.open_filename)

    def saveas_file(self):
        fullfilename = felapps.funutils.getFileToSave(self,
                                                      ext=['json', 'lte'])
        if fullfilename is None:
            self.update_stat('save as', fullfilename, 'ERR')
            return
        else:
            ext = self.get_file_ext(fullfilename)
            if ext == 'json':
                if not self.data.has_key('json') or self.data_refresh_flag:
                    dlg = wx.MessageDialog(
                        self,
                        "Push 'Generate' button to generate data.",
                        "Data Save As Warning",
                        style=wx.ICON_WARNING | wx.OK | wx.CENTER)
                    if dlg.ShowModal() == wx.ID_OK:
                        dlg.Destroy()
                    else:
                        return
                else:
                    f = open(fullfilename, 'w')
                    f.write(self.data['json'])
                    f.close()
            elif ext == 'lte':
                if not self.data.has_key('lte') or self.data_refresh_flag:
                    dlg = wx.MessageDialog(
                        self,
                        "Push 'Generate' button to generate data.",
                        "Data Save As Warning",
                        style=wx.ICON_WARNING | wx.OK | wx.CENTER)
                    if dlg.ShowModal() == wx.ID_OK:
                        dlg.Destroy()
                    else:
                        return
                else:
                    f = open(fullfilename, 'w')
                    f.write(self.data['lte'])
                    f.close()
            self.update_stat('save as', fullfilename, 'OK')
            return fullfilename

    def open_file(self):
        fullfilename = felapps.funutils.getFileToLoad(self,
                                                      ext=['json', 'lte'])
        if fullfilename is None:
            self.update_stat('open', fullfilename, 'ERR')
            return
        else:
            self.update_stat('open', fullfilename, 'OK')
            return fullfilename

    def clear_tree(self):
        """ return has_tree stat
        """
        if not self.mainview_tree.IsEmpty():
            self.mainview_tree.DeleteAllItems()
        return False

    def show_tree(self, has_tree=False, force_update=False):
        """ show tree list
        :param has_tree: tree exist or not, False by default, 
            if True, tree should be cleared first
        :param force_update: force update flag, if True, update neglect other flags.
        return has_tree, True successful, not change when exception
        """
        if has_tree:
            self.has_tree = self.clear_tree()

        if force_update:
            self.data_refresh_flag = True

        try:
            if self.data_refresh_flag:
                fn = self.open_filename
                if self.get_filetype(fn).lower() == 'json':
                    data_dict = self.read_json(fn)
                elif self.get_filetype(fn).lower() == 'lte':
                    data_dict = self.read_lte(fn)
            else:
                data_dict = self.data['dict']

            tree_name = self.treename_tc.GetValue()
            tree_root = self.mainview_tree.AddRoot(tree_name)
            self.add_items(data_dict,
                           root=tree_root,
                           target=self.mainview_tree)
            self.expand_tree(self.expand_all_flag)
            self.update_stat('list tree', 'Listing tree succeed', 'OK')
            self.tree_refresh_flag = False
            self.set_title()
            self.all_children = self.get_children(tree_root,
                                                  self.mainview_tree)
            return True
        except:
            self.update_stat('list tree', 'Listing tree failed', 'ERR')
            return self.has_tree

    def expand_tree(self, expand_all_flag):
        if expand_all_flag:
            self.mainview_tree.ExpandAll()
        else:
            self.mainview_tree.CollapseAll()

    def add_items(self, data_dict, root=None, target=None):
        """ add items for tree
            :param data_dict: dict of tree data
            :param root: treeitemid of tree root
            :param target: treectrl obj
        """
        if root is None:
            print("Warning: TreeCtrl root must be given.")
            return
        if target is None:
            print("Warning: TreeCtrl target must be given.")
            return
        for k in sorted(data_dict):
            if isinstance(data_dict[k], dict):
                k_item_root = target.AppendItem(root, k)
                self.add_items(data_dict[k], k_item_root, target)
            else:
                item_val = ' : '.join((k, str(data_dict[k])))
                target.AppendItem(root, item_val)

    def exit_app(self):
        dlg = wx.MessageDialog(self,
                               "Do you want to exit this application?",
                               "Exit Warning",
                               style=wx.ICON_INFORMATION | wx.YES_NO |
                               wx.CENTER)
        if dlg.ShowModal() == wx.ID_YES:
            self.Close(True)

    def show_data(self, item):
        """ show data key-value in ListCtrl for tree item
        """
        child, cookie = self.mainview_tree.GetFirstChild(item)
        child_list = []
        while child.IsOk():
            child_list.append(child)
            child, cookie = self.mainview_tree.GetNextChild(item, cookie)

        lc = self.nodeview_lc
        lc.DeleteAllItems()
        for i, child in enumerate(child_list):
            text = self.mainview_tree.GetItemText(child)
            try:
                k, v = [s.strip() for s in text.split(':')]
            except ValueError:
                k, v = s, '...'
            idx = lc.InsertStringItem(MAXNROW, v)
            lc.SetStringItem(idx, 1, k)

    def get_filetype(self, filename):
        """ return file type according to extension
        """
        if filename is not None:
            return filename.split('.')[-1]

    def read_json(self, filename):
        """ return dict the first line of json file, 
            which defined by filename
        """
        return json.loads(open(filename, 'r').read().strip())

    def read_lte(self, filename):
        """ parse lte file first, then return dict as read_json() does
        """
        lpins = lattice.LteParser(filename)
        return json.loads(lpins.file2json())

    def json2lte(self, filename):
        """ convert json to lte

            return tuple of json, lte file content
        """
        data_json = open(filename, 'r').read().strip()
        latins = lattice.Lattice(data_json)

        self.lattice_instance = latins
        self.all_beamlines = latins.getAllBl()
        if self.use_beamline is None:
            self.use_beamline = 'bl' if 'bl' in self.all_beamlines else self.all_beamlines[
                0]
        bl_ele_list = [latins.getFullBeamline(k, True)
                       for k in self.all_beamlines]
        self.beamlines_dict = dict(zip(self.all_beamlines, bl_ele_list))

        data_lte = latins.generateLatticeFile(self.use_beamline, 'sio')
        return data_json, data_lte

    def lte2json(self, filename):
        """ convert lte to json

            return tuple of json, lte file content
        """
        lpins = lattice.LteParser(filename)
        data_json = lpins.file2json()

        latins = lattice.Lattice(lpins.file2json())
        self.latins = latins
        self.all_beamlines = latins.getAllBl()
        if self.use_beamline is None:
            self.use_beamline = 'bl' if 'bl' in self.all_beamlines else self.all_beamlines[
                0]
        bl_ele_list = [latins.getFullBeamline(k, True)
                       for k in self.all_beamlines]
        self.beamlines_dict = dict(zip(self.all_beamlines, bl_ele_list))

        data_lte = open(filename, 'r').read()
        return data_json, data_lte

    def update_stat(self, mode='open', infostr='', stat=''):
        """ write operation stats to log
        :param mode: 'open', 'saveas', 'listtree'
        :param infostr: string to put into info_st
        :param stat: 'OK' or 'ERR'
        """
        self._update_stat[mode](mode, infostr, stat)

    def _update_open(self, mode, infostr, stat):
        self._file_stat(mode, infostr, stat)

    def _update_saveas(self, mode, infostr, stat):
        self._file_stat(mode, infostr, stat)

    def _update_listtree(self, mode, infostr, stat):
        self._tree_stat(mode, infostr, stat)

    def _tree_stat(self, mode, infostr, stat):
        """ update stat regarding to tree generating process,
            e.g. show_tree()
        """
        action_str = mode.upper()
        info_str = infostr
        if stat == 'OK':
            self.action_st_panel.SetBackgroundColour('#00FF00')
        else:  # ERR
            self.action_st_panel.SetBackgroundColour('#FF0000')
        self.action_st.SetLabel(action_str)
        if info_str is None:
            pass
        child_cnt_0 = self.mainview_tree.GetChildrenCount(
            self.mainview_tree.GetRootItem(),
            recursively=False)
        child_cnt_1 = self.mainview_tree.GetChildrenCount(
            self.mainview_tree.GetRootItem(),
            recursively=True)
        self.info_st.SetLabel("{0} ({1} elements.)".format(info_str,
                                                           child_cnt_0))
        if self.info_st.IsEllipsized():
            self.info_st.SetToolTip(wx.ToolTip(info_str))

        self.log.append({'stat': stat,
                         'logstr':
                         "[{ts}] {acts:<10s} : {infs} ({cnt1}|{cnt2})".format(
                             ts=time.strftime("%Y/%m/%d-%H:%M:%S",
                                              time.localtime()),
                             acts=action_str,
                             infs=info_str,
                             cnt1=child_cnt_0,
                             cnt2=child_cnt_1), })

    def _file_stat(self, mode, infostr, stat):
        """ update stat regarding to file operation, 
            e.g. open, save, saveas, etc.
        """
        action_str = mode.upper()
        info_str = infostr

        if stat == 'OK':
            self.action_st_panel.SetBackgroundColour('#00FF00')
        else:  # ERR
            self.action_st_panel.SetBackgroundColour('#FF0000')
        self.action_st.SetLabel(action_str)
        if info_str is None:
            info_str = 'Undefined File'
        self.info_st.SetLabel(info_str)
        if self.info_st.IsEllipsized():
            self.info_st.SetToolTip(wx.ToolTip(info_str))

        self.log.append({'stat': stat,
                         'logstr':
                         "[{ts}] {acts:<10s} : {infs}".format(ts=time.strftime(
                             "%Y/%m/%d-%H:%M:%S", time.localtime()),
                                                              acts=action_str,
                                                              infs=info_str)})

    def get_refresh_flag(self, filename):
        """ set refresh data flag
            return True or False
        """
        if filename is not None and filename != self.open_filename:
            self.open_filename = filename
            self.tree_refresh_flag = True
            self.data_refresh_flag = True
            return True
        else:
            return False

    def get_beamlines(self):
        """ return dict with k:v,
            k: 'beamline name'
            v: beamline elements list regarding to 'beamline name'
        """
        return self.beamlines_dict

    def get_file_ext(self, filename):
        """ return file extension, e.g. file.json, return json
        """
        return filename.split('.')[-1]

    def get_children(self, root=None, target=None):
        """ return list of all the children of root of given tree
            :param root: treectrl item, treeitemid
            :param target: treectrl object
        """
        if root is None:
            print("Warning: TreeCtrl root/child must be given.")
            return None
        if target is None:
            print("Warning: TreeCtrl target must be given.")
            return None
        child, cookie = target.GetFirstChild(root)
        child_list = []
        while child.IsOk():
            if target.ItemHasChildren(child):
                child_list.extend(self.get_children(child, target))
            child_list.append(child)
            child, cookie = target.GetNextChild(root, cookie)
        return child_list
