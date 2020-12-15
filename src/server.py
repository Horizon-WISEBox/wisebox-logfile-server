#!/usr/bin/env python3.7

import io
import os
import struct
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Union

import netifaces
import pytz
import web
from jsonargparse import ActionConfigFile, ArgumentParser

VERSION = '1.0.1'
DESCRIPTION = 'Simple server for display of WISEBox log files'

urls = (
    '/', 'Index',
    '/download', 'Download',
    '/(wp.*)', 'Logfile',
)

app_globals = {}

render = web.template.render('templates/', base='base', globals=app_globals)


class ExtArgumentParser(ArgumentParser):

    def check_config(
            self,
            cfg: Union[SimpleNamespace, dict],
            skip_none: bool = True,
            branch=None):
        import jsonargparse as ap
        cfg = ccfg = ap.deepcopy(cfg)
        if not isinstance(cfg, dict):
            cfg = ap.namespace_to_dict(cfg)
        if isinstance(branch, str):
            cfg = ap._flat_namespace_to_dict(
                ap._dict_to_flat_namespace({branch: cfg}))

        def get_key_value(dct, key):
            keys = key.split('.')
            for key in keys:
                dct = dct[key]
            return dct

        def check_required(cfg):
            for reqkey in self.required_args:
                try:
                    val = get_key_value(cfg, reqkey)
                    if val is None:
                        raise TypeError(f'Required key "{reqkey}" is None.')
                except:
                    raise TypeError(
                        f'Required key "{reqkey}" not included in config.')

        def check_values(cfg, base=None):
            subcommand = None
            for key, val in cfg.items():
                if key in ap.meta_keys:
                    continue
                kbase = key if base is None else base+'.'+key
                action = ap._find_action(self, kbase)
                if action is not None:
                    if val is None and skip_none:
                        continue
                    self._check_value_key(action, val, kbase, ccfg)
                    if (isinstance(action, ap.ActionSubCommands)
                            and kbase != action.dest):
                        if subcommand is not None:
                            raise KeyError(
                                f'Only values from a single sub-command '
                                f'are allowed ("{subcommand}", "{kbase}).')
                        subcommand = kbase
                elif isinstance(val, dict):
                    check_values(val, kbase)
                else:
                    pass

        try:
            check_required(cfg)
            check_values(cfg)
        except Exception as ex:
            self.error(f'Config checking failed :: {ex}')


class Index:
    def GET(self):
        d = Path(app_globals['CONFIG'].log.dir)
        log_files = list()
        for f in d.glob('wp*'):
            dt = datetime.strptime(f.stem.replace(
                'wp', ''), '%Y%m%d%H%M%S').replace(tzinfo=pytz.UTC)
            log_files.append((f.name, dt, f.suffix.replace('.', '')))
        return render.index(log_files=log_files)


class Download:
    def GET(self):
        web.header(
            'Content-Disposition', 'attachment; filename="wisebox.zip"')
        web.header('Content-type', 'application/zip')
        web.header('Content-transfer-encoding', 'binary')
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode='w') as zip_file:
            d = Path(app_globals['CONFIG'].log.dir)
            for f in d.glob('wp*'):
                zip_file.write(f, arcname=f.name)
        return zip_buf.getvalue()


class Logfile:

    def decode_head(self, i, buf):
        ENCODING = 'utf_8'
        header = dict()
        header['logfile_version'] = struct.unpack_from('<H', buf, i)[0]
        i += 2
        mac_bytes = struct.unpack_from('<BBBBBB', buf, i)
        header['mac'] = ':'.join([f'{x:02x}' for x in mac_bytes])
        i += 6
        header['interval'] = struct.unpack_from('<I', buf, i)[0]
        i += 4
        tz_len = struct.unpack_from('<B', buf, i)[0]
        i += 1
        header['timezone'] = buf[i:i+tz_len].decode(ENCODING)
        i += tz_len
        metadata_len = struct.unpack_from('<I', buf, i)[0]
        i += 4
        metadata = buf[i:i+metadata_len].decode(ENCODING)
        i += metadata_len
        header['metadata'] = metadata
        return i, header

    def decode_body(self, i, buf):
        entries = list()
        while i < len(buf):
            (a, b, c) = struct.unpack_from('<iHH', buf, i)
            st = datetime.fromtimestamp(a, tz=pytz.UTC)
            i += 8
            j = i + c
            rssis = []
            while i < j:
                (rssi, ) = struct.unpack_from('<b', buf, i)
                i += 1
                rssis.append(rssi)
            entries.append((st, b, c, rssis))
        return i, entries

    def GET(self, filename):
        f = Path(app_globals['CONFIG'].log.dir, filename)
        startdate = datetime.strptime(f.stem.replace(
            'wp', ''), '%Y%m%d%H%M%S').replace(tzinfo=pytz.UTC)
        with f.open('rb') as bf:
            buf = bf.read()
        i = 0
        i, header = self.decode_head(i, buf)
        i, entries = self.decode_body(i, buf)
        return render.logfile(
            startdate=startdate,
            status=f.suffix.replace('.', ''),
            entries=entries,
            header=header)


def main():
    app_name = Path(sys.argv[0]).stem

    parser = ExtArgumentParser(
        prog=app_name,
        default_config_files=[],
        description=DESCRIPTION,
        error_handler='usage_and_exit_error_handler')

    parser.add_argument(
        'interface',
        type=str,
        help='capture interface, e.g. wlan0')
    parser.add_argument(
        'log.dir',
        type=str,
        help='directory to write logs to')
    parser.add_argument('--config', action=ActionConfigFile)
    parser.add_argument(
        '--version',
        action='version',
        version=f'{app_name} version {VERSION}')

    cfg = parser.parse_args()
    app_globals['CONFIG'] = cfg

    try:
        iface = netifaces.ifaddresses(cfg.interface)
        app_globals['DEVICE_ID'] = iface[netifaces.AF_LINK][0]['addr']
    except KeyError:
        app_globals['DEVICE_ID'] = 'Unknown'
    app_globals['VERSION'] = VERSION
    app = web.application(urls, globals())
    app.run()


if __name__ == "__main__":
    main()
