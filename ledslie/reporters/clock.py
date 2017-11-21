import sys
from datetime import datetime

from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks, DeferredList
from twisted.application.internet import ClientService, backoffPolicy
from twisted.internet.endpoints import clientFromString
from twisted.logger import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver,
    FilteringLogObserver, LogLevelFilterPredicate)

from flask.config import Config
import msgpack

from mqtt.client.factory import MQTTFactory

# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER, LEDSLIE_TOPIC_SERIALIZER

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


# -----------------------
# MQTT Publishing Service
# -----------------------

class MQTTService(ClientService):
    def __init__(self, endpoint, factory, config):
        super().__init__(endpoint, factory)
        self.config = config
        self.count = 0

    def startService(self):
        log.info("starting MQTT Client Publisher Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)

    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol = protocol
        self.protocol.onDisconnection = self.onDisconnection
        # We are issuing 3 publish in a row
        # if order matters, then set window size to 1
        # Publish requests beyond window size are enqueued
        self.protocol.setWindowSize(3)
        self.task = task.LoopingCall(self.publish)
        self.task.start(1, now=False)
        try:
            yield self.protocol.connect("TwistedMQTT-clock", keepalive=60)
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}",
                      broker=self.config.get('MQTT_BROKER_CONN_STRING'), excp=e)
        else:
            log.info("Connected to {broker}", broker=self.config.get('MQTT_BROKER_CONN_STRING'))

    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)

    def publish(self):
        display_size = config['DISPLAY_SIZE']
        def _logFailure(failure):
            log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            log.debug("all publihing complete args={args!r}", args=args)

        log.debug(" >< Starting one round of publishing >< ")
        date_str = str(datetime.now().strftime("%a %H:%M:%S"))
        msg = msgpack.packb({b"type": b'1line', b'text': date_str})
        # d = self.protocol.publish(topic=LEDSLIE_TOPIC_SERIALIZER, qos=1, message='\xff'*self.config.get("DISPLAY_SIZE"))
        d = self.protocol.publish(topic=LEDSLIE_TOPIC_TYPESETTER, qos=1, message=bytearray(msg))
        # d.addErrback(_logFailure)
        return d


if __name__ == '__main__':
    config = Config('.')
    config.from_object('ledslie.defaults')
    config.from_envvar('LEDSLIE_CONFIG')

    log = Logger()
    startLogging()
    setLogLevel(namespace='mqtt', levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')

    factory = MQTTFactory(profile=MQTTFactory.PUBLISHER)
    myEndpoint = clientFromString(reactor, config.get('MQTT_BROKER_CONN_STRING'))
    serv = MQTTService(myEndpoint, factory, config)
    serv.startService()
    reactor.run()
