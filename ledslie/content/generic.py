# Ledslie, a community information display
# Copyright (C) 2017-18  Chotee@openended.eu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

import os
from mqtt.client.factory import MQTTFactory
from twisted.application.internet import ClientService
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import clientFromString
from twisted.internet import reactor

from twisted.logger import Logger, LogLevel, globalLogBeginner, textFileLogObserver, \
    FilteringLogObserver, LogLevelFilterPredicate

# ----------------
# Global variables
# ----------------
from ledslie.config import Config
from ledslie.definitions import LEDSLIE_TOPIC_STATS_BASE

logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

log = Logger(__file__.split(os.sep)[-1])

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
        observers.append(FilteringLogObserver(observer=textFileLogObserver(sys.stdout),
                                              predicates=[logLevelFilterPredicate]))

    if filepath is not None and filepath != "":
        observers.append(FilteringLogObserver(observer=textFileLogObserver(open(filepath, 'a')),
                                              predicates=[logLevelFilterPredicate]))
    globalLogBeginner.beginLoggingTo(observers)


def setLogLevel(namespace=None, levelStr='info'):
    '''
    Set a new log level for a given namespace
    LevelStr is: 'critical', 'error', 'warn', 'info', 'debug'
    '''
    level = LogLevel.levelWithName(levelStr)
    logLevelFilterPredicate.setLogLevelForNamespace(namespace=namespace, level=level)


def CreateContent(contentCls):
    startLogging()
    setLogLevel(namespace='mqtt', levelStr='debug')
    setLogLevel(namespace=contentCls.__name__, levelStr='debug')

    factory = MQTTFactory(profile=MQTTFactory.PUBLISHER)
    myEndpoint = clientFromString(reactor, Config().get('MQTT_BROKER_CONN_STRING'))
    serv = contentCls(myEndpoint, factory)
    serv.startService(contentCls.__name__)
    return serv

class GenericContent(ClientService):
    def __init__(self, endpoint, factory, reactor=None):
        super().__init__(endpoint, factory)
        if reactor is None:
            from twisted.internet import reactor
        self.reactor = reactor
        self.config = Config()
        self.protocol = None
        self._system_name = None

    def startService(self, name):
        log.info("starting MQTT Content Publisher Service")
        # invoke whenConnected() inherited method
        self._system_name = name
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)

    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol = protocol
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)
        try:
            yield self.protocol.connect(self._system_name, keepalive=60)
        except Exception as e:
            self.log.error("Connecting to {broker} raised {excp!s}",
                      broker=self.config.get('MQTT_BROKER_CONN_STRING'), excp=e)
        else:
            self.log.info("Connected to {broker}", broker=self.config.get('MQTT_BROKER_CONN_STRING'))
            self.reactor.callLater(0, self.onBrokerConnected)
        self_name = self.__class__.__name__
        self.publish(topic=LEDSLIE_TOPIC_STATS_BASE+self_name, message="%s now (re-)connected" % self_name)

    def onBrokerConnected(self):
        log.info("onBrokerConnected called")

    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)

    def publish(self, topic, message, qos=0, retain=False):
        if hasattr(message, 'serialize'):
            message = message.serialize()
        return self.protocol.publish(topic, message, qos, retain)
