#!/usr/bin/env python3
"""
    Ledslie, a community information display
    Copyright (C) 2017  Chotee@openended.eu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

============

I decide what information is to be shown on the screen. I do this by keeping track of animations and messages are
available for displaying.

Messages are send to topic «ledslie/sequences/1/» + «name». Where «name» is the name of the sequence to display. For
each name only the last sequence is retained. THis allows producers to provide updated information.

An image is simply a sequence of one frame
"""

import sys

from flask.config import Config
from mqtt.client.factory import MQTTFactory
from twisted.application.internet import ClientService, backoffPolicy, _maybeGlobalReactor
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import clientFromString
from twisted.logger import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver,
    FilteringLogObserver, LogLevelFilterPredicate)

# Global object to control globally namespace logging
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES, LEDSLIE_TOPIC_SERIALIZER
from ledslie.processors.messages import ImageSequence

# ----------------
# Global variables
# ----------------

logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)


# -----------------
# Utility Functions
# -----------------

def startLogging(console=True, filepath=None):
    '''
    Starts the global Twisted logger subsystem with maybe
    stdout and/or a file specified in the config file
    '''
    global logLevelFilterPredicate

    observers = []
    if console:
        observers.append( FilteringLogObserver(observer=textFileLogObserver(sys.stdout),
            predicates=[logLevelFilterPredicate] ))

    if filepath is not None and filepath != "":
        observers.append( FilteringLogObserver(observer=textFileLogObserver(open(filepath, 'a')),
            predicates=[logLevelFilterPredicate] ))
    globalLogBeginner.beginLoggingTo(observers)


def setLogLevel(namespace=None, levelStr='info'):
    '''
    Set a new log level for a given namespace
    LevelStr is: 'critical', 'error', 'warn', 'info', 'debug'
    '''
    level = LogLevel.levelWithName(levelStr)
    logLevelFilterPredicate.setLogLevelForNamespace(namespace=namespace, level=level)

# -----------------------
# MQTT Subscriber Service
# ------------------------


class Catalog(object):
    def __init__(self):
        self.sequences = {}
        self.active_program = None

    def has_content(self):
        return bool(self.sequences)

    def is_empty(self):
        return not self.has_content()

    def select_active_program(self):
        self.active_program = self.sequences[None]

    def remove_program(self, program):
        del self.sequences[None]

    def next_frame(self):
        if self.active_program is None:
            self.select_active_program()
        try:
            return self.active_program.next_frame()
        except IndexError:
            self.remove_program(self.active_program)
            self.active_program = None
            self.select_active_program()
            self.next_frame()

    def add_sequence(self, program_id, seq):
        self.sequences[program_id] = seq


class Scheduler(ClientService):
    def __init__(self, endpoint, factory, config, reactor=None):
        super().__init__(endpoint, factory, retryPolicy=backoffPolicy(), clock=reactor)
        self.reactor = _maybeGlobalReactor(reactor)
        self.config = config
        self.catalog = Catalog()
        self.sequencer = None

    def startService(self):
        log.info("starting MQTT Client Subscriber Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)


    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol                 = protocol
        self.protocol.onPublish       = self.onPublish
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)
        self.stats_task = task.LoopingCall(self.publish_vital_stats)
        self.stats_task.start(5.0, now=False)
        try:
            yield self.protocol.connect("TwistedMQTT-pubsubs", keepalive=60)
            yield self.subscribe()
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}",
                      broker=self.config.get('MQTT_BROKER_CONN_STRING'), excp=e)
        else:
            log.info("Connected and subscribed to {broker}", broker=self.config.get('MQTT_BROKER_CONN_STRING'))

    def _logPublishFailure(failure):
        log.debug("publisher reported {message}", message=failure.getErrorMessage())
        return failure

    def publish_vital_stats(self):
        pass

    def subscribe(self):

        def _logFailure(failure):
            log.debug("subscriber reported {message}", message=failure.getErrorMessage())
            return failure

        def _logGrantedQoS(value):
            log.debug("subscriber response {value!r}", value=value)
            return True

        d1 = self.protocol.subscribe(LEDSLIE_TOPIC_SEQUENCES, 1)
        d1.addCallbacks(_logGrantedQoS, _logFailure)
        return d1


    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("onPublish topic={topic}, msg={payload}", payload=payload, topic=topic)
        program_id = self.get_program_id(topic)
        seq = ImageSequence(self.config).load(payload)
        if seq is None:
            return
        self.catalog.add_sequence(program_id, seq)
        if self.sequencer is None:
            self.sequencer = self.reactor.callLater(0, self.send_next_frame)

    def get_program_id(self, topic):
        program_id = None
        # if topic != LEDSLIE_TOPIC_SEQUENCES:
        #     program_id = topic.split('/')[-1]
        return program_id

    def send_next_frame(self):
        try:
            frame = self.catalog.next_frame()
        except KeyError:
            return
        self.publish_frame(frame)
        self.sequencer = self.reactor.callLater(frame.duration, self.send_next_frame)

    def publish_frame(self, frame):
        d1 = self.protocol.publish(topic=LEDSLIE_TOPIC_SERIALIZER, message=bytes(frame))
        d1.addErrback(self._logPublishFailure)
        return d1

    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)


if __name__ == '__main__':
    config = Config('.')
    config.from_object('ledslie.defaults')
    config.from_envvar('LEDSLIE_CONFIG')

    log = Logger()
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')
    factory    = MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
    myEndpoint = clientFromString(reactor, config.get('MQTT_BROKER_CONN_STRING'))
    serv       = Scheduler(myEndpoint, factory, config)
    serv.startService()
    reactor.run()
