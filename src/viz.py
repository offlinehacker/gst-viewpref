#!/usr/bin/env python
# -*- coding: utf-8 -*

from wizard.canvas import Canvas
from statsgrabber import StatsGrabber
import gobject
from gstmanager.event import EventListener, EventLauncher
from candies.core import Group, Rectangle, Color, Label
from clutter import Color as CColor

wwidth = 100
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
        self.add_icon(name="player_play", action_signal="play", desc="Play")
        self.add_icon(name="player_pause", action_signal="pause", desc="Pause")
        self.add_icon(name="player_stop", action_signal="send_eos", desc="Send EOS")
        self.add_icon(name="exit", action_signal="quit", desc="Force Exit")
        self.n_actors = 0
        self.yoffset = 0
        self.pipelinel = pipelinel
        self.parse_pipeline(pipelinel)
        self.display_pipeline()
        self.stats = StatsGrabber()

        self.desc = desc = Label()
        desc.set_position(0, 400)
        desc.show()
        self.stage.add(desc)

        gobject.timeout_add(100, self.stats.get_queue_info, pipelinel, self.queue_list)

    def evt_item_description(self, event):
        txt = event.content
        self.desc.set_text(txt)
        self.desc.set_position(5, self.last_y)

    def parse_pipeline(self, pipelinel):
        self.item_list = item_list = []
        self.queue_list = queue_list = []
        for item in pipelinel.pipeline:
            item_list.append(item)
        item_list.reverse()
        for item in item_list:
            name = item.get_name()
            if name.startswith("queue"):
                queue_list.append({"name": name, "elt": item})
                #print "found queue"
       
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


class GstElementWidget(Group, EventListener, EventLauncher):
    def __init__(self, element):
        EventListener.__init__(self)
        EventLauncher.__init__(self)
        Group.__init__(self)
        self.name = name = element.get_name()
        self.gstelt = element
        if name.find("src") != -1:
            color = Color("Blue")
        elif name.find("sink") != -1:
            color = Color("LightBlue")
        else:
            color = Color("Green")
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
        l.set_text(self.name)
        self.show()

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
            color = CColor(red, green, 0, 255)
            self.back.set_color(color)
            self.label.set_text(text)

    def evt_progress_report(self, event):
        name = event.content["name"]
        progress_s = event.content["progress_s"]
        if self.name == name:
            text = "%s\nLate by: %s sec" %(name, progress_s)
            if int(progress_s) < 0 and int(progress_s) > -2:
                self.back.set_color(Color("Orange"))
            elif int(progress_s) <= -2:
                self.back.set_color(Color("Red"))
            else:
                self.back.set_color(Color("Green"))
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

