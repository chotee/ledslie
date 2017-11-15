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

import msgpack
from twisted.internet.defer       import inlineCallbacks, DeferredList
from twisted.internet             import reactor, task
from twisted.internet.endpoints   import clientFromString
from twisted.application.internet import ClientService, backoffPolicy

from twisted.logger   import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver,
    FilteringLogObserver, LogLevelFilterPredicate)

from mqtt.client.factory import MQTTFactory

from flask.config import Config

# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
from ledslie.definitions import LEDSLIE_TOPIC_STATS_BASE, LEDSLIE_TOPIC_SEQUENCES

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


class Scheduler(ClientService):
    def __init__(self, endpoint, factory, config):
        super().__init__(endpoint, factory, retryPolicy=backoffPolicy())
        self.config = config
        self.programs = {}
        self.current_program = None


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
        self.protocol.onPublish       = self.onPublish
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)
        self.task = task.LoopingCall(self.publish_vital_stats)
        self.task.start(5.0, now=False)
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

    def publish(self):
        d1 = self.protocol.publish(topic=LEDSLIE_TOPIC_STATS_BASE+"scheduler", message="Yea, stats")
        d1.addErrback(self._logPublishFailure)
        return d1

    def subscribe(self):

        def _logFailure(failure):
            log.debug("subscriber reported {message}", message=failure.getErrorMessage())
            return failure

        def _logGrantedQoS(value):
            log.debug("subscriber response {value!r}", value=value)
            return True

        #        d1 = self.protocol.subscribe("foo/bar/baz1", 2)
        d1 = self.protocol.subscribe(LEDSLIE_TOPIC_SEQUENCES, 1)
        d1.addCallbacks(_logGrantedQoS, _logFailure)
        return d1


    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("topic={topic}, msg={payload}", payload=payload, topic=topic)


    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)


class Image(object):
    def __init__(self, img_data, **kwargs):
        self.img_data = img_data
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __bytes__(self):
        return self.img_data


class ImageSequence(object):
    def __init__(self, config):
        self.config = config
        self.id = None
        self.sequence = []

    def load(self, payload):
        self.id, seq = msgpack.unpackb(payload)
        for image_data, image_info in seq:
            if len(image_data) != self.config.get('DISPLAY_SIZE'):
                log.error("Images are of the wrong size. Ignoring.")
                return
            try:
                image_duration = image_info[b'duration']
            except KeyError:
                break
            self.sequence.append(Image(image_data, duration=image_duration))
        return self

    @property
    def duration(self):
        return sum([i.duration for i in self.sequence])

    def __iter__(self):
        return iter(self.sequence)


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


#
# from zlib import crc32
#
# import paho.mqtt.client as mqtt
# from collections import deque
#
# import msgpack
# from threading import Timer
#
# from flask.config import Config
#
# from ledslie.definitions import LEDSLIE_TOPIC_SERIALIZER, LEDSLIE_TOPIC_SEQUENCES
#
#
# class GenericProcessor(object):
#     pass
#
#
#
# class Sequencer(GenericProcessor):
#     def __init__(self, config):
#         self.config = config
#         self.queue = deque()
#         self.timer = None
#
#     # The callback for when the client receives a CONNACK response from the server.
#     def on_connect(self, client, userdata, flags, rc):
#         print("Connected with result code "+str(rc))
#
#         # Subscribing in on_connect() means that if we lose the connection and
#         # reconnect then subscriptions will be renewed.
#         client.subscribe(LEDSLIE_TOPIC_SEQUENCES)
#
#     # The callback for when a PUBLISH message is received from the server.
#     def on_message(self, client, userdata, mqtt_msg):
#         queue_started_empty = len(self.queue) == 0
#         seq = ImageSequence(self.config).load(mqtt_msg.payload)
#         client.publish("ledslie/logs/sequencer", "Incoming %s" % seq.id)
#         self.queue.extend(seq)
#         if queue_started_empty and self.queue:
#             self.schedule_image(client)
#
#     def send_image(self, client, image):
#         client.publish(LEDSLIE_TOPIC_SERIALIZER, bytes(image))
#         client.publish("ledslie/logs/sequencer", "Published image %s" % crc32(bytes(image)))
#
#     def schedule_image(self, client):
#         image = self.queue.popleft()
#         self.send_image(client, image)
#         if self.queue:  # there's still work in the queue
#             client.publish("ledslie/logs/sequencer", "Scheduling next image for %dms. %d images in queue" %
#                            (image.duration, len(self.queue)))
#             self.timer = Timer(image.duration/1000.0, self.schedule_image, [client]).start()
#         else:
#             client.publish("ledslie/logs/sequencer", "Image Queue empty")
#
#     def run(self, client):
#         client.on_connect = self.on_connect
#         client.on_message = self.on_message
#         client.connect(self.config.get('MQTT_BROKER_URL'),
#                        self.config.get('MQTT_BROKER_PORT'),
#                        self.config.get('MQTT_KEEPALIVE'))
#         client.loop_forever()
#
#
# if __name__ == '__main__':
#     config = Config('.')
#     config.from_object('ledslie.defaults')
#     config.from_envvar('LEDSLIE_CONFIG')
#     client = mqtt.Client()
#     Sequencer(config).run(client)
