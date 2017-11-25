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
"""

import sys

from mqtt.client.factory import MQTTFactory
from twisted.application.internet import ClientService, backoffPolicy, _maybeGlobalReactor
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks, DeferredList
from twisted.internet.endpoints import clientFromString
from twisted.logger import Logger, LogLevel, globalLogBeginner, textFileLogObserver, \
    FilteringLogObserver, LogLevelFilterPredicate

from ledslie.config import Config

logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

log = Logger()

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


def CreateService(ServiceCls):
    startLogging()
    setLogLevel(namespace='mqtt', levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')
    factory = MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
    myEndpoint = clientFromString(reactor, Config().get('MQTT_BROKER_CONN_STRING'))
    serv = ServiceCls(myEndpoint, factory)
    serv.startService(ServiceCls.__name__)
    return serv


class GenericProcessor(ClientService):
    subscriptions = ()

    def __init__(self, endpoint, factory, reactor=None):
        super().__init__(endpoint, factory, retryPolicy=backoffPolicy(), clock=reactor)
        self.reactor = _maybeGlobalReactor(reactor)
        self.config = Config()

    def startService(self, name):
        log.info("starting MQTT Client Subscriber&Publisher Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker, name)
        ClientService.startService(self)

    @inlineCallbacks
    def connectToBroker(self, protocol, name):
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
            yield self.protocol.connect(name, keepalive=60)
            yield self.subscribe()
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}",
                      broker=self.config.get('MQTT_BROKER_CONN_STRING'), excp=e)
        else:
            log.info("Connected and subscribed to {broker}", broker=self.config.get('MQTT_BROKER_CONN_STRING'))
            self.reactor.callLater(0, self.onBrokerConnected)

    def onBrokerConnected(self):
        log.info("onBrokerConnected called")

    def subscribe(self):
        def _logFailure(failure):
            log.debug("subscriber reported {message}", message=failure.getErrorMessage())
            return failure

        def _logGrantedQoS(value):
            log.debug("subscriber response {value!r}", value=value)
            return True
        deferreds = []
        for topic, qos in self.subscriptions:
            d = self.protocol.subscribe(topic, qos)
            d.addCallbacks(_logGrantedQoS, _logFailure)
            deferreds.append(d)
        return DeferredList(deferreds)

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        raise NotImplemented()

    def publish(self, topic, message, qos=0, retain=False):
        if isinstance(message, bytes):
            message = bytearray(message)
        return self.protocol.publish(topic, message, qos, retain=retain)

    def _logPublishFailure(failure):
        log.debug("publisher reported {message}", message=failure.getErrorMessage())
        return failure

    def publish_vital_stats(self):
        pass

    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)