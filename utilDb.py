# -*- coding: utf-8 *-*
import os
import sqlite3
import datetime, time
import rssParser
import utilWeb

class UtilDb():
    _instance = None
    conn = None
    c = None
    treta = None

    def __init__(self, city="Berlin"):
        self.treta = city

    #def __new__(cls, *args, **kwargs):
    #    if not cls._instance:
    #        cls._instance = super(UtilDb, cls).__new__(
    #                            cls, *args, **kwargs)
    #    return cls._instance

    def getC(self):
        if not self.c:
            self.conn = sqlite3.connect(rssParser.getDefConf(), timeout=10)
            # Enable access to row elements by name or by index.
            self.conn.row_factory = sqlite3.Row
            self.c = self.conn.cursor()
        return self.c

    def commit(self):
        self.conn.commit()

    def closeConn(self):
        self.conn.close()
        self.c = None

    def prepareDB(self):
        # Create table
        c = self.getC()
        c.execute('''CREATE TABLE if not exists shows
        (show text, monitored integer, fetching integer, cover text,
        hasCover integer, PRIMARY KEY (show))''')
        c.execute('''CREATE TABLE if not exists episodes
        (show text, season integer, episode integer, viewed integer, file text,
        PRIMARY KEY (show, season, episode))''')
        c.execute('''CREATE TABLE if not exists config
        (key text, value text,
        PRIMARY KEY (key))''')

    def insertRssEpisode(self, episode):
        c = self.getC()
        c.execute("INSERT INTO episodes VALUES (\"" + episode[0] + "\"," +
            str(episode[1]) + "," + str(episode[2]) + ",0, \"\")")

    def insertFoundEpisode(self, episode, path):
        c = self.getC()
        try:
            c.execute("INSERT INTO episodes VALUES (\"" + episode[0] + "\"," +
                str(episode[1]) + "," + str(episode[2]) + ",0, \"" + path + "\")")
        except sqlite3.IntegrityError:
            c.execute("UPDATE episodes SET file = \"" + path + "\" WHERE show = \"" +
                str(episode[0]) + "\" AND season = " + str(episode[1]) +
                " AND episode = " + str(episode[2]))

    def insertFoundShow(self, showname):
        c = self.getC()
        c.execute("INSERT INTO shows " +
                "(show, monitored, fetching, cover, hasCover) VALUES (\"" +
                showname + "\", 1, 1, \"\", 0)")

        # if new show is inserted
        sid = utilWeb.GetShowID(showname)
        imgPath = ""
        if (sid):
            #imgPath = "http://images.tvrage.com/shows/" + str(int(str(sid)[0])+1) + "/" + sid + ".jpg"
            c.execute("UPDATE shows SET cover = \"" + sid +
                "\", hasCover=1 WHERE show = \"" + showname + "\"")

    def cleanMissingEpisodes(self, ui):
        c = self.getC()
        missingFiles = []
        future = datetime.datetime.now() + datetime.timedelta(days=5)
        deadline = int(time.mktime(future.timetuple()))
        now = int(time.mktime(datetime.datetime.now().timetuple()))

        # Removes shows that are both unmonitored and have no episodes in
        # the database
        for show in c.execute("SELECT * FROM shows WHERE monitored == 0 " +
                                "AND show NOT IN (SELECT show FROM episodes)"):
            self.cleanShow(show['show'])
            ui.addLog("Removing the show '" + show['show'] +
                "' from the database")

        for row in c.execute("SELECT * FROM episodes WHERE file <> \"\" " +
                                "AND viewed < 2"):
            if not (os.path.isfile(row[4])):
                # adds missing file to list
                missingFiles.append(row[4])

        # record the deadline for the missing files
        if missingFiles:
            c.execute("UPDATE episodes SET viewed = " + str(deadline) +
                " WHERE file IN (\"" + "\", \"".join(missingFiles) + "\")")
            ui.addLog("The following episodes are missing: " +
                "\n".join(missingFiles))

        # delete every record with a missing file OR past the deadline
        c.execute("DELETE FROM episodes WHERE file = \"\" OR " +
        "(viewed > 1 AND viewed < " + str(now) + ")")
        self.commit()
        self.closeConn()

    def cleanShow(self, showName):
        c = self.getC()
        valid = True
        # checks if the show has any episode
        for row in c.execute("SELECT * FROM episodes WHERE show =\"" +
         showName + "\""):
            valid = False
        if (valid):
            c.execute("DELETE FROM shows WHERE show =\"" +
            showName + "\" AND fetching = 0")
            self.commit()

    def showInList(self, c, showName):
        for row in c.execute("SELECT * FROM shows WHERE show =\"" +
         showName + "\" AND fetching = 1"):
            return True
        return False

    def shouldDownload(self, c, showName, season, episode):
        for row in c.execute("SELECT * FROM episodes WHERE show = \"" +
        showName + "\" AND season = " + str(season) + " AND episode = " +
        str(episode)):
            return False
        return True

    def setViewed(self, episode, viewed):
        c = self.getC()
        c.execute("UPDATE episodes SET viewed = " + viewed +
        " WHERE show = \"" + episode[0] + "\" AND season = " +
        str(episode[1]) + " AND episode = " +
        str(episode[2]))
        self.commit()
        self.closeConn()
        return True

    def setMonitored(self, show, monitored):
        c = self.getC()
        c.execute("UPDATE shows SET monitored = " + monitored +
        " WHERE show = \"" + show[0] + "\"")
        self.commit()
        self.closeConn()
        return True

    def setFetching(self, show, fetching):
        c = self.getC()
        c.execute("UPDATE shows SET fetching = " + fetching +
        " WHERE show = \"" + show[0] + "\"")
        self.commit()
        self.closeConn()
        return True

    def getConfs(self):
        c = self.getC()
        confs = []
        for row in c.execute("SELECT * FROM config"):
            confs.append((str(row[0]), str(row[1])))
        self.closeConn()
        return confs

    def setConfs(self, ui):
        confs = self.getConfs()
        ui.setConfs(confs)

    def setConf(self, key, value):
        print "set " + value
        c = self.getC()
        c.execute("INSERT OR REPLACE into config VALUES (\"" + key +
            "\", \"" + value + "\")")
        self.commit()
        self.closeConn()
        return True

    def loadDB(self, ui):
        ui.clearEpisodes()
        c = self.getC()
        for row in c.execute("""SELECT episodes.*, shows.monitored
                            FROM episodes INNER JOIN shows ON episodes.show = shows.show
                            WHERE viewed < 2 ORDER BY episodes.show"""):
            ui.addButton(row)
        for row in c.execute("""SELECT show, monitored, fetching, cover,
        hasCover FROM shows ORDER BY show"""):
            ui.addShow(row)
