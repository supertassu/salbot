#!/usr/bin/env python3
from argparse import ArgumentParser
import datetime
from ib3 import Bot
from ib3.auth import SASL
from ib3.connection import SSL
from ib3.mixins import DisconnectOnError, RejoinOnKick
from ib3.nick import Regain
import logging
import mwclient
import os.path
import yaml


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%SZ',
)
logging.captureWarnings(True)

logger = logging.getLogger('salbot')
logger.setLevel(logging.DEBUG)


parser = ArgumentParser(description='salbot')
parser.add_argument(
    '-c',
    '--config',
    default=os.path.join(os.path.dirname(__file__), 'config.yml'),
    help='Configuration file',
)


class IrcLogBot(SASL, SSL, DisconnectOnError, RejoinOnKick, Bot, Regain):
    def __init__(self, config):
        self.config = config

        super(IrcLogBot, self).__init__(
            server_list=[(self.config['irc']['server'], self.config['irc']['port'])],
            nickname=self.config['irc']['nick'],
            realname=self.config['irc']['realname'],
            ident_password=self.config['irc']['password'],
            channels=self.config['irc']['channels'],
        )

        self.site = mwclient.Site(
            self.config['mediawiki']['host'],
            path=self.config['mediawiki']['path'],
            scheme=self.config['mediawiki']['scheme'],
            consumer_token=self.config['mediawiki']['consumer_token'],
            consumer_secret=self.config['mediawiki']['consumer_secret'],
            access_token=self.config['mediawiki']['access_token'],
            access_secret=self.config['mediawiki']['access_secret'],
            clients_useragent='SALbot',
        )

    def get_version(self):
        return 'SALBot'

    def on_pubmsg(self, conn, event):
        if not self.has_primary_nick():
            # Don't do anything if we haven't acquired the primary nick
            return

        msg: str = event.arguments[0]
        channel: str = event.target
        nick: str = event.source.split('!')[0]

        if not msg.startswith('!log'):
            continue

        self.handle_msg(channel, msg, nick)

    def handle_msg(self, channel: str, msg: str, user: str):
        sal_msg = msg[5:].strip()

        now = datetime.datetime.utcnow()

        page = self.site.Pages[self.config['mediawiki']['page']]
        text = page.text()
        lines = text.split('\n')
        first_header = 0

        target_section = now.strftime('== %Y-%m-%d ==')
        logline = '* [%02d:%02d] <%s> %s' % (
            now.hour,
            now.minute,
            user,
            sal_msg,
        )
        summary = '%s <%s> %s' % (channel, user, sal_msg)

        for pos, line in enumerate(lines):
            if line.startswith('== '):
                first_header = pos
                break

        if lines[first_header] == target_section:
            lines.insert(first_header + 1, logline)
        else:
            lines.insert(first_header, '')
            lines.insert(first_header, logline)
            lines.insert(first_header, target_section)

        page.save('\n'.join(lines), summary=summary, bot=True)
        self.connection.privmsg(channel, '%s: Your message was logged!' % user)
        logger.info('Logged %s to SAL by request of %s on %s', sal_msg, user, channel)


if __name__ == '__main__':
    args = parser.parse_args()
    config = yaml.safe_load(open(args.config, 'r'))
    logbot = IrcLogBot(config)

    try:
        logbot.start()
    except KeyboardInterrupt:
        logbot.disconnect()
    except Exception as e:
        logbot.disconnect()
        raise e
