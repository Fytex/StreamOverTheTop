class RoutingTable:
    def __init__(self, server, previous, metric, destins):
        self.server = server
        self.previous = previous
        self.metric = metric
        self.destins = destins
        self.state = False