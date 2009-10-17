#!/usr/bin/env python
# -*- coding: utf-8 -*

from gstmanager.event import EventListener, EventLauncher
from statsgrabber import StatsGrabber

class PipelineActioner(EventListener):
    def __init__(self, pipelinel):
        EventListener.__init__(self)
        self.registerEvent("send_eos")
        self.registerEvent("item_description")
        self.registerEvent("play")
        self.registerEvent("pause")
        self.pipelinel = pipelinel
        self.stats = StatsGrabber(pipelinel)

    def evt_send_eos(self, event):
        self.pipelinel.send_eos()

    def evt_play(self, event):
        self.pipelinel.play()

    def evt_pause(self, event):
        self.pipelinel.pause()
