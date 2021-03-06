"""
This module sets up the logging system by looking for a "logging.json"
configuration file. It will search (in this order) the local directory, $PISA
and finally the package resources. The loggers found in there will be lifted
to the module namespace.

Currently, we have three loggers
* logging: generic for what is going on  (typically: `opening file x` or
  `doing this now` messages)
* physics: for any physics output that might be interesting
  (`have x many events`, `the flux is ...`)
* tprofile: for how much time it takes to run some step (in the format of
  `time : start bla`, `time : stop bla`)
"""


from __future__ import absolute_import

import json
import logging as logging_module
import logging.config as logging_config
from os import environ
from os.path import expanduser, expandvars, isfile, join
from pkg_resources import resource_stream


__all__ = ['logging', 'physics', 'tprofile', 'set_verbosity']

__author__ = 'S. Boeser'

__license__ = '''Copyright (c) 2014-2017, The IceCube Collaboration

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.'''


def initialize_logging():
    """Intializing PISA logging"""
    # Add a trace level
    logging_module.TRACE = 5
    logging_module.addLevelName(logging_module.TRACE, 'TRACE')
    def trace(self, message, *args, **kws):
        """Trace-level logging"""
        self.log(logging_module.TRACE, message, *args, **kws)
    logging_module.Logger.trace = trace
    logging_module.RootLogger.trace = trace
    logging_module.trace = logging_module.root.trace

    # Get the logging configuration
    logf = None
    try:
        if 'PISA_RESOURCES' in environ:
            for path in environ['PISA_RESOURCES'].split(':'):
                fpath = join(expanduser(expandvars(path)),
                             'settings/logging/logging.json')
                if isfile(fpath):
                    logf = open(fpath, 'r')
                    break

        if logf is None:
            resource_spec = ('pisa_examples',
                             'resources/settings/logging/logging.json')
            logf = resource_stream(*resource_spec)

        if logf is None:
            raise ValueError('Could not find "logging.json" in PISA_RESOURCES'
                             ' or in pisa_examples/resources.')
        logconfig = json.load(logf)

    finally:
        if logf is not None:
            logf.close()

    # Setup the logging system with this config
    logging_config.dictConfig(logconfig)

    thandler = logging_module.StreamHandler()
    tformatter = logging_module.Formatter(
        fmt=logconfig['formatters']['profile']['format']
    )
    thandler.setFormatter(tformatter)

    # Capture warnings
    logging_module.captureWarnings(True)

    _logging = logging_module.getLogger('pisa')
    _physics = logging_module.getLogger('pisa.physics')
    _tprofile = logging_module.getLogger('pisa.tprofile')
    # TODO: removed following line due to duplicate logging messages. Probably
    # should fix this in a better manner...
    #_tprofile.handlers = [thandler]

    return _logging, _physics, _tprofile


def set_verbosity(verbosity):
    """Overwrite the verbosity level for the root logger
    Verbosity should be an integer with the levels just below.
    """
    # Ignore if no verbosity is given
    if verbosity is None:
        return

    # define verbosity levels
    levels = {0: logging_module.WARN,
              1: logging_module.INFO,
              2: logging_module.DEBUG,
              3: logging_module.TRACE}

    if verbosity not in levels:
        raise ValueError(
            '`verbosity` specified is %s but must be one of %s.'
            %(verbosity, levels.keys())
        )

    # Overwrite the root logger with the verbosity level
    logging.setLevel(levels[verbosity])
    tprofile.setLevel(levels[verbosity])


# Make the loggers public
logging, physics, tprofile = initialize_logging() # pylint: disable=invalid-name
