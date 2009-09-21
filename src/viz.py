#!/usr/bin/env python
# -*- coding: utf-8 -*

from touchwizard.canvas import Canvas
from pipeline_actioner import PipelineActioner
import gobject
from gstmanager.event import EventListener, EventLauncher
import clutter
from clutter import Group, Rectangle, Label, Color

wwidth = 140
wheight = 30
hspacing = 10
vspacing = 20

class PipelineViz(Canvas, EventListener):
    def __init__(self, pipelinel):
        Canvas.__init__(self, 1024,768, "gst-viewperf")
        EventListener.__init__(self)
        self.registerEvent("send_eos")
        self.registerEvent("item_description")
        self.registerEvent("play")
        self.registerEvent("pause")
        self.add_icon(file="player_play", launch_evt="play", desc="Play")
        self.add_icon(file="player_pause", launch_evt="pause", desc="Pause")
        self.add_icon(file="player_stop", launch_evt="send_eos", desc="Send EOS")
        self.add_icon(file="exit", launch_evt="quit", desc="Force Exit")
        self.n_actors = 0
        self.yoffset = 0
        self.pipelinel = pipelinel
        self.parse_pipeline(pipelinel)
        self.display_pipeline()

        self.pipeline_actioner = PipelineActioner(pipelinel)
        self.display_cpuinfo()

        self.desc = desc = Label()
        desc.set_position(0, 400)
        desc.show()
        self.stage.add(desc)

        gobject.timeout_add(100, self.pipeline_actioner.stats.get_queue_info, self.queue_list)
        gobject.timeout_add(100, self.pipeline_actioner.stats.get_videorate_info, self.videorate_list)

    def evt_item_description(self, event):
        txt = event.content
        self.desc.set_text(txt)
        self.desc.set_position(5, self.last_y)

    def parse_pipeline(self, pipelinel):
        self.item_list = item_list = []
        self.queue_list = queue_list = []
        self.videorate_list = videorate_list = []
        for item in pipelinel.pipeline:
            item_list.append(item)
        item_list.reverse()
        for item in item_list:
            name = item.get_name()
            if name.startswith("queue"):
                queue_list.append({"name": name, "elt": item})
                #print "found queue"
            elif name.startswith("videorate"):
                videorate_list.append({"name": name, "elt": item})
       
    def display_pipeline(self):
        for item in self.item_list:
            if not item.get_name().startswith("caps"):
                item = GstElementWidget(item)
                self.add_widget(item)

    def evt_send_eos(self, event):
        self.pipelinel.send_eos()

    def evt_play(self, event):
        self.pipelinel.play()

    def evt_pause(self, event):
        self.pipelinel.pause()
       
    def add_widget(self, widget):
        nb_per_line = int(self.stage.get_width()/wwidth) -1
        #print self.n_actors, nb_per_line
        if self.n_actors >= nb_per_line: 
            #print "new line needed"
            self.yoffset += wheight + vspacing
            self.n_actors = 0
        self.stage.add(widget)
        x = (self.n_actors %nb_per_line)*(wwidth + hspacing) + 5
        y = self.widgets_area.get_position()[1] + self.yoffset + 5
        self.last_y = y + 15 + wheight
        #print y
        widget.set_position(x, y)
        self.n_actors += 1
        if widget.name.find("sink") != -1:
            #print widget.name
            self.yoffset += wheight + vspacing*2
            self.n_actors = 0

    def display_cpuinfo(self):
        self.cpu = cpu = Label()
        cpu.set_line_wrap(False)
        self.update_cpuinfo()
        self.stage.add(cpu)
        cpu.set_position(1024-cpu.get_width(), 590)
        gobject.timeout_add_seconds(10, self.update_cpuinfo)

    def update_cpuinfo(self):
        file = open("/proc/cpuinfo", "r")
        data = file.readlines()
        file.close()
        for line in data:
            if line.startswith("model name"):
                model = line.split(":")[1]
                model = model.replace("\n", "")
            if line.startswith("cpu MHz"):
                freq = line.split(":")[1]
                freq = freq.replace("\n", "")
                freq = freq.split(".")[0]
        self.cpu.set_text("CPU: %s at %s Mhz" %(model, freq))

class GstElementWidget(Group, EventListener, EventLauncher):
    def __init__(self, element):
        EventListener.__init__(self)
        EventLauncher.__init__(self)
        Group.__init__(self)
        self.name = name = element.get_name()
        self.gstelt = element
        if name.find("src") != -1:
            color = clutter.color_parse("Blue")
        elif name.find("sink") != -1:
            color = clutter.color_parse("LightBlue")
        else:
            color = clutter.color_parse("Green")
        self.back = r = Rectangle(color)
        r.set_size(wwidth,wheight)
        r.show()
        self.add(r)
        self.label = l = Label()
        l.show()
        self.add(l)
        self.set_reactive(True)
        self.connect("button-press-event", self.display_props)

        if name.startswith("queue"):
            self.leaky = leaky = int(element.get_property("leaky"))
            if leaky > 0:
                self.name = "%s, leaky" %name
            self.registerEvent("queue_state")
        if name.startswith("progressreport"):
            self.registerEvent("progress_report")
        if name.startswith("videorate"):
            self.registerEvent("videorate")
        l.set_text(self.name)
        self.show()

    def evt_videorate(self, event):
        name = event.content["name"]
        drop = event.content["drop"]
        dup = event.content["dup"]
        text = "%s\nDrop: %s Dup: %s" %(self.name, drop, dup)
        self.label.set_text(text)

    def evt_queue_state(self, event):
        name = event.content["name"]
        fill_state = min(event.content["fill-state"], 100)
        if self.leaky > 0 and fill_state == 100:
            text = "%s\nDROPPING" %(self.name)
        else:
            text = "%s\nfilled %s%%" %(self.name, fill_state)
        if self.name == name or self.name == "%s, leaky" %name:
            red = int(fill_state*2.55)
            green = 255 - red
            color = Color(red, green, 0, 255)
            self.back.set_color(color)
            self.label.set_text(text)

    def evt_progress_report(self, event):
        name = event.content["name"]
        progress_s = event.content["progress_s"]
        if self.name == name:
            text = "%s\nLate by: %s sec" %(name, progress_s)
            if int(progress_s) < 0 and int(progress_s) > -2:
                self.back.set_color(clutter.color_parse("Orange"))
            elif int(progress_s) <= -2:
                self.back.set_color(clutter.color_parse("Red"))
            else:
                self.back.set_color(clutter.color_parse("Green"))
            self.label.set_text(text)

    def display_props(self, source, event):
        desc = "Item description:\n"
        elt = self.gstelt
        import gobject
        props = gobject.list_properties(elt)
        for prop in props:
            name = prop.name
            if name != "last-buffer":
                value = elt.get_property(name)
                desc += "%s=%s\n" %(name, str(value))
        self.launchEvent("item_description", desc)
