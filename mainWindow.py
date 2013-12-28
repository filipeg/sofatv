#!/usr/bin/env python
# -*- coding: utf-8 *-*

import pygtk
pygtk.require('2.0')
import gtk
import sys
import subprocess
import os
import threading
import rssParser
from utilDb import UtilDb
import utilWeb


class MainWindow:

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
            UtilDb().cleanMissingEpisodes()
            self.clearEpisodes()
            UtilDb().loadDB(self)
        elif (data == "hide_unmonitored_shows"):
            UtilDb().setConf("hide_unmonitored_shows",
                ("OFF", "ON")[widget.get_active()])
            self.setConfs(UtilDb().getConfs())
            UtilDb().loadDB(self)
        elif (data == "hide_unmonitored"):
            UtilDb().setConf("hide_unmonitored",
                ("OFF", "ON")[widget.get_active()])
            self.setConfs(UtilDb().getConfs())
            UtilDb().loadDB(self)
        elif (data == "hide_viewed"):
            UtilDb().setConf("hide_viewed",
                ("OFF", "ON")[widget.get_active()])
            self.setConfs(UtilDb().getConfs())
            UtilDb().loadDB(self)

    def callbackEpisode(self, widget, data=None):
        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])
        UtilDb().setViewed(data, ("0", "1")[widget.get_active()])

    def callbackEpisodeInfo(self, widget, data=None):
        launchThread = False
        if widget.get_has_tooltip():
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
        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])
        if widget.get_label() == "Fetching":
            UtilDb().setFetching(data, ("0", "1")[widget.get_active()])
        else:
            UtilDb().setMonitored(data, ("0", "1")[widget.get_active()])

    def callbackShowRemove(self, widget, data=None):
        print "Remove show %s was clicked" % data[0]
        # removes show if no episodes exist
        UtilDb().cleanShow(data[0])

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

    def __init__(self):
        # Allow threads
        gtk.threads_init()
        self.curShowInfo = ""
        self.curShowInfoLock = threading.Lock()

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        # This is a new call, which just sets the title of our
        # new window to "Hello Buttons!"
        self.window.set_title("SofaTV")
        self.window.set_size_request(700, 600)

        # Here we just set a handler for delete_event that immediately
        # exits GTK.
        self.window.connect("delete_event", self.delete_event)

        # Sets the border width of the window.
        self.window.set_border_width(10)

        self.notebook = gtk.Notebook()
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_border_width(4)
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.scrolled_window.show()

        self.wrapper = gtk.VBox(False, 0)
        self.box = gtk.HBox(False, 0)
        self.scrolled_window.add_with_viewport(self.wrapper)

        frame = gtk.Frame("Main Frame")
        frame.set_border_width(10)
        frame.show()
        label = gtk.Label("Main")
        self.notebook.append_page(frame, label)
        self.coversFrame = gtk.Frame("Covers Frame")
        self.coversFrame.set_border_width(10)
        self.coversBox = gtk.Table(4, 4, True)
        label = gtk.Label("Covers")
        #self.coversBox = gtk.VBox(False, 0)
        self.coversFrame.add(self.coversBox)
        self.coversBox.show()
        self.coversFrame.show()
        self.tX = 0
        self.tY = 0
        self.notebook.append_page(self.coversFrame, label)

        self.setConfs(UtilDb().getConfs())
        label = gtk.Label("Config")
        self.notebook.append_page(self.getConfigFrame(), label)
        self.notebook.show()

        self.window.add(self.notebook)
        frame.add(self.scrolled_window)
        self.btnLoadRss = gtk.Button("Load RSS")
        self.btnSweepSubDir = gtk.Button("Search files (sub-dir)")
        self.btnClean = gtk.Button("Clean missing")

        self.btnLoadRss.connect("clicked", self.callbackBtn, "btnLoadRss")
        self.btnSweepSubDir.connect("clicked", self.callbackBtn, "btnSweepSubDir")
        self.btnClean.connect("clicked", self.callbackBtn, "btnClean")
        self.wrapper.add(self.btnLoadRss)
        self.wrapper.add(self.btnSweepSubDir)
        self.wrapper.add(self.btnClean)
        self.wrapper.add(self.box)

        # We create a box to pack widgets into.  This is described in detail
        # in the "packing" section. The box is not really visible, it
        # is just used as a tool to arrange widgets.
        self.box1 = gtk.VBox(False, 0)
        self.box2 = gtk.VBox(False, 0)

        # Put the box into the main window.
        self.box.pack_start(self.box1, True, True, 0)
        self.box.pack_start(self.box2, True, True, 0)

        # Creates a new button with the label "Button 1".
        self.button1 = gtk.Button("Button 1")

        # Now when the button is clicked, we call the "callback" method
        # with a pointer to "button 1" as its argument
        self.button1.connect("clicked", self.callback, "button 1")

        # Instead of add(), we pack this button into the invisible
        # box, which has been packed into the window.
        #self.box1.pack_start(self.button1, True, True, 0)

        # Always remember this step, this tells GTK that our preparation for
        # this button is complete, and it can now be displayed.
        #self.button1.show()

        # Do these same steps again to create a second button
        self.button2 = gtk.Button("Button 2")

        # Call the same callback method with a different argument,
        # passing a pointer to "button 2" instead.
        self.button2.connect("clicked", self.callback, "button 2")

        #self.box1.pack_start(self.button2, True, True, 0)

        # The order in which we show the buttons is not really important, but I
        # recommend showing the window last, so it all pops up at once.
        #self.button2.show()
        self.btnLoadRss.show()
        self.btnSweepSubDir.show()
        self.btnClean.show()
        self.wrapper.show()
        self.box.show()
        self.box1.show()
        self.box2.show()
        self.window.show()

        source_id = gtk.idle_add(rssParser.main, self)

    def addButton(self, episode):
        if (self.isConf("hide_unmonitored", "ON") and episode[5] == 0):
            return
        if (self.isConf("hide_viewed", "ON") and episode['viewed'] == 1):
            return

        self.boxShow = gtk.HBox(False, 0)
        self.button3 = gtk.ToggleButton(episode['show'] + " S" +
        str(episode['season']) + "E" + str(episode['episode']))
        if (episode['viewed'] == 1):
            self.button3.set_active(True)
        else:
            self.button3.set_active(False)
        self.button3.connect("toggled", self.callbackEpisode, episode)
        self.button3.connect("enter", self.callbackEpisodeInfo, episode)
        self.buttonPlay = gtk.Button("Play")
        self.buttonPlay.connect("clicked", self.callbackPlay, episode['file'])
        self.boxShow.pack_start(self.button3, True, True, 0)
        self.boxShow.pack_start(self.buttonPlay, True, True, 0)
        self.box1.pack_start(self.boxShow, True, True, 0)
        self.button3.show()
        self.buttonPlay.show()
        self.boxShow.show()
        self.episodes.append(self.boxShow)

    def clearEpisodes(self):
        for box in self.episodes:
            box.hide()
        for box in self.shows:
            box.hide()
        self.episodes = []
        self.shows = []

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
        self.boxShow = gtk.HBox(False, 0)
        self.btnMonitored = gtk.ToggleButton(show['show'])
        if (show['monitored'] == 1):
            self.btnMonitored.set_active(True)
        else:
            self.btnMonitored.set_active(False)
        self.btnMonitored.connect("toggled", self.callbackShow, show)
        self.btnFetching = gtk.ToggleButton("Fetching")
        if (show['fetching'] == 1):
            self.btnFetching.set_active(True)
        else:
            self.btnFetching.set_active(False)
        self.btnFetching.connect("clicked", self.callbackShow, show)
        self.boxShow.pack_start(self.btnMonitored, True, True, 0)
        self.boxShow.pack_start(self.btnFetching, True, True, 0)
        self.box2.pack_start(self.boxShow, True, True, 0)
        self.btnMonitored.show()
        self.btnFetching.show()
        self.boxShow.show()
        self.shows.append(self.boxShow)

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
        pixbuf = gtk.gdk.pixbuf_new_from_file(show['cover'])
        scaled_buf = pixbuf.scale_simple(100,100,gtk.gdk.INTERP_BILINEAR)
        image.set_from_pixbuf(scaled_buf)
        image.show()
        aspect_frame = gtk.AspectFrame(show['show'], # label
            0.5, # center x
            0.5, # center y
            1.5, # xsize/ysize = 2
            False) # ignore child's aspect

        aspect_frame.show()
        self.showCovers.append(image)
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
        self.configFrame = gtk.Frame("Config Frame")
        self.configFrame.set_border_width(10)
        self.configBox = gtk.Table(1, 4, False)
        label = gtk.Label("Config")

        self.btn_hide_unmonitored_shows = gtk.CheckButton("Hide unmonitored shows")
        self.configBox.attach(self.btn_hide_unmonitored_shows, 0, 1, 0, 1)
        self.btn_hide_unmonitored_shows.show()
        self.btn_hide_unmonitored_shows.set_active(self.isConf("hide_unmonitored_shows", "ON"))
        self.btn_hide_unmonitored_shows.connect("toggled", self.callbackBtn, "hide_unmonitored_shows")

        self.btn_hide_unmonitored = gtk.CheckButton("Hide unmonitored shows' episodes")
        self.configBox.attach(self.btn_hide_unmonitored, 0, 1, 1, 2)
        self.btn_hide_unmonitored.show()
        self.btn_hide_unmonitored.set_active(self.isConf("hide_unmonitored", "ON"))
        self.btn_hide_unmonitored.connect("toggled", self.callbackBtn, "hide_unmonitored")

        self.btn_hide_viewed = gtk.CheckButton("Hide viewed episodes")
        self.configBox.attach(self.btn_hide_viewed, 0, 1, 2, 3)
        self.btn_hide_viewed.show()
        self.btn_hide_viewed.set_active(self.isConf("hide_viewed", "ON"))
        self.btn_hide_viewed.connect("toggled", self.callbackBtn, "hide_viewed")

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.txt_log = gtk.TextView()
        self.txt_log.set_editable(False)
        self.txt_log.set_cursor_visible(False)
        sw.add(self.txt_log)
        sw.show()
        self.configBox.attach(sw, 0, 1, 3, 5)
        self.txt_log.show()

        self.configFrame.add(self.configBox)
        self.configBox.show()
        self.configFrame.show()
        return self.configFrame

    def setConfs(self, confs):
        self.confs = confs

    def isConf(self, key, expectedValue):
        for conf in self.confs:
            if (conf[0] == key and conf[1] == expectedValue):
                return True
        return False

    def addLog(self, text):
        gtk.idle_add(self._addLog, text)

    def _addLog(self, text):
        enditer = self.txt_log.get_buffer().get_end_iter()
        self.txt_log.get_buffer().insert(enditer, text + "\n")

    def addShowInfo(self, button, text):
        #gtk.idle_add(self.btnClean.set_label, text)
        gtk.idle_add(button.set_tooltip_text, text)


def main():
    gtk.main()
