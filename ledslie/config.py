from flask import Config as FlaskConfig

_Config_instance = None

def Config(envvar_silent=True):
    global  _Config_instance
    if _Config_instance is None:
        _Config_instance = FlaskConfig('.')
        _Config_instance.from_object('ledslie.defaults')
        _Config_instance.from_envvar('LEDSLIE_CONFIG', silent=envvar_silent)
    return _Config_instance

