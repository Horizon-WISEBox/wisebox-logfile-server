#!/usr/bin/env python3.7

import struct

from datetime import datetime
from pathlib import Path

import netifaces

import pytz

import web

from jsonargparse import ArgumentParser

urls = (
    '/', 'index',
    '/(wp.*)', 'logfile',
)

app_globals = {}

render = web.template.render('templates/', base='base', globals=app_globals)


class index:
    def GET(self):
        d = Path('/var/log/wiseparks-logger')
        log_files = list()
        for f in d.glob('wp*'):
            dt = datetime.strptime(f.stem.replace(
                'wp', ''), '%Y%m%d%H%M%S').replace(tzinfo=pytz.UTC)
            log_files.append((f.name, dt, f.suffix.replace('.', '')))
        return render.index(log_files=log_files)


class logfile:
    def GET(self, filename):
        f = Path('/var/log/wiseparks-logger', filename)
        startdate = datetime.strptime(f.stem.replace(
            'wp', ''), '%Y%m%d%H%M%S').replace(tzinfo=pytz.UTC)
        entries = list()
        with f.open('rb') as bf:
            buf = bf.read()
        i = 0
        while i < len(buf):
            (a, b) = struct.unpack_from('<iH', buf, i)
            st = datetime.fromtimestamp(a, tz=pytz.UTC)
            i += 6
            j = i + b
            rssis = []
            while i < j:
                (rssi, ) = struct.unpack_from('<b', buf, i)
                i += 1
                rssis.append(rssi)
            entries.append((st, b, rssis))
        return render.logfile(
            startdate=startdate,
            status=f.suffix.replace('.', ''),
            entries=entries)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('interface', type=str)
    cfg = parser.parse_path(
        '/etc/wiseparks/wiseparks-logger.yaml',
        _skip_check=True)
    try:
        iface = netifaces.ifaddresses(cfg.interface)
        app_globals['DEVICE_ID'] = iface[netifaces.AF_LINK][0]['addr']
    except KeyError:
        app_globals['DEVICE_ID'] = 'Unknown'
    app = web.application(urls, globals())
    app.run()
