#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import signal
import os
import subprocess
import re
import threading
GObject.threads_init()

## TODO:
## - update on signal
## - icons instead of text on the buttons
## - localization, defaulting to english

class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="coPi")
        Gtk.Window.fullscreen(self)
        self.set_border_width(3)
        grid = Gtk.Grid()
        self.add(grid)

        ## TODO:
        ## find the correct way to provide IDs for stock icons  
        ## https://developer.gnome.org/icon-naming-spec/      
#        ejectIcon = Gtk.Image()
#        ejectIcon.set_from_stock(Gtk., Gtk.IconSize.BUTTON)
#        playIcon = Gtk.Image()
#        playIcon.set_from_stock("media-playback-start", Gtk.IconSize.BUTTON)

        self.sourceGrid = Gtk.Grid()
        self.sourceLabel = Gtk.Label("Quelle: Nicht angeschlossen")
        self.sourceProgressBar = Gtk.ProgressBar()
        self.sourceProgressBar.set_fraction(0)
        self.sourceProgressBar.set_text("Nicht angeschlossen")
        self.sourceProgressBar.set_show_text(True)
        self.sourceButtonEject = Gtk.Button(label="Auswerfen")
        self.sourceButtonEject.set_hexpand(True)
        self.sourceButtonEject.connect("clicked", self.on_sourceButtonEject_clicked)
        self.sourceGrid.add(self.sourceLabel)
        self.sourceGrid.attach_next_to(self.sourceProgressBar, self.sourceLabel, Gtk.PositionType.BOTTOM, 1, 1)
        self.sourceGrid.attach_next_to(self.sourceButtonEject, self.sourceLabel, Gtk.PositionType.RIGHT, 1, 2)
        grid.add(self.sourceGrid)
        
        self.targetGrid = Gtk.Grid()
        self.targetLabel = Gtk.Label("Ziel: Nicht angeschlossen")
        self.targetProgressBar = Gtk.ProgressBar()
        self.targetProgressBar.set_fraction(0)
        self.targetProgressBar.set_text("Nicht angeschlossen")
        self.targetProgressBar.set_show_text(True)
        self.targetButtonEject = Gtk.Button("Auswerfen")
        self.targetButtonEject.set_hexpand(True)
        self.targetButtonEject.connect("clicked", self.on_targetButtonEject_clicked)
        self.targetGrid.add(self.targetLabel)
        self.targetGrid.attach_next_to(self.targetProgressBar, self.targetLabel, Gtk.PositionType.BOTTOM, 1, 1)
        self.targetGrid.attach_next_to(self.targetButtonEject, self.targetLabel, Gtk.PositionType.RIGHT, 1, 2)
        grid.attach_next_to(self.targetGrid, self.sourceGrid, Gtk.PositionType.BOTTOM, 1, 1)

        self.statusGrid = Gtk.Grid()
        self.statusLabel = Gtk.Label("Kopiervorgang")
        self.statusProgressBar = Gtk.ProgressBar()
        self.statusProgressBar.set_fraction(0)
        self.statusProgressBar.set_text("Warten")
        self.statusProgressBar.set_show_text(True)
        self.statusButtonStart = Gtk.Button("Start")
        self.statusButtonStart.connect("clicked", self.on_statusButtonStart_clicked)
        self.statusButtonStart.set_hexpand(True)
        self.statusGrid.add(self.statusLabel)
        self.statusGrid.attach_next_to(self.statusProgressBar, self.statusLabel, Gtk.PositionType.BOTTOM, 1, 1)
        self.statusGrid.attach_next_to(self.statusButtonStart, self.statusLabel, Gtk.PositionType.RIGHT, 1, 2)
        grid.attach_next_to(self.statusGrid, self.targetGrid, Gtk.PositionType.BOTTOM, 1, 1)

        self.systemGrid = Gtk.Grid()
        self.statusButtonUpdate = Gtk.Button("Aktualisieren")
        self.statusButtonUpdate.connect("clicked", self.on_systemButtonUpdate_clicked)
        self.systemGrid.add(self.statusButtonUpdate)
        self.statusButtonShutdown = Gtk.Button("Pi Herunterfahren")
        self.statusButtonShutdown.connect("clicked", self.on_systemButtonShutdown_clicked)
        self.systemGrid.add(self.statusButtonShutdown)
        grid.attach_next_to(self.systemGrid, self.statusGrid, Gtk.PositionType.BOTTOM, 1, 1)
        
        self.updateStatus()
        
        ## quit cleanly when the windows is closed
        ## otherwise the process just keeps hanging		
        self.connect("delete-event", self.mainQuit)
        ## TODO: update display on signal
        ## https://pymotw.com/2/signal/
        signal.signal(signal.SIGUSR1, self.receive_signal_usr1)

    def receive_signal_usr1(self, signum, stack):
        self.updateStatus()

    def on_systemButtonUpdate_clicked(self, b):
        self.updateStatus()

    def on_systemButtonShutdown_clicked(self, b):
        subprocess.call(["sudo", "shutdown", "-h", "now"])

    def on_statusButtonStart_clicked(self, b):
        threading.Thread(target=self.copy).start()
        #self.copy()

    def on_sourceButtonEject_clicked(self, b):
        subprocess.call(["sudo", "umount", self.sourcePath])
        self.updateStatus()

    def on_targetButtonEject_clicked(self, b):
        subprocess.call(["sudo", "umount", self.targetPath])
        self.updateStatus()

    def copy(self):
        print "Kopiere"
        GObject.idle_add(self.sourceButtonEject.set_sensitive, False)
        GObject.idle_add(self.targetButtonEject.set_sensitive, False)
        GObject.idle_add(self.statusButtonStart.set_sensitive, False)
        # https://gist.github.com/JohannesBuchner/4d61eb5a42aeaad6ce90
        cmd = "sudo rsync --info=progress2 -a %s %s" % (self.sourcePath, self.targetPath)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(proc.stdout.readline, ""):
            m = re.findall(r'\s(\d+)%', stdout_line)
            if m:
                progress = int(m[0])
                progress_float = progress / 100.0
                GObject.idle_add(self.statusProgressBar.set_text, "%d%%" % progress)
                GObject.idle_add(self.statusProgressBar.set_fraction, progress_float)
        proc.stdout.close()
        return_code = proc.wait()
        GObject.idle_add(self.sourceButtonEject.set_sensitive, True)
        GObject.idle_add(self.targetButtonEject.set_sensitive, True)
        GObject.idle_add(self.statusButtonStart.set_sensitive, True)
        GObject.idle_add(self.updateStatus)

    def updateStatus(self):
        path = "/media"
        dirs = os.listdir(path)
        self.sourcePath = None
        self.targetPath = None
        for dir in dirs:
            dirpath = path + "/" + dir
            if os.path.isdir(dirpath):
                stat = os.statvfs(dirpath)
                total = stat.f_blocks*stat.f_bsize
                free = stat.f_bfree*stat.f_bsize
                used = (stat.f_blocks-stat.f_bfree)*stat.f_bsize
                percent = float(used)/float(total)
                if dir.startswith('backup'):
                    self.targetLabel.set_text("Ziel: " + dir)
                    self.targetProgressBar.set_fraction(percent)
                    self.targetProgressBar.set_text("%s frei" % self.sizeof_fmt(free))
                    self.targetPath = dirpath
                    self.targetButtonEject.set_sensitive(True)
                else:
                    self.sourceLabel.set_text("Quelle: " + dir)
                    self.sourceProgressBar.set_fraction(percent)
                    self.sourceProgressBar.set_text("%s frei" % self.sizeof_fmt(free))
                    self.sourcePath = dirpath
                    self.sourceButtonEject.set_sensitive(True)
        if self.sourcePath is None:
            self.sourceLabel.set_text("Quelle: Nicht angeschlossen")
            self.sourceProgressBar.set_fraction(0.0)
            self.sourceProgressBar.set_text("Nicht angeschlossen")
            self.sourceButtonEject.set_sensitive(False)
        if self.targetPath is None:
            self.targetLabel.set_text("Ziel: Nicht angeschlossen")
            self.targetProgressBar.set_fraction(0.0)
            self.targetProgressBar.set_text("Nicht angeschlossen")
            self.targetButtonEject.set_sensitive(False)
        if self.sourcePath is None or self.targetPath is None:
            self.statusButtonStart.set_sensitive(False)
        else:
            self.statusButtonStart.set_sensitive(True)

    def sizeof_fmt(self, num, suffix='B'):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)		

    def mainQuit(self, b, c):
        Gtk.main_quit(self, b, c)

win = MyWindow()
win.show_all()
Gtk.main()

