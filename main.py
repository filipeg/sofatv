#!/usr/bin/env python
# -*- coding: utf-8 *-*
import os
import sys
import wx
import glob
from configobj import ConfigObj
from mainWindow import MainWindow
import feedparser
import episodeparser
import sqlite3

def showInList(showName, shows):
    for show in shows:
        if (showName == show[0]):
            return True
    return False

def main():
    """Parses command line arguments
    """
    print "Starting sofaTV"
    default_configuration = os.path.expanduser("~/.config/sofaTV/")
    if not os.path.exists(default_configuration):
        os.makedirs(default_configuration)
    default_configuration += "conf.conf"
    file = open(default_configuration, 'w+')
    file.close()
    #cfg = ConfigObj(default_configuration)
    conn = sqlite3.connect(default_configuration)
    c = conn.cursor()
    # Create table
    c.execute('''CREATE TABLE if not exists episodes
    (show text, season integer, episode integer, viewed integer)''')
    path = "~/Downloads/"
    types = ('*.avi', '*.mkv', '*.mp4') # the tuple of file types
    files_grabbed = []
    episodes = []
    os.chdir(path)
    #cfg['episodes'] = {}
    for files in types:
        files_grabbed.extend(glob.glob(files))
    for file in files_grabbed:
        try:
            episode = episodeparser.parse_filename(file)
            #cfg['episodes'][episode[0]] = episode
            c.execute("INSERT INTO episodes VALUES (\"" + episode[0] + "\"," +
            str(episode[1]) + "," + str(episode[2]) + ",0)")
            episodes.append(episode)
        except NameError:
            pass
    #cfg.write()
    conn.commit()
    for row in c.execute('SELECT * FROM episodes ORDER BY show'):
        print row
        hello.addButton(row)
    conn.close()
    #episodes.append(("leverage",1,1))
    eztv_rss_url = "http://rss.bt-chat.com/?group=3&cat=9"
    feed = feedparser.parse(eztv_rss_url)
    for item in feed["items"]:
        title = item["title"].encode('ascii', 'ignore')
        try:
            episode = episodeparser.parse_filename(title)
            if (showInList(episode[0], episodes)):
                command = "transmission-gtk \"" + item["magneturi"]
                command = command + "&tr=" + item["tracker"] + "\""
                print command
                #os.system(command)
        except NameError:
            pass


class SofaTVApp(wx.App):
    def OnInit(self):
        frame = MainWindow(None)
        self.SetTopWindow(frame)

        frame.Show(True)
        return True


if __name__ == '__main__':
    #hello = mainWindow.MainWindow()
    #mainWindow.main()
    app = SofaTVApp(redirect=False)
    app.MainLoop()
