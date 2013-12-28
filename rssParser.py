# -*- coding: utf-8 *-*
import os
import sys
import subprocess
import glob
from configobj import ConfigObj
import threading
import feedparser
import episodeparser
from utilDb import UtilDb
import sqlite3

def getDefConf():
    default_configuration = os.path.expanduser("~/.config/sofaTV/")
    if not os.path.exists(default_configuration):
        os.makedirs(default_configuration)
    default_configuration += "conf.conf"
    if not (os.path.isfile(default_configuration)):
        file = open(default_configuration, 'w+')
        file.close()
    return default_configuration

def main(ui):
    """Parses command line arguments
    """
    print "Starting sofaTV"
    #default_configuration = getDefConf()

    #cfg = ConfigObj(default_configuration)
    #conn = sqlite3.connect(default_configuration)
    #c = conn.cursor()

    db = UtilDb()
    db.prepareDB()
    c = db.getC()

    path = os.path.expanduser("~/Downloads/")
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
            #c.execute("INSERT INTO episodes VALUES (\"" + episode[0] + "\"," +
            #str(episode[1]) + "," + str(episode[2]) + ",0, \"" + path+file + "\")")
            db.insertFoundEpisode(episode, path+file)
            episodes.append(episode)
            try:
                #c.execute("INSERT INTO shows VALUES (\"" + episode[0] + "\", 1)")
                db.insertFoundShow(episode[0])
            except sqlite3.IntegrityError:
                pass
        except NameError:
            pass
        except sqlite3.IntegrityError:
            pass
    #cfg.write()
    db.commit()
    db.loadDB(ui)
    db.closeConn()


def sweepDir(ui, levels):
    db = UtilDb()
    db.prepareDB()
    c = db.getC()
    path = os.path.expanduser("~/Downloads/")
    sweepSubDir(ui, db, path, levels)

    db.loadDB(ui)
    db.closeConn()


def sweepSubDir(ui, db, path, levels):
    types = ('*.avi', '*.mkv', '*.mp4')  # the tuple of file types
    files_grabbed = []
    episodes = []
    os.chdir(path)
    #cfg['episodes'] = {}

    for files in types:
        files_grabbed.extend(glob.glob(files))
    for file in files_grabbed:
        try:
            episode = episodeparser.parse_filename(file)
            db.insertFoundEpisode(episode, path + file)
            episodes.append(episode)
            try:
                db.insertFoundShow(episode[0])
            except sqlite3.IntegrityError:
                pass
        except NameError:
            pass
        except sqlite3.IntegrityError:
            pass
    db.commit()

    # Enters sub-directories
    if (levels > 0):
        for subdir in os.walk('.').next()[1]:
            sweepSubDir(ui, db, path + subdir + "/", levels - 1)


class LoadRssThread(threading.Thread):

    def __init__(self, ui):
        super(LoadRssThread, self).__init__()
        self.ui = ui
        self.start()

    def run(self):
        loadRSSThread(self.ui)


# Wrapper for threaded loadRSSThread
def loadRSS(ui):
    LoadRssThread(ui)


# Loads RSS feeds, should run in a seperate thread
def loadRSSThread(ui):

    db = UtilDb()
    c = db.getC()

    #episodes.append(("leverage",1,1))
    eztv_rss_url = "http://rss.bt-chat.com/?group=3&cat=9"
    #eztv_rss_url = "http://rss.bt-chat.com/?group=2&cat=9" # VTV
    #eztv_rss_url = "http://feeds.feedburner.com/eztv-rss-atom-feeds?format=xml"
    loadRSSFeed(db, eztv_rss_url, ui)

    eztv_rss_url = "http://rss.bt-chat.com/?group=2&cat=9"  # VTV
    loadRSSFeed(db, eztv_rss_url, ui)

    db.closeConn()


# Called by loadRSS(), loads an URL
def loadRSSFeed(db, feedUrl, ui):
    loaded = False
    ui.addLog("** Loading RSS feed: " + feedUrl)
    feed = feedparser.parse(feedUrl)
    c = db.getC()

    for item in feed["items"]:
        loaded = True
        title = item["title"].encode('ascii', 'ignore')
        try:
            episode = episodeparser.parse_filename(title)
            if (db.showInList(c, episode[0])):
                if (db.shouldDownload(c, episode[0], episode[1], episode[2])):
                    command = "transmission-gtk \"" + item["magneturi"]
                    command = command + "&tr=" + item["tracker"] + "\""
                    print command
                    command = item["magneturi"] + "&tr=" + item["tracker"]
                    #os.system(command)
                    subprocess.Popen(['transmission-gtk', command])
                    db.insertRssEpisode(episode)
                    ui.addLog("Downloading " + episode[0] + "S" +
                        str(episode[1]) + "E" + str(episode[2]))
                else:
                    #print "Já temos " + str(episode)
                    ui.addLog("Já temos " + episode[0] + "S" +
                        str(episode[1]) + "E" + str(episode[2]))
            #else:
            #    print "Não interessa: " + str(episode)
                #os.system(command)
        except NameError:
            pass
    if loaded:
        db.commit()
    else:
        ui.addLog("Failed to load feed")
