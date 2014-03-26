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

class MainWindow(wx.Frame):

    episodes = []
    shows = []
    showCovers = []

    notebook = None

    # Our new improved callback.  The data passed to this method
    # is printed to stdout.
    def callback(self, widget, data):
        print "Hello again - %s was pressed" % data

    def callbackBtn(self, widget, data):
        if (data == "btnLoadRss"):
            rssParser.loadRSS(self)
        elif (data == "btnSweepSubDir"):
            rssParser.sweepDir(self, 2)
        elif (data == "btnClean"):
            UtilDb().cleanMissingEpisodes(self)
            self.clearEpisodes()
            UtilDb().loadDB(self)
        elif (data == "hide_unmonitored_shows"):
            UtilDb().setConf("hide_unmonitored_shows",
                ("OFF", "ON")[widget.GetValue()])
            self.setConfs(UtilDb().getConfs())
            UtilDb().loadDB(self)
        elif (data == "hide_unmonitored"):
            UtilDb().setConf("hide_unmonitored",
                ("OFF", "ON")[widget.GetValue()])
            self.setConfs(UtilDb().getConfs())
            UtilDb().loadDB(self)
        elif (data == "hide_viewed"):
            UtilDb().setConf("hide_viewed",
                ("OFF", "ON")[widget.GetValue()])
            self.setConfs(UtilDb().getConfs())
            UtilDb().loadDB(self)

    def callbackEntry(self, widget, event, data):
        #keyname = gtk.gdk.keyval_name(event.keyval)
        keycode = event.GetKeyCode()
        if (data == "content_path"
            and keycode == 306):#wx.WXK_RETURN):
            UtilDb().setConf(data, widget.GetValue())
            self.setConfs(UtilDb().getConfs())
            self.addLog("* Content path updated")
        else:
           event.Skip() 

    def callbackEpisode(self, widget, data=None):
        widget.SetValue((True, False)[widget.GetValue()])
        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.GetValue()])
        UtilDb().setViewed(data, ("0", "1")[widget.GetValue()])

    def callbackEpisodeInfo(self, widget, data=None):
        launchThread = False
        if widget.GetToolTip() is not None:
            return
        self.curShowInfoLock.acquire()
        if self.curShowInfo == "":
            launchThread = True
        self.curShowInfo = data
        self.curShowInfoBtn = widget
        self.curShowInfoLock.release()
        if launchThread:
            utilWeb.ShowInfoThread(self)

    def callbackShow(self, widget, data=None):
        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.GetValue()])
        if widget.GetLabelText() == "Fetching":
            UtilDb().setFetching(data, ("0", "1")[widget.GetValue()])
        else:
            UtilDb().setMonitored(data, ("0", "1")[widget.GetValue()])

    def callbackShowRemove(self, widget, data=None):
        print "Remove show %s was clicked" % data[0]
        # removes show if no episodes exist
        #UtilDb().cleanShow(data[0])

    def callbackPlay(self, widget, filepath=None):
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            #pid = os.fork()
            #if pid > 0:
            #    return
            #os.chdir('/')
            #os.setsid()
            #os.umask(0)
            #pid = os.fork()
            #if pid > 0:
            subprocess.call(('xdg-open', filepath))
            #os.system('xdg-open ' + filepath)
            #os.spawnlp(os.P_DETACH, 'xdg-open', 'xdg-open', filepath)
            #pid = subprocess.Popen([sys.executable, "launch.py", filepath])
            #subprocess.call(('python', 'launch.py "' + filepath+'"'))
        print "clicked " + filepath

    # another callback
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def __init__(self, parent):
        # Allow threads
        #gtk.threads_init()
        wx.Frame.__init__(self, parent, -1, "SofaTV",
                          pos=(50, 50), size=(700, 600))
        self.curShowInfo = ""
        self.curShowInfoLock = threading.Lock()

        # Here we just set a handler for delete_event that immediately
        # exits GTK.
        #self.window.connect("delete_event", self.delete_event)

        # Sets the border width of the window.
        #self.window.set_border_width(10)

        #self.Layout()
        #self.Show()

        #self.window.add(self.notebook)
        #frame.add(self.scrolled_window)
        self.wrapper = wx.Panel(self) #gtk.VBox(False, 0)
        self.wraSizer = wx.BoxSizer(wx.VERTICAL)#gtk.HBox(False, 0)

        """self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_border_width(4)
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.scrolled_window.show()
        """

        self.notebook = wx.Notebook(self.wrapper, id=wx.ID_ANY,
                style= wx.BK_DEFAULT)#gtk.Notebook()
        self.wraSizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        self.wrapper.SetSizer(self.wraSizer)
        #self.scrolled_window.add_with_viewport(self.wrapper)

        #self.listPanel = wx.Panel(parent=self.notebook, id=wx.ID_ANY)#, label="Main Frame")#gtk.Frame("Main Frame")
        self.listPanel = wx.ScrolledWindow(parent=self.notebook, id=wx.ID_ANY)
        self.listPanel.SetScrollRate(20, 20)
        self.listPanel.EnableScrolling(True,True)
        #adiciona o box1 agora para ter onde colocar os botoes
        self.lPSizer = wx.BoxSizer(wx.VERTICAL)
        self.listPanel.SetSizer(self.lPSizer)
        self.listPanel.Layout()

        self.boxBtns = wx.BoxSizer(wx.HORIZONTAL)
        self.btnLoadRss = wx.Button(self.listPanel, -1, "Load RSS")
        self.btnSweepSubDir = wx.Button(self.listPanel, -1, "Search files (sub-dir)")
        self.btnClean = wx.Button(self.listPanel, -1, "Clean missing")

        self.btnLoadRss.Bind(wx.EVT_BUTTON,
                lambda evt: self.callbackBtn(self.callbackBtn, "btnLoadRss"))
        self.btnSweepSubDir.Bind(wx.EVT_BUTTON,
                lambda evt: self.callbackBtn(self.callbackBtn, "btnSweepSubDir"))
        self.btnClean.Bind(wx.EVT_BUTTON,
                lambda evt: self.callbackBtn(self.callbackBtn, "btnClean"))
        self.boxBtns.Add(self.btnLoadRss, 0, wx.ALL, 1)
        self.boxBtns.Add(self.btnSweepSubDir, 0, wx.ALL, 1)
        self.boxBtns.Add(self.btnClean, 0, wx.ALL, 1)

        # We create a box to pack widgets into.  This is described in detail
        # in the "packing" section. The box is not really visible, it
        # is just used as a tool to arrange widgets.
        self.box0 = wx.BoxSizer(wx.HORIZONTAL)
        self.box1 = wx.BoxSizer(wx.VERTICAL)
        self.boxShows = wx.BoxSizer(wx.VERTICAL)

        # Put the boxes into the main window.
        self.lPSizer.Add(self.boxBtns)
        self.lPSizer.Add(self.box0)
        self.box0.Add(self.box1)
        self.box0.Add(self.boxShows)

        #frame.set_border_width(10)
        #frame.Show()
        #label = gtk.Label("Main")
        self.notebook.AddPage(self.listPanel, "Main")#.append_page(frame, label)
        """self.coversFrame = gtk.Frame("Covers Frame")
        self.coversFrame.set_border_width(10)
        self.coversBox = gtk.Table(4, 4, True)
        label = gtk.Label("Covers")
        #self.coversBox = gtk.VBox(False, 0)
        self.coversFrame.add(self.coversBox)
        self.coversBox.show()
        self.coversFrame.show()
        self.tX = 0
        self.tY = 0
        self.notebook.append_page(self.coversFrame, label)"""

        UtilDb().prepareDB()
        self.setConfs(UtilDb().getConfs())
        #label = gtk.Label("Config")
        self.notebook.AddPage(self.getConfigFrame(), "Config")
        #self.notebook.Show()
		
		#@modified ana.castro Issue #2
		#Getting the shows being monitored and which have unsee episodes;
		# creating a new tab for each of the shows
		#Defining the tab's content:
		# it consists on all the unseen episodes and the options to see it and set it as already seen
        shows = UtilDb().getMonitoredShowsWithUnseenEpisodes()
        for show in shows:
		   self.notebook.AddPage(self.getShowFrame(show["show"]), show["show"])		
		
        self.Layout()
        self.Show()

        #source_id = gtk.idle_add(rssParser.main, self)
        rssParser.main(self)

    #@modified ana.castro Issue #2
    def addButton(self, episode):
        return self.addEpisodePanel(episode, self.listPanel, self.box1)

    #@modified ana.castro Issue #2
    def addEpisodePanel(self, episode, parentPanel, parentSizer):
        if (self.isConf("hide_unmonitored", "ON") and episode[5] == 0):
            return
        if (self.isConf("hide_viewed", "ON") and episode['viewed'] == 1):
            return
		
        #adiciona um botao rapido..
        boxShow = wx.BoxSizer(wx.HORIZONTAL)
        #self.boxShow = gtk.HBox(False, 0)
        button3 = wx.ToggleButton(parentPanel, -1, episode['show'] + " S" +
        str(episode['season']) + "E" + str(episode['episode']))
        boxShow.Add(button3, 0, wx.ALL, 1)
        if (episode['viewed'] == 1):
            button3.SetValue(True)
        else:
            button3.SetValue(False)
        #self.button3.connect("toggled", self.callbackEpisode, episode)
        button3.Bind(wx.EVT_LEFT_DOWN,
                lambda evt: self.callbackEpisode(button3, episode))
        #self.button3.connect("enter", self.callbackEpisodeInfo, episode)
        button3.Bind(wx.EVT_ENTER_WINDOW,
                lambda evt: self.callbackEpisodeInfo(button3, episode))
        buttonPlay = wx.Button(parentPanel, -1, "Play")#gtk.Button("Play")
        buttonPlay.Bind(wx.EVT_BUTTON,
                lambda evt: self.callbackPlay(None, episode['file']))
        #self.buttonPlay.connect("clicked", self.callbackPlay, episode['file'])
        #self.argBind(wx.EVT_BUTTON, self.callbackPlay, self.buttonPlay, episode['file'])
        boxShow.Add(buttonPlay, 0, wx.ALL, 1)
        #self.episodes.append(self.boxShow)
        parentSizer.Add(boxShow, 0, wx.ALL, 1)
        w, h = self.lPSizer.GetMinSize()
        parentPanel.SetVirtualSize((w, h))

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
        self.txt_content_path = wx.TextCtrl(self.configFrame, size=(300,30))#gtk.Entry()
        #self.configBox.attach(self.txt_content_path, 0, 1, 3, 4)
        #self.txt_content_path.show()
        if self.getConf("content_path"):
            self.txt_content_path.SetValue(self.getConf("content_path"))
        #self.txt_content_path.connect("key-press-event", self.callbackEntry, "content_path")
        self.txt_content_path.Bind(wx.EVT_KEY_DOWN,
                lambda evt: self.callbackEntry(self.txt_content_path, evt, "content_path"))
        sizer.Add(self.txt_content_path, 0, wx.ALL, 10)
        #self.txt_content_path.set_tooltip_text("Content path")

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


def main():
    gtk.main()
