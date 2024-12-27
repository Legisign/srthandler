#!/usr/bin/env python3
'''

  srthandler -- classes and methods for SubRip (.srt) handling

  2021-07-18  0.9.5  Utilizing f-strings.
  2021-07-27  0.9.6  More f-strings, enums.
  2024-12-27  1.0    Exceptions renamed, declared 1.0.

'''

import re
import codecs
import enum

version = '1.0'

# HELPER FUNCTIONS

def to_secs(time):
    '''Convert a time string into a float of seconds.

    Time can be in the format [[00]:00:]00[,000] for hours, minutes,
    seconds and parts of seconds. The function raises ValueError if the
    string cannot be converted.
    '''
    # .srt files use a decimal comma (actually, a decimal period works
    # too but let’s standardize here!)
    if isinstance(time, (float, int)):
        return time
    if not isinstance(time, str):
        raise TypeError(f'not a number or string: {time}')
    if time.startswith('-'):
        sign = -1
        time = time[1:]
    else:
        sign = 1
    timepoint = re.compile(r'^(\d+:)?(\d+:)?(\d+[.,]?\d*)$')
    m = timepoint.match(time)
    if not m:
        raise ValueError(f'cannot be parsed as time: {time}')
    while None in m.groups():
        time = '00:' + time
        m = timepoint.match(time)
    to_float = lambda s: float(s.rstrip(':').replace(',', '.'))
    hours, mins, secs = [to_float(p) for p in m.groups()]
    return sign * (hours * 3600 + mins * 60 + secs)

def to_timestr(seconds):
    '''Convert seconds (float) to a time string.

    The resulting string is in the format [[00:]00:]00[,000] for hours,
    minutes, seconds, and parts of seconds.
    '''
    if not isinstance(seconds, (float, int)):
        raise TypeError(f'not a number: {seconds}')
    hrs = f'{int(seconds) // 3600:02d}'
    mins = f'{(int(seconds) % 3600) // 60:02d}'
    secs = f'{(seconds % 60):06.3f}'.replace('.', ',')
    return f'{hrs}:{mins}:{secs}'

# EXCEPTIONS

class ParseError(Exception):
    '''General parse error'''
    def __init__(self, lineno=0):
        self.lineno = lineno

class IndexError(ParseError):
    '''Parse error: subtitle’s index is not a number.'''
    pass

class TimeStampError(ParseError):
    '''Parse error: time line cannot be parsed correctly.'''
    pass

# CLASSES

class ParserState(enum.Enum):
    '''State of the parser.'''
    REC = enum.auto()       # waiting for the record number
    TIME = enum.auto()      # waiting for the timepoint
    TEXT = enum.auto()      # waiting for the text

class Entry(object):
    '''Object holding a single subtitle text.

    Object’s properties are the in-time and out-time the subtitle (in
    seconds), and the subtitle text as a list of strings.'''

    def __init__(self, intime=0, outtime=0, text=None):
        self.intime = to_secs(intime)
        self.outtime = to_secs(outtime)
        self.text = text

    def __repr__(self):
        intime = to_timestr(self.intime)
        outtime = to_timestr(self.outtime)
        text = self.text if self.text else ''
        return f'{intime} --> {outtime}\n{text}'

    @property
    def dur(self):
        '''Return duration of this entry.'''
        return self.outtime - self.intime

    @property
    def intime(self):
        return self.__intime

    @intime.setter
    def intime(self, intime):
        self.__intime = to_secs(intime)

    def move_by(self, offset):
        '''Move subtitle by offset (seconds).'''
        self.intime += to_secs(offset)
        self.outtime += to_secs(offset)

    def move_to(self, pos=0.0):
        '''Move subtitle to pos (seconds).'''
        pos = to_secs(pos)
        curr_dur = self.dur
        self.intime = pos
        self.outtime = pos + curr_dur

    @property
    def outtime(self):
        return self.__outtime

    @outtime.setter
    def outtime(self, outtime):
        self.__outtime = to_secs(outtime)

    @property
    def text(self):
        return '\n'.join(self.__text)

    @text.setter
    def text(self, text):
        if text is None:
            self.__text = []
        elif isinstance(text, str):
            self.__text = [text]
        elif isinstance(text, list):
            self.__text = text
        else:
            raise TypeError(f'invalid type: {text}')

class Subtext(list):
    '''List of Entry objects.'''

    def __init__(self, filename=None, start_from=1):
        self.start_from = start_from
        if filename:
            self.read(filename)

    def __repr__(self):
        return '\n'.join([f'{i + self.start_from}\n{s}\n' \
            for i, s in enumerate(self)])

    def check(self):
        '''A simple check of the correctness of the subtext layer.

        If no errors found, returns empty dict.'''
        log = {}
        for lineno, pair in enumerate(zip(self, self[1:]), 2):
            prev, this = pair
            if this.intime <= prev.intime:
                log[lineno] = 'before or at previous entry'
            if this.dur <= 0:
                log[lineno] = 'duration <= 0'
        return log

    def insert(self, intime=0.0, outtime=0.0, dur=0.0, text=None):
        '''Insert a new record in the layer.'''
        intime = to_secs(intime)
        outtime = to_secs(outtime)
        dur = to_secs(dur)
        # This checks if `outtime` wasn’t given but `dur` was.
        # As they are `float`, checking strict equality is to be avoided.
        if outtime < 0.001 and dur > 0.001:
            outtime = intime + dur
        new = Entry(intime=intime, outtime=outtime, text=text)
        if self == []:
            self.append(new)
        else:
            for i, ref in enumerate(self):
                if ref.intime > intime:
                    break
            super().insert(i, new)
            # Fix overlap instantly
            if ref.outtime > intime:
                ref.outtime = intime

    def move_by(self, offset, start=0.0):
        '''Move the layer by offset (seconds) starting from given time.'''
        offset = to_secs(offset)
        start = to_secs(start)
        for sub in self:
            if sub.intime >= start:
                sub.move_by(offset)

    def move_to(self, pos=0.0, start=0.0):
        '''Move the layer to pos (seconds) starting from given time.'''
        pos = to_secs(pos)
        start = to_secs(start)
        for sub in self:
            if sub.intime >= start:
                offset = pos - sub.intime
                break
        self.move_by(offset, start)

    def parse(self, buff):
        '''Parse buffer as SRT data.'''
        timeline = re.compile('^(?P<intime>\d+:\d+:\d+[,.]\d+)\s+-->\s+'
                              '(?P<outtime>\d+:\d+:\d+[,.]\d+)$')
        state = ParserState.REC
        curr = None
        text = []
        for lineno, line in enumerate(buff, 1):
            line = line.strip()
            if state == ParserState.REC:
                if not line.isnumeric():
                    raise IndexError(lineno)
                curr = Entry()
                state = ParserState.TIME
            elif state == ParserState.TIME:
                m = timeline.match(line)
                if not m:
                    raise TimeStampError(lineno)
                curr.intime = m.group('intime')
                curr.outtime = m.group('outtime')
                state = ParserState.TEXT
            elif state == ParserState.TEXT:
                if line:
                    text.append(line)
                else:
                    curr.text = text
                    self.append(curr)
                    state = ParserState.REC
                    curr = None
                    text = []
        # Handle the last entry
        if curr:
            curr.text = text
            self.append(curr)

    def read(self, filename):
        '''Read given file and forward it to parse().'''
        self.filename = filename
        try:
            # UTF-8 with or without BOM
            with codecs.open(filename, 'r', 'utf_8_sig') as f:
                self.parse(f)
        except UnicodeDecodeError:
            # Latin-9
            with codecs.open(filename, 'r', 'iso8859-15') as f:
                self.parse(f)

    def sync(self, startpoint, endpoint):
        '''Synchronize layer between given timepoints (in seconds).'''
        if isinstance(startpoint, str):
            startpoint = to_secs(startpoint)
        if isinstance(endpoint, str):
            endpoint = to_secs(endpoint)
        assert isinstance(startpoint, (float, int))
        assert isinstance(endpoint, (float, int))
        first, *_, last = self
        first.intime = startpoint
        first.outtime = startpoint + first.dur
        for sub in self[1:]:
            curr_dur = sub.dur
            sub.intime = (endpoint * sub.intime) / last.intime
            sub.outtime = sub.intime + curr_dur

    def write(self, filename=None):
        '''Write the layer to a file.'''
        if not self.filename and filename:
                self.filename = filename
        if not self.filename:
            raise ValueError('Entry.Subtext.write(): no filename')
        with open(self.filename, 'w') as srtfile:
            srtfile.write(str(self))
