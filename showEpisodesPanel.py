#!/usr/bin/env python
# -*- coding: utf-8 *-*

import wx
import sys
import subprocess
import os
import threading
import rssParser
from utilDb import UtilDb
import utilWeb
import ctypes

class ShowEpisodesPanel(wx.Panel):

    sepSeasons = False
    episodes = []
    seasonColls = {}

    notebook = None

    # another callback
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def __init__(self, ui, parentPanel, parentSizer, showParams):
        wx.Panel.__init__(self, parentPanel, -1)

        self.ui = ui
        self.parentPanel = parentPanel
        self.parentSizer = parentSizer

        self.panelSz = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.panelSz)

        self.showParams = showParams
        if showParams["seasons"] > 1:
            self.sepSeasons = True

    def on_change(self, event):
        self.GetParent().Layout()

    def addEpisodes(self, episodes):
		for e in episodes:
			self.addButton(e)

    #@modified ana.castro Issue #2
    def addButton(self, episode):
        return self.addEpisodePanel(episode, self, self.panelSz)

    #@modified ana.castro Issue #2
    def addEpisodePanel(self, episode, parentPanel, parentSizer):
        if (self.ui.isConf("hide_unmonitored", "ON") and episode[5] == 0):
            return
        if (self.ui.isConf("hide_viewed", "ON") and episode['viewed'] != 0):
            return

        episodesPanel = parentPanel
        episodesSizer = parentSizer

        # whether to use collapsible panes
        if self.sepSeasons:
            if self.seasonColls.get(episode['season']) == None:
                title = "%s (S%d)" % (episode['show'],episode['season'])
                collpane = wx.CollapsiblePane(parentPanel, wx.ID_ANY,
                       title)
                parentSizer.Add(collpane, 0, wx.GROW | wx.ALL, 5)
                win = collpane.GetPane()
                paneSz = wx.BoxSizer(wx.VERTICAL)
                win.SetSizer(paneSz)
                paneSz.SetSizeHints(win)
                collpane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_change)
                self.seasonColls[episode['season']] = [collpane, win, paneSz]
            # get panel and sizer
            episodesPanel = self.seasonColls.get(episode['season'])[1]
            episodesSizer = self.seasonColls.get(episode['season'])[2]

        #adiciona um botao rapido..
        boxShow = wx.BoxSizer(wx.HORIZONTAL)
        button3 = wx.ToggleButton(episodesPanel, -1, episode['show'] + " S" +
        str(episode['season']) + "E" + str(episode['episode']))
        boxShow.Add(button3, 0, wx.ALL, 1)
        if (episode['viewed'] == 1):
            button3.SetValue(True)
        else:
            button3.SetValue(False)
        #self.button3.connect("toggled", self.callbackEpisode, episode)
        button3.Bind(wx.EVT_LEFT_DOWN,
                lambda evt: self.ui.callbackEpisode(button3, episode))
        #self.button3.connect("enter", self.callbackEpisodeInfo, episode)
        button3.Bind(wx.EVT_ENTER_WINDOW,
                lambda evt: self.ui.callbackEpisodeInfo(button3, episode))
        buttonPlay = wx.Button(episodesPanel, -1, "Play")#gtk.Button("Play")
        buttonPlay.Bind(wx.EVT_BUTTON,
                lambda evt: self.ui.callbackPlay(None, episode['file']))
        boxShow.Add(buttonPlay, 0, wx.ALL, 1)
        episodesSizer.Add(boxShow, 0, wx.ALL, 1)
        #w, h = self.ui.lPSizer.GetMinSize()
        #episodesPanel.SetVirtualSize((w, h))
        

        if len(self.seasonColls) == 1 and self.seasonColls.get(episode['season']) != None:
            self.seasonColls.get(episode['season'])[0].Collapse()
            self.seasonColls.get(episode['season'])[0].Expand()
            w, h = episodesSizer.GetMinSize()
            episodesPanel.SetVirtualSize((w, h))
        w, h = self.ui.lPSizer.GetMinSize()
        self.parentPanel.SetVirtualSize((w, h))

    def clearEpisodes(self):
        for box in self.episodes:
            box.hide()
        for box in self.shows:
            box.hide()
        for box in self.showCovers:
            self.coversBox.remove(box)
        self.box1.DeleteWindows()
        self.boxShows.DeleteWindows()
        self.listPanel.Layout()
        self.episodes = []
        self.shows = []
        self.showCovers = []
        self.tX = self.tY = 0

    # show button right click callback: displays context menu
    def cb_showButtonRClick(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            #make widget popup
            widget.popup(None, None, None, event.button, event.time)
            pass

    def menuitem_response(self, widget):
        print 'not implemented'

    def addShow(self, show):
        if (show['monitored'] != 1 and self.isConf("hide_unmonitored_shows", "ON")):
            return
        boxShow = wx.BoxSizer(wx.HORIZONTAL)
        btnMonitored = wx.ToggleButton(self.listPanel, -1, show['show'])
        btnMonitored.SetValue(show['monitored'] == 1)
        btnMonitored.Bind(wx.EVT_TOGGLEBUTTON,
                lambda evt: self.callbackShow(btnMonitored, show))
        btnFetching = wx.ToggleButton(self.listPanel, -1, "Fetching")
        btnFetching.SetValue(show['fetching'] == 1)
        btnFetching.Bind(wx.EVT_TOGGLEBUTTON,
                lambda evt: self.callbackShow(btnFetching, show))

        boxShow.Add(btnMonitored)
        boxShow.Add(btnFetching)
        self.boxShows.Add(boxShow)
        self.listPanel.Layout()
        return

        #menu
        menu = gtk.Menu()
        menu_item = gtk.MenuItem("Quarantine show")
        menu.append(menu_item)
        menu_item.connect("activate", self.menuitem_response)
        menu_item.show()
        menu_item2 = gtk.CheckMenuItem("Fetching")
        if (show['fetching'] == 1):
            menu_item2.set_active(True)
        else:
            menu_item2.set_active(False)
        menu.append(menu_item2)
        menu_item2.connect("activate", self.callbackShow, show)
        menu_item2.show()
        # show button context menu
        self.btnMonitored.connect_object("event", self.cb_showButtonRClick, menu)

        # Remove Show button
        btnRemoveShow = gtk.Button("X")
        btnRemoveShow.connect("clicked", self.callbackShowRemove, show)
        btnRemoveShow.show()
        #self.boxShow.pack_start(btnRemoveShow, True, True, 0)

        if not (show['cover']):
            return
        if not (show['hasCover']):
            return
        image = gtk.Image()
        #image.set_from_file(show[2])
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file(show['cover'])
            scaled_buf = pixbuf.scale_simple(100,100,gtk.gdk.INTERP_BILINEAR)
            image.set_from_pixbuf(scaled_buf)
            image.show()
        except Exception:
            pass
        aspect_frame = gtk.AspectFrame(show['show'], # label
            0.5, # center x
            0.5, # center y
            1.5, # xsize/ysize = 2
            False) # ignore child's aspect

        aspect_frame.show()
        self.showCovers.append(aspect_frame)
        self.coversBox.attach(aspect_frame, self.tX, self.tX+1, self.tY,self.tY+1)

        aspect_frame.add(image)
        #image.connect('expose-event', self.on_image_resize, aspect_frame, pixbuf)

        self.tX += 1
        if (self.tX == 4):
            self.tX = 0
            self.tY += 1

    # currently unused
    def on_image_resize(self, widget, event, window, pixbuf):
        allocation = widget.get_allocation()
        #if self.temp_height != allocation.height or self.temp_width != allocation.width:
        #    self.temp_height = allocation.height
        #    self.temp_width = allocation.width
        #    pixbuf = pixbuf.scale_simple(allocation.width, allocation.height, gtk.gdk.INTERP_BILINEAR)
        #        widget.set_from_pixbuf(pixbuf)

    def getConfigFrame(self):
        confs = UtilDb().getConfs()
        self.configFrame = wx.Panel(self.notebook)#gtk.Frame("Config Frame")
        sizer = wx.BoxSizer(wx.VERTICAL)#wx.GridBagSizer(hgap=5, vgap=5)
        self.configFrame.SetSizer(sizer)
        #label = gtk.Label("Config")

        self.btn_hide_unmonitored_shows = wx.CheckBox(self.configFrame, -1, "Hide unmonitored shows", (10, 10))
        self.btn_hide_unmonitored_shows.SetValue(self.isConf("hide_unmonitored", "ON"))
        #self.btn_hide_unmonitored.connect("toggled", self.callbackBtn, "hide_unmonitored")
        self.btn_hide_unmonitored_shows.Bind(wx.EVT_CHECKBOX,
                lambda evt: self.callbackBtn(self.btn_hide_unmonitored_shows, "hide_unmonitored_shows"))
        sizer.Add(self.btn_hide_unmonitored_shows, 0, wx.ALL, 10)

        self.btn_hide_unmonitored = wx.CheckBox(self.configFrame, -1, "Hide unmonitored shows' episodes", (10, 10))
        self.btn_hide_unmonitored.SetValue(self.isConf("hide_unmonitored", "ON"))
        #self.btn_hide_unmonitored.connect("toggled", self.callbackBtn, "hide_unmonitored")
        self.btn_hide_unmonitored.Bind(wx.EVT_CHECKBOX,
                lambda evt: self.callbackBtn(self.btn_hide_unmonitored, "hide_unmonitored"))
        sizer.Add(self.btn_hide_unmonitored, 0, wx.ALL, 10)

        self.btn_hide_viewed = wx.CheckBox(self.configFrame, -1, "Hide viewed episodes", (10, 10))
        self.btn_hide_viewed.SetValue(self.isConf("hide_viewed", "ON"))
        #self.btn_hide_viewed.connect("toggled", self.callbackBtn, "hide_viewed")
        self.btn_hide_viewed.Bind(wx.EVT_CHECKBOX,
                lambda evt: self.callbackBtn(self.btn_hide_viewed, "hide_viewed"))
        sizer.Add(self.btn_hide_viewed, 0, wx.ALL, 10)

        btn_show_frame = wx.CheckBox(self.configFrame, -1, "Display Show frame", (10, 10))
        btn_show_frame.SetValue(self.isConf("display_show_frame", "ON"))
        btn_show_frame.Bind(wx.EVT_CHECKBOX,
                lambda evt: self.callbackBtn(btn_show_frame, "display_show_frame"))
        sizer.Add(btn_show_frame, 0, wx.ALL, 10)

        leftColSize = 160
        boxCPath = wx.BoxSizer(wx.HORIZONTAL)
        txt_content_path = wx.TextCtrl(self.configFrame, size=(300,30))#gtk.Entry()
        if self.getConf("content_path"):
            txt_content_path.SetValue(self.getConf("content_path"))
        #self.txt_content_path.connect("key-press-event", self.callbackEntry, "content_path")
        txt_content_path.Bind(wx.EVT_KEY_DOWN,
                lambda evt: self.callbackEntry(txt_content_path, evt, "content_path"))
        boxCPath.Add(wx.StaticText(self.configFrame, size=(leftColSize,15), label="Content Path:"), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 1)
        boxCPath.Add(txt_content_path, 0, wx.ALL, 1)
        sizer.Add(boxCPath, 0, wx.ALL, 10)

        boxBtCP = wx.BoxSizer(wx.HORIZONTAL)
        txt_btclient_path = wx.TextCtrl(self.configFrame, size=(200,30))
        if self.getConf("btorrent_client_path"):
            txt_btclient_path.SetValue(self.getConf("btorrent_client_path"))
        txt_btclient_path.Bind(wx.EVT_KEY_DOWN,
                lambda evt: self.callbackEntry(txt_btclient_path, evt, "btorrent_client_path"))
        boxBtCP.Add(wx.StaticText(self.configFrame, size=(leftColSize,15), label="BitTorrent Client Path:"), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 1)
        boxBtCP.Add(txt_btclient_path, 0, wx.ALL, 1)
        sizer.Add(boxBtCP, 0, wx.ALL, 10)

        #sw = gtk.ScrolledWindow()
        #sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.txt_log = wx.TextCtrl(self.configFrame, size=(400,300), style=wx.TE_MULTILINE | wx.TE_READONLY)#gtk.TextView()
        #self.txt_log.set_cursor_visible(False)
        #sw.add(self.txt_log)
        #sw.show()
        #self.configBox.attach(sw, 0, 1, 4, 6)
        sizer.Add(self.txt_log, 0, wx.ALL, 10)
        self.txt_log.Show()
        """
        self.configFrame.add(self.configBox)
        self.configBox.show()"""
        self.configFrame.Show()
        return self.configFrame

    #Returning a panel with two buttons
    #@created ana.castro Issue #2
    def getShowFrame(self, show):
        showFrame = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        showFrame.SetSizer(sizer)
		
        episodes = UtilDb().getShowEpisodes(show)
        for episode in episodes:
            self.addEpisodePanel(episode, showFrame, sizer)
        return showFrame

    def setConfs(self, confs):
        self.confs = confs

    def getConf(self, key):
        for conf in self.confs:
            if (conf[0] == key):
                return conf[1]
        return None

    def isConf(self, key, expectedValue):
        for conf in self.confs:
            if (conf[0] == key and conf[1] == expectedValue):
                return True
        return False

    def addLog(self, text):
        wx.CallAfter(self.txt_log.AppendText, text + "\n")

    def _addLog(self, text):
        enditer = self.txt_log.get_buffer().get_end_iter()
        self.txt_log.get_buffer().insert(enditer, text + "\n")

    def addShowInfo(self, button, text):
        #gtk.idle_add(button.set_tooltip_text, text)
        wx.CallAfter(button.SetToolTip, wx.ToolTip(text))

