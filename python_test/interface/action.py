# -*- coding: utf-8 -*-
from protocol import Protocol
import logging
import threading

logger = logging.getLogger(__name__)

class Action(threading.Thread)
    def __init__(self, protocol, params):
        threading.Thread.__init__(self)
        self.protocol = protocol
        self.timeout = 0.1
        
    def run(self):
        