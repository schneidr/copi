#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import os
import subprocess
#import cgi

class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="coPi")
        self.set_border_width(3)
        
        grid = Gtk.Grid()
        self.add(grid)
        
        self.targetGrid = Gtk.Grid()
        self.targetLabel = Gtk.Label("Ziel: Nicht angeschlossen")
        self.targetProgressBar = Gtk.ProgressBar()
        self.targetProgressBar.set_fraction(0)
        self.targetProgressBar.set_text("Nicht angeschlossen")
        self.targetProgressBar.set_show_text(True)
        self.targetButtonEject = Gtk.Button(label="Auswerfen")
        self.targetButtonEject.connect("clicked", self.on_targetButtonEject_clicked)
        self.targetGrid.add(self.targetLabel)
        self.targetGrid.attach_next_to(self.targetProgressBar, self.targetLabel, Gtk.PositionType.BOTTOM, 1, 1)
        self.targetGrid.attach_next_to(self.targetButtonEject, self.targetLabel, Gtk.PositionType.RIGHT, 1, 2)
        grid.add(self.targetGrid)

        self.statusGrid = Gtk.Grid()
        grid.attach_next_to(self.statusGrid, self.targetGrid, Gtk.PositionType.BOTTOM, 1, 1)

        self.sourceGrid = Gtk.Grid()
        self.sourceLabel = Gtk.Label("Quelle: Nicht angeschlossen")
        self.sourceProgressBar = Gtk.ProgressBar()
        self.sourceProgressBar.set_fraction(0)
        self.sourceProgressBar.set_text("Nicht angeschlossen")
        self.sourceProgressBar.set_show_text(True)
        self.sourceButtonEject = Gtk.Button(label="Auswerfen")
        self.sourceButtonEject.connect("clicked", self.on_sourceButtonEject_clicked)
        self.sourceGrid.add(self.sourceLabel)
        self.sourceGrid.attach_next_to(self.sourceProgressBar, self.sourceLabel, Gtk.PositionType.BOTTOM, 1, 1)
        self.sourceGrid.attach_next_to(self.sourceButtonEject, self.sourceLabel, Gtk.PositionType.RIGHT, 1, 2)
        grid.attach_next_to(self.sourceGrid, self.targetGrid, Gtk.PositionType.BOTTOM, 1, 1)
        
        self.updateStatus()
        
        # quit cleanly when the windows is closed
        # otherwise the process just keeps hanging		
        self.connect("delete-event", self.mainQuit)

    def on_sourceButtonEject_clicked(self, b):
        subprocess.call(["sudo", "umount", self.sourcePath])
        self.updateStatus()

    def on_targetButtonEject_clicked(self, b):
        subprocess.call(["sudo", "umount", self.targetPath])
        self.updateStatus()

    def updateStatus(self):
        path = "/media/pi"
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
                if dir.startswith('backup'):
                    self.targetLabel.set_text("Ziel: " + dir)
                    self.targetProgressBar.set_fraction(free/total)
                    self.targetProgressBar.set_text("%s frei" % self.sizeof_fmt(free))
                    self.targetPath = dirpath
                else:
                    self.sourceLabel.set_text("Quelle: " + dir)
                    self.sourceProgressBar.set_fraction(free/total)
                    self.sourceProgressBar.set_text("%s frei" % self.sizeof_fmt(free))
                    self.sourcePath = dirpath
        if self.sourcePath is None:
            self.sourceLabel.set_text("Quelle: Nicht angeschlossen")
            self.sourceProgressBar.set_fraction(0.0)
            self.sourceProgressBar.set_text("Nicht angeschlossen")
        if self.targetPath is None:
            self.targetLabel.set_text("Quelle: Nicht angeschlossen")
            self.targetProgressBar.set_fraction(0.0)
            self.targetProgressBar.set_text("Nicht angeschlossen")

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

