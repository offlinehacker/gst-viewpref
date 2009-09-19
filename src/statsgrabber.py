from gstmanager.event import EventListener, EventLauncher 

class StatsGrabber(EventLauncher, EventListener):
    def __init__(self):
        EventListener.__init__(self)
        EventLauncher.__init__(self)
        self.registerEvent('progress')
        self.reference_progress = 0

    def get_queue_info(self, pipelinel, name_list):
        fills = []
        # set_property_on_element example
        for queue in name_list:
            fill_time = pipelinel.get_property_on_element(element_name=queue["name"], property_name="current-level-time")
            max_time = pipelinel.get_property_on_element(element_name=queue["name"], property_name="max-size-time")
            fill_percent = int((fill_time/float(max_time))*100)
            fills.append(fill_percent)
            self.launchEvent("queue_state",{"name": queue["name"], "fill-state": fill_percent})
        return True

    def evt_progress(self, event):
        data = event.content["data"]
        source = event.content["source"]
        progress_s = data["current"]
        if source == "progressreport0":
            self.reference_progress = progress_s
            self.launchEvent("info", "Progress: %s seconds" %progress_s)
        rel_progress = progress_s - self.reference_progress
        self.launchEvent("progress_report", {"name": source, "progress_s": rel_progress})

