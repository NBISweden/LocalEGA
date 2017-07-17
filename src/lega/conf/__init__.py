import sys
import configparser
import logging
from logging.config import fileConfig, dictConfig
from pathlib import Path
import yaml

_config_files = [
    Path(__file__).parent / 'defaults.ini',
    Path.home() / '.lega/conf.ini'
]

f"""This module provides a dictionary-like with configuration settings.
It also loads the logging settings when `setup` is called.

The `--log <file>` argument is used to configuration where the logs go.
Without it, there is no logging capabilities.
The <file> can be in `INI` or `YAML` format.

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from {_config_files[0]}
* from {_config_files[1]}
* and finally from the file specified as the `--conf` argument.


See `https://github.com/NBISweden/LocalEGA` for a full documentation.
:copyright: (c) 2017, NBIS System Developers.
"""

LOG = logging.getLogger('lega-conf')

class Configuration(configparser.RawConfigParser):
    conf_file = None
    log_conf = None

    def _load_conf(self,args=None, encoding='utf-8'):
        f'''Loads the configuration files in order:
           1) {_config_files[0]}
           2) {_config_files[1]}
           3) the command line arguments following `--conf`

        When done, the logging settings are loaded
        from the file specified after the `--log` argument.

        The latter file must be either in `INI` format
        or in `YAML` format, in which case, it must end in `.yaml` or `.yml`.'''

        # Finding the --conf file
        try:
            self.conf_file = Path(args[ args.index('--conf') + 1 ])
            if self.conf_file not in _config_files:
                _config_files.append( self.conf_file )
            LOG.info(f"Overriding configuration settings with {self.conf_file}")
        except ValueError:
            LOG.info("--conf <file> was not mentioned\n"
                     "Using the default configuration files")
        except (TypeError, AttributeError): # if args = None
            LOG.info("Using the default configuration files")
        except IndexError:
            LOG.error("Wrong use of --conf <file>")
            raise ValueError("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)

    def _load_log_file(self,filename):
        LOG.info(f'Reading the log configuration from: {filename}')
        if filename.suffix in ('.yaml', '.yml'):
            with open(filename, 'r') as stream:
                dictConfig(yaml.load(stream))
                self.log_conf = filename
        else: # It's an ini file
            fileConfig(filename)
            self.log_conf = filename

    def _load_log_conf(self,args=None):
        # Finding the --log file
        try:
            lconf = Path(args[ args.index('--log') + 1 ])
            self._load_log_file(lconf)
        except ValueError:
            LOG.info("--log <file> was not mentioned")
            default_log_conf = self.get('DEFAULT','log_conf',fallback=None)
            if default_log_conf:
                default_log_conf = Path(default_log_conf)
                self._load_log_file(default_log_conf)
        except (TypeError, AttributeError): # if args = None
            pass # No log conf
        except IndexError:
            LOG.error("Wrong use of --log <file>")
            sys.exit(2)
        except Exception as e:
            print(e)
            #sys.exit(2)

    def setup(self,args=None, encoding='utf-8'):
        self._load_conf(args,encoding)
        self._load_log_conf(args)


    def __repr__(self):
        '''Show the configuration files'''
        res = 'Configuration files:\n\t* ' + '\n\t* '.join(str(s) for s in _config_files)
        if self.log_conf:
            res += '\nLogging settings loaded from ' + str(self.log_conf)
        return res

CONF = Configuration()
