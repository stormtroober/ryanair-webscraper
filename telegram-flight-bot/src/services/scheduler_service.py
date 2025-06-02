from threading import Timer

class SchedulerService:
    def __init__(self, flight_search_function, interval=5400):
        self.flight_search_function = flight_search_function
        self.interval = interval
        self.timer = None

    def start(self):
        self.schedule_next_run()

    def schedule_next_run(self):
        self.timer = Timer(self.interval, self.run_flight_search)
        self.timer.start()

    def run_flight_search(self):
        self.flight_search_function()
        self.schedule_next_run()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()