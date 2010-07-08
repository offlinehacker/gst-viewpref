#!/usr/bin/env python
# -*- coding: utf-8 -*

import touchwizard
import easyevent
import clutter
import candies2
import os

__path__ = os.path.dirname(os.path.abspath(os.path.expanduser(__file__)))
touchwizard.icon_path = __path__

class SamplePanel(candies2.container.ContainerAdapter, easyevent.User,
                                             clutter.Actor, clutter.Container):
    __gtype_name__ = 'SamplePanel'
    
    def __init__(self):
        candies2.container.ContainerAdapter.__init__(self)
        clutter.Actor.__init__(self)
        easyevent.User.__init__(self)
        self.connect('notify::visible', self.on_show)
        
    def on_show(self, panel, event):
        if self.props.visible:
            self.launch_event('info_message', 'Welcome to the Touchwizard Test Page !')
    
   
class Page(touchwizard.Page):
    title = 'Gst-viewperf'
    name = 'viewperf'
    panel = SamplePanel

if __name__ == '__main__':
    touchwizard.quick_launch(Page)
    '''
    stage = clutter.Stage()
    stage.set_size(800, 480)
    stage.connect('destroy', clutter.main_quit)
    
    panel = SamplePanel()
    panel.set_position(0, 23)
    panel.set_size(800, 360)
    
    stage.add(panel)
    stage.show()

    clutter.main()
    '''
