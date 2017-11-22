import sys

import os
from mqtt.client.factory import MQTTFactory
from twisted.application.internet import ClientService
from twisted.internet.endpoints import clientFromString
from twisted.internet import reactor

from twisted.logger import Logger, LogLevel, globalLogBeginner, textFileLogObserver, \
    FilteringLogObserver, LogLevelFilterPredicate

# ----------------
# Global variables
# ----------------
from ledslie.config import Config

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


def CreateReporter(reporterCls):
    startLogging()
    setLogLevel(namespace='mqtt', levelStr='debug')
    setLogLevel(namespace=reporterCls.__name__, levelStr='debug')

    factory = MQTTFactory(profile=MQTTFactory.PUBLISHER)
    myEndpoint = clientFromString(reactor, Config().get('MQTT_BROKER_CONN_STRING'))
    serv = reporterCls(myEndpoint, factory)
    serv.startService()
    return serv

class GenericReporter(ClientService):
    def __init__(self, endpoint, factory):
        super().__init__(endpoint, factory)
        self.config = Config()
        self.log = Logger(self.__class__.__name__)

    def startService(self):
        log.info("starting MQTT Client Publisher Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)

    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)
