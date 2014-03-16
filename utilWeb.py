# -*- coding: utf-8 *-*
import urllib
import os
import threading
import time


def GetQuickInfo(showname, episode=None):
    #showname = showname.replace(" ","")
    urlPrefix = "http://services.tvrage.com/tools/quickinfo.php?show="
    url = urlPrefix + showname
    strStrip = "b'<pre>Show ID@\n"
    pos = 1
    data = "<>"
    if episode is not None:
        url = url + "&ep=" + episode
        strStrip = "b'Episode Info@\n"
        pos = 7

    try:
        webFile = urllib.urlopen(url)

    except:
        return 0

    i = 0
    for entry in webFile:
        i += 1
        if i == pos:
            line = str(entry)
            data = line.strip(strStrip)
        else:
            pass
    webFile.close()
    return data


def GetShowID(showname):
    #showname = showname.replace(" ","")
    urlPrefix = "http://services.tvrage.com/tools/quickinfo.php?show="
    url = urlPrefix + showname

    try:
        webFile = urllib.urlopen(url)

    except:
        return 0

    i = 0
    for entry in webFile:
        i += 1
        if i == 1:
            line = str(entry)
            ShowID = line.strip("b'<pre>Show ID@\n")
        else:
            pass
    webFile.close()

    cachePath = None
    if ShowID == 'No Show Results Were Found For "'+showname+'"':
        ShowID=None #ShowID = "Nicht gefunden..."
    else:
        imgUrl = "http://images.tvrage.com/shows/" + str(int(int(ShowID)/1000+1)) + "/" + ShowID + ".jpg"
        cachePath = os.path.expanduser("~/.cache/sofaTV/")
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        cachePath = cachePath + ShowID + ".jpg"
        urllib.urlretrieve(imgUrl, cachePath)
        pass #ShowID=int(ShowID)

    return cachePath


class ShowInfoThread(threading.Thread):

    def __init__(self, ui):
        super(ShowInfoThread, self).__init__()
        self.ui = ui
        self.start()

    def run(self):
        finished = False
        expected = ""
        expectedBtn = None
        while not finished:
            self.ui.curShowInfoLock.acquire()
            if self.ui.curShowInfo == "":
                self.ui.curShowInfoLock.release()
                return  # error
            if expected == "" or self.ui.curShowInfo[4] != expected[4]:
                expected = self.ui.curShowInfo
                expectedBtn = self.ui.curShowInfoBtn
                self.ui.curShowInfoLock.release()
            else:
                self.ui.curShowInfoLock.release()
                showinfo = GetQuickInfo(expected[0], str(expected[1])
                        + "x" + str(expected[2])).split("^")
                if len(showinfo) < 3:
                    showinfo = ("", "<>")
                self.ui.addShowInfo(expectedBtn, "[" +
                showinfo[0] + "] " + showinfo[1] + " (" + showinfo[2] + ")")
                finished = True

            if finished:
                self.ui.curShowInfoLock.acquire()
                self.ui.curShowInfo = ""
                self.ui.curShowInfoLock.release()
            else:
                time.sleep(0.5)
