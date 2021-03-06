#!/usr/bin/env python3.5

"""A simple web crawler -- main driver program."""

# TODO:
# - Add arguments to specify TLS settings (e.g. cert/key files).

import argparse
import asyncio
import requests
import logging
import base64
import configparser
import sys

import crawling
import reporting

from server import StoppableHTTPServer, AuthHandler

ARGS = argparse.ArgumentParser(description="Web crawler")
ARGS.add_argument(
    '--iocp', action='store_true', dest='iocp',
    default=False, help='Use IOCP event loop (Windows only)')
ARGS.add_argument(
    '--select', action='store_true', dest='select',
    default=False, help='Use Select event loop instead of default')
ARGS.add_argument(
    'roots', nargs='*',
    default=[], help='Root URL (may be repeated)')
ARGS.add_argument(
    '--max_redirect', action='store', type=int, metavar='N',
    default=10, help='Limit redirection chains (for 301, 302 etc.)')
ARGS.add_argument(
    '--max_tries', action='store', type=int, metavar='N',
    default=4, help='Limit retries on network errors')
ARGS.add_argument(
    '--max_tasks', action='store', type=int, metavar='N',
    default=100, help='Limit concurrent connections')
ARGS.add_argument(
    '--exclude', action='store', metavar='REGEX',
    help='Exclude matching URLs')
ARGS.add_argument(
    '--strict', action='store_true',
    default=True, help='Strict host matching (default)')
ARGS.add_argument(
    '--lenient', action='store_false', dest='strict',
    default=False, help='Lenient host matching')
ARGS.add_argument(
    '-v', '--verbose', action='count', dest='level',
    default=2, help='Verbose logging (repeat for more verbose)')
ARGS.add_argument(
    '-q', '--quiet', action='store_const', const=0, dest='level',
    default=2, help='Only log errors')
ARGS.add_argument(
    '--auth', action='store_true', dest='auth',
    default=False, help='Use CREST Authentication (fill out client_app.ini)')
ARGS.add_argument(
    '--invalid', action='store_true', dest='invalid',
    default=False, help='Invalidate the stored refresh token and go through the authorization process again')
ARGS.add_argument(
    '--nopages', action='store_false', dest='follow_pages',
    default=True, help='Do not follow page links')

def fix_url(url):
    """Prefix a schema-less URL with http://."""
    if '://' not in url:
        url = 'http://' + url
    return url


def main():
    """Main program.

    Parse arguments, set up event loop, run crawler, print report.
    """
    args = ARGS.parse_args()
    if not args.roots:
        print('Use --help for command line help')
        return

    global config
    global headers

    config = configparser.ConfigParser()
    config.read('client_app.ini')

    headers = {
        "User-Agent": config['client']['user-agent']
    }

    # @todo: figure out what to do with these. Currently just for creating the auth URL
    scopes = [
        'publicData',
        'characterContactsRead',
        'characterFittingsRead',
        'characterLocationRead'
    ]

    if args.auth:
        id = bytes("{}:{}".format(config['client']['Key'], config['client']['secret']), encoding="utf-8")
        headers.update({
            "Authorization": b"Basic " + base64.b64encode(id),
            "Content-Type": "application/x-www-form-urlencoded"
        })

        if config['client'].get('refresh', None) and not args.invalid:
            print("Using Refresh token to login")
            # do requests here to get auth/refresh code and stick them in config (save maybe?)
            r = requests.post('https://login.eveonline.com/oauth/token',
                              data="grant_type=refresh_token&refresh_token={}".format(config['client']['refresh']),
                              headers=headers).json()
            headers.update({"Authorization": "Bearer {}".format(r['access_token'])})
        else:
            def handleLogin(httpd, parts):
                # do requests here to get auth/refresh code and stick them in config (save maybe?)
                r = requests.post('https://login.eveonline.com/oauth/token',
                                  data="grant_type=authorization_code&code={}".format(parts['code'][0]),
                                  headers=headers).json()

                config["client"]["refresh"] = r['refresh_token']
                with open('client_app.ini', 'w') as configfile:
                    config.write(configfile)

                headers.update({"Authorization": "Bearer {}".format(r['access_token'])})
                httpd.stop()

            httpd = StoppableHTTPServer(('', 6789), AuthHandler)
            url = "https://login.eveonline.com/oauth/authorize/?response_type=code&scope={}&redirect_uri=http://localhost:6789/&client_id={}".format("+".join(scopes), config['client']['key'])
            print("Please go here to authenticate: \n {}".format(url))
            httpd.serve(handleLogin)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(args.level, len(levels)-1)])

    if args.iocp:
        from asyncio.windows_events import ProactorEventLoop
        loop = ProactorEventLoop()
        asyncio.set_event_loop(loop)
    elif args.select:
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    roots = {fix_url(root) for root in args.roots}

    crawler = crawling.Crawler(roots,
                               exclude=args.exclude,
                               strict=args.strict,
                               max_redirect=args.max_redirect,
                               max_tries=args.max_tries,
                               max_tasks=args.max_tasks,
                               headers=headers,
                               follow_pages=args.follow_pages,
                               )
    try:
        loop.run_until_complete(crawler.crawl())  # Crawler gonna crawl.
    except KeyboardInterrupt:
        sys.stderr.flush()
        print('\nInterrupted\n')
    finally:
        reporting.report(crawler)
        crawler.close()

        # next two lines are required for actual aiohttp resource cleanup
        loop.stop()
        loop.run_forever()

        loop.close()


if __name__ == '__main__':
    main()
