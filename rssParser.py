# -*- coding: utf-8 *-*
import os
import re
import subprocess
import glob
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
        cfg_file = open(default_configuration, 'w+')
        cfg_file.close()
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

    path = os.path.expanduser(db.getContentPath())
    types = ('*.avi', '*.mkv', '*.mp4') # the tuple of file types
    files_grabbed = []
    episodes = []

    if not os.path.exists(path):
        db.loadDB(ui)
        db.closeConn()
        return

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
    if len(files_grabbed) > 0:
        db.commit()
    db.loadDB(ui)
    db.closeConn()


def sweepDir(ui, levels):
    db = UtilDb()
    db.prepareDB()
    path = os.path.expanduser(db.getContentPath())
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
        print file
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
    if len(files_grabbed) > 0:
        db.commit()
    episode_count = len(episodes)

    # Enters sub-directories
    subdirs = []
    if (levels > 0):
        for subdir in os.walk('.').next()[1]:
            subdirs.append(subdir)
            episode_count += sweepSubDir(ui, db, path + subdir + "/", levels - 1)

    if not episode_count and subdirs:
        for subdir in subdirs:
            if not (subdir.startswith("Season ") or
                subdir.startswith("season ")):
                return episode_count
        # Seems we have a show directory with Season subdirectories
        show_name = os.path.basename(os.path.normpath(path))
        for subdir in subdirs:
            sweepSeasonSubDir(ui, db, path + subdir + "/", show_name, subdir)

    return episode_count


def sweepSeasonSubDir(ui, db, path, showname, dirname):
    types = ('*.avi', '*.mkv', '*.mp4')  # the tuple of file types
    files_grabbed = []
    episodes = []

    season = 0
    seasonMatch = re.compile(r'[Ss][a-s]* ([0-9]+)').search(dirname)
    if seasonMatch:
        season = int(seasonMatch.group(1))
    else:
        # Invalid directory name
        return

    os.chdir(path)

    for files in types:
        files_grabbed.extend(glob.glob(files))
    for file in files_grabbed:
        try:
            episode = episodeparser.parse_filename_episode(file, showname, season)
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
    if len(files_grabbed) > 0:
        db.commit()

    episode_count = len(episodes)

    return episode_count


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
    if ui.getConf("btorrent_client_path"):
        client = ui.getConf("btorrent_client_path")
    else:
        return
    loaded = modified = False
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
                    command = client + " \"" + item["magneturi"]
                    command = command + "&tr=" + item["tracker"] + "\""
                    #print command
                    command = item["magneturi"] + "&tr=" + item["tracker"]
                    #os.system(command)
                    subprocess.Popen([client, command])
                    db.insertRssEpisode(episode)
                    modified = True
                    ui.addLog("Downloading " + episode[0] + "S" +
                        str(episode[1]) + "E" + str(episode[2]))
                else:
                    ui.addLog("Already have " + episode[0] + "S" +
                        str(episode[1]) + "E" + str(episode[2]))
        except NameError:
            pass
    if modified:
        db.commit()
    if not loaded:
        ui.addLog("Failed to load feed")
