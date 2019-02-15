#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''

  srtmanip -- manipulate .srt subtitles

  Author:   SuperOscar Softwares, Tommi Nieminen 2008–19
  License:  GNU General Public License 3.0 or newer

  2019-01-30  0.9.1  A new name and a new structure; all class-specific
                     moved to a module. Replaced backwards- and forwards-
                     moving commands with -m, --move-by. Added -t, --move-to.
                     Added -n, --numbers-from.

'''

import sys
import os
import getopt

# This is just to shorten helper function calls:
from subrip import *

# Constants
version = '0.9.1'
short_opts = 'cf:hm:n:s:t:V'
long_opts = ('check',           # -c
             'from=',           # -f
             'move-by=',        # -m
             'numbers-from='    # -n
             'sync=',           # -s
             'move-to=',        # -t
             'help',            # -h
             'version')         # -V

class ProgramError(Exception):
    pass

def warn(msg):
    '''Print a warning message to stderr.'''
    prgname = os.path.basename(sys.argv[0])
    print('{}: {}'.format(prgname, msg), file=sys.stderr)

def die(msg):
    '''Print a warning message to stderr and quit.'''
    warn(msg)
    sys.exit(1)

def show_info(show_usage=False):
    '''Show help.'''
    global version
    prgname = os.path.basename(sys.argv[0])
    print('{} versio {}'.format(prgname, version))
    if show_usage:
        print('''
Käyttö:

    {} [ KOMENTO|VALITSIMET ] TIEDOSTO ...

Komennot (vain yksi kerrallaan):

    -c, --check                         tarkista tiedoston oikeellisuus
    -m SIIRTYMÄ, --move-by=SIIRTYMÄ     siirrä suhteellisesti
    -s AIKA-AIKA, --sync=AIKA-AIKA      tahdista tekstit aikojen väliin
    -t AIKA, --move-to=AIKA             siirrä absoluuttisesti

    SIIRTYMÄ ja AIKA ovat muotoa "[[00:]00:]00[,000]" (tunnit, minuutit,
    sekunnit ja sekunnin osat).

    Repliikit numeroidaan aina automaattisesti uudelleen. Ilman muita
    komentoja tämä on myös ainoa tehtävä toimenpide.

Valitsimet:

    -f AIKA, --from=AIKA                aloita työ kohdasta AIKA
    -n LUKU, --numbers-from=LUKU        numeroinnin alku
    -h, --help                          näytä tämä ohje ja lopeta
    -V, --version                       näytä versiotiedot ja lopeta
'''.format(prgname))

def init(cmdline, short_opts, long_opts):
    '''Parse the command line.'''
    opts, args = getopt.getopt(cmdline, short_opts, long_opts)
    actions = ''
    settings = {'initial': 1}
    for opt, val in opts:
        if opt in ('-c', '--check'):
            actions += 'c'
        elif opt in ('-f', '--from'):
            settings['from'] = to_secs(val)
        elif opt in ('-m', '--move-by'):
            actions += 'm'
            settings['by'] = to_secs(val)
        elif opt in ('-n', '--numbers-from'):
            settings['initial'] = int(val)
        elif opt in ('-s', '--sync'):
            actions += 's'
            first, last = val.split('-')
            settings['sync'] = (to_secs(first), to_secs(last))
        elif opt in ('-t', '--move-to'):
            actions += 't'
            settings['to'] = to_secs(val)
        elif opt in ('-h', '--help', '-V', '--version'):
            show_info(opt.lstrip('-').startswith('h'))
            sys.exit(0)
    if len(args) > 1:
        raise ProgramError
    return actions, settings, args

try:
    actions, settings, args = init(sys.argv[1:], short_opts, long_opts)
except getopt.GetoptError:
    die('Virhe komentorivillä ("--help" auttaa)')
except ValueError as err:
    die(err)
except ProgramError:
    die('Ristiriitaisia tehtäviä ("--help auttaa")')
if not actions:
    actions = 'n'
if not args:
    die('Ei tekstitystiedostoja ("--help" auttaa)')
elif 'operate-from' in settings and actions != 'm' and actions != 't':
    warn('-f, --from on mieletön, ohitetaan')
for arg in args:
    try:
        subs = SubtextLayer(arg, settings['initial'])
    except FileNotFoundError:
        die('Tiedostoa ei löydy: "{}"'.format(arg))
    except PermissionError:
        die('Ei oikeutta lukea: "{}"'.format(arg))
    except IOError as exc:
        die('Yleinen tiedostovirhe: "{}"'.format(arg))
    except ParseError as exc:
        die('Jäsennysvirhe: "{}", rivi {}'.format(arg, exc.args[0] + 1))
    if actions == 'c':
        msgs = subs.check()
        if msgs:
            print('{}:'.format(arg))
            for entry in sorted(msgs):
                print('#{:04d}: {}'.format(entry, msgs[entry]))
    elif actions == 'm':
        subs.move_by(settings['by'], settings.get('from', 0))
    elif actions == 's':
        first, last = settings['sync']
        subs.sync(first, last)
    elif actions == 't':
        subs.move_to(settings['to'], settings.get('from', 0))
    else:
        # Renumbering is done automatically
        pass
    print(subs)
