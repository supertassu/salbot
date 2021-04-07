# salbot

Log server admin log messages from IRC channel(s) to a MediaWiki page.

## install

You'll need Python 3 and the requirements in `requirements.txt`, use Docker or
a systemd service or whatever you like to run it.

## config

See the provided example config, modify it and save it as `config.yaml`. The
MediaWiki [OAuth extension](https://www.mediawiki.org/wiki/Extension:OAuth) is
required, you'll need an owner-only OAuth 1 token. It's recommended to use a
separate account and grant it the 'bot' user group.

SASL support is required from the user IRC network.

## usage

When the bot has connected, simply use `!log message here` in any channel that
it's in. No access control is required for my use case so I didn't add any, if
you need it and decide to add it feel free to send a PR and get it merged
upstream.

## license

This program is licensed under the BSD-3-Clause license, see license.txt for
details.
