#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
# pylint: disable=W0702

import sys
import os
import logging
import feedparser
import requests
import transmissionrpc

from config import *

addedfile = os.path.join(
    os.path.abspath(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ), fpath['added']
)

filteredfile = os.path.join(
    os.path.abspath(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ), fpath['filtered']
)

logfile = os.path.join(
    os.path.abspath(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ), fpath['log']
)


def read_addeditems():
    """ read already added torrent """
    addeditems = []
    if os.path.exists(addedfile):
        with open(addedfile, 'r') as items:
            for line in items:
                addeditems.append(line.rstrip('\n'))
    return addeditems


def read_filtereditems():
    """ read names that shold be added """
    filtereditems = []
    if os.path.exists(filteredfile):
        with open(filteredfile, 'r') as items:
            for line in items:
                filtereditems.append(line.rstrip('\n'))
    return filtereditems


def pushover_notify(msg):
    """ notify by pushover """
    payload = {
        'token': pushover['token'],
        'user': pushover['user'],
        'message': msg
    }

    req = requests.post(
        pushover['url'],
        params=payload
        )
    logging.info("Pushover response: " + req.text)
    return


def download_item(url):
    """ download torrent """
    filename = url.split('/')[-1]
    filename = os.path.join(
        os.path.abspath(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ), filename
    )

    req = requests.get(url)
    with open(filename, 'wb') as out_file:
        out_file.write(req.content)
    return filename


def add_item(item):
    """ add item to queue """
    logging.info("Adding Torrent: " + item.title + " (" + item.link + ")")
    file = download_item(item.link)
    __tc__.add_torrent('file://' + file)
    pushover_notify(item.title)
    with open(addedfile, 'a') as out_file:
        out_file.write(item.link + '\n')
    return


def parse_feed(feed_url):
    """ parse feed """
    feed = feedparser.parse(feed_url)
    if feed.bozo and feed.bozo_exception:
        logging.error(
            "Error reading feed \'{0}\': ".format(feed_url) +
            str(feed.bozo_exception).strip()
            )
        return

    addeditems = read_addeditems()
    filtereditems = read_filtereditems()

    for item in feed.entries:
        # item.title
        # item.link
        # item.comments
        # item.pubDate
        # logging.info("Found Torrent: " + item.title + " (" + item.link + ")")
        itemname = item.title.split(' / ')[0]
        if (item.link not in addeditems) and (itemname in filtereditems):
            try:
                add_item(item)
            except:
                logging.error(
                    "Error adding item \'{0}\': ".format(item.link) +
                    str(sys.exc_info()[0]).strip()
                    )
    return

if __name__ == "__main__":

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s]: %(message)s',
        level=logging.DEBUG,
        filename=logfile
    )

    try:
        __tc__ = transmissionrpc.Client(
            transmission['host'],
            transmission['port'],
            transmission['user'],
            transmission['password']
            )
    except transmissionrpc.error.TransmissionError as trpc_exc:
        logging.error("Error connecting to Transmission: " +
                      str(trpc_exc).strip())
        exit(0)
    except:
        logging.error("Error connecting to Transmission: " +
                      str(sys.exc_info()[0]).strip())
        exit(0)

    parse_feed(feed['url'])

