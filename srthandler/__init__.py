#!/usr/bin/env python3
'''

  srthandler -- classes and methods for SubRip (.srt) handling

  2021-07-18  0.9.5  Utilizing f-strings.

'''

import re
import codecs

version = '0.9.5'

# HELPER FUNCTIONS

def to_secs(time):
    '''Convert a time string into a float of seconds.

    Time can be in the format [[00]:00:]00[,000] for hours, minutes,
    seconds and parts of seconds. The function raises ValueError if the
    string cannot be converted.
    '''
    # .srt files use a decimal comma (actually, a decimal period works
    # too but let’s standardize here!)
    if time.startswith('-'):
        sign = -1
        time = time[1:]
    else:
        sign = 1
    timepoint = re.compile(r'^(\d+:)?(\d+:)?(\d+[.,]?\d*)$')
    m = timepoint.match(time)
    if not m:
        raise ValueError
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
    hrs = f'{seconds // 3600:02d}'
    mins = f'{(seconds % 3600) // 60}:02d'
    secs = f'{(seconds % 60):06.3f}'.replace('.', ',')
    # # Python cannot zero-pad floats!
    # if secs.index(',') == 1:
    #     secs = '0' + secs
    return f'{hrs}:{mins}:{secs}'

# EXCEPTIONS

class ParseError(Exception):
    '''General parse error'''
    pass

class IndexLineError(ParseError):
    '''Parse error: subtitle’s index is not a number.'''
    pass

class TimeLineError(ParseError):
    '''Parse error: time line cannot be parsed correctly.'''
    pass

# CLASSES

class SubtextEntry(object):
    '''Object holding a single subtitle text.

    Object’s properties are the in-time and out-time the subtitle (in
    seconds), and the subtitle text as a list of strings.'''

    def __init__(self, intime=0.0, outtime=0.0, text=None):
        self.intime = intime
        self.outtime = outtime
        self.text = text

    def __str__(self):
        return f'{to_timestr(self.intime)} --> {to_timestr(self.outtime)}\n{self.text}'

    @property
    def dur(self):
        '''Return duration of this entry.'''
        return self.outtime - self.intime

    @property
    def intime(self):
        return self.__intime

    @intime.setter
    def intime(self, intime):
        if isinstance(intime, (int, float)):
            self.__intime = intime
        elif isinstance(intime, str):
            self.__intime = to_secs(intime)
        else:
            raise TypeError(intime)

    def move_by(self, offset):
        '''Move subtitle by offset (seconds).'''
        if isinstance(offset, str):
            offset = to_secs(offset)
        self.intime += offset
        self.outtime += offset

    def move_to(self, pos=0.0):
        '''Move subtitle to pos (seconds).'''
        if isinstance(pos, str):
            pos = to_secs(pos)
        dur = self.dur
        self.intime = pos
        self.outtime = pos + dur

    @property
    def outtime(self):
        return self.__outtime

    @outtime.setter
    def outtime(self, outtime):
        if isinstance(outtime, (int, float)):
            self.__outtime = outtime
        elif isinstance(outtime, str):
            self.__outtime = to_secs(outtime)
        else:
            raise TypeError(outtime)

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
            raise TypeError(text)

class SubtextLayer(list):
    '''List of SubtextEntry objects.'''

    def __init__(self, filename=None, start_from=1):
        self.start_from = start_from
        if filename:
            self.read(filename)

    def __str__(self):
        return '\n'.join(['{}\n{}\n'.format(i + self.start_from, str(s)) \
            for i, s in enumerate(self)])

    def check(self):
        '''A simple check of the correctness of the subtext layer.'''
        log = {}
        for no, pair in enumerate(zip(self, self[1:])):
            prev, this = pair
            if this.intime <= prev.intime:
                log[no + 2] = 'before or at previous entry'
            if this.dur <= 0:
                log[no + 2] = 'duration <= 0'
        return log

    def insert(self, intime=0.0, outtime=0.0, dur=0.0, text=None):
        '''Insert a new record in the layer.'''
        if isinstance(intime, str):
            intime = to_secs(intime)
        if isinstance(outtime, str):
            outtime = to_secs(outtime)
        if isinstance(dur, str):
            dur = to_secs(dur)
        if outtime < 0.001 and dur > 0.001:
            outtime = intime + dur
        new = SubtextEntry(intime, outtime, text)
        if self == []:
            self.append(new)
        elif self[-1].intime < intime:
            # Fix overlapping instantly
            if self[-1].outtime > intime:
                self[-1].outtime = intime
            self.append(new)
        else:
            for i, ref in enumerate(self):
                if ref.intime > intime:
                    break
            super().insert(i, new)
            # Fix overlaps instantly
            if ref.outtime > intime:
                ref.outtime = intime

    def move_by(self, offset, start=0.0):
        '''Move the layer by offset (seconds) starting from given time.'''
        if isinstance(offset, str):
            offset = to_secs(offset)
        if isinstance(start, str):
            start = to_secs(start)
        for sub in self:
            if sub.intime >= start:
                sub.move_by(offset)

    def move_to(self, pos=0.0, start=0.0):
        '''Move the layer to pos (seconds) starting from given time.'''
        if isinstance(pos, str):
            pos = to_secs(pos)
        if isinstance(start, str):
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
        # State can be one of the following:
        #   rec# : waiting for record #
        #   time : waiting for timepoint
        #   text : waiting for actual content
        state = 'rec#'
        curr = None
        text = []
        for lineno, line in enumerate(buff):
            line = line.strip()
            if state == 'rec#':
                if not line.isnumeric():
                    raise IndexLineError(lineno)
                curr = SubtextEntry()
                state = 'time'
            elif state == 'time':
                m = timeline.match(line)
                if not m:
                    raise TimeLineError(lineno)
                curr.intime = m.group('intime')
                curr.outtime = m.group('outtime')
                state = 'text'
            elif state == 'text':
                if not line:
                    if text:
                        curr.text = text
                        text = []
                    self.append(curr)
                    state = 'rec#'
                    curr = None
                else:
                    text.append(line)
        # Handle the last entry
        if curr:
            if text:
                curr.text = text
            self.append(curr)

    def read(self, filename):
        '''Read given file and forward it to parse().'''
        self.filename = filename
        try:
            # UTF-8 with (or without) BOM
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
        first, *_, last = self
        first.intime = startpoint
        first.outtime = startpoint + first.dur
        for sub in self[1:]:
            dur = sub.dur
            sub.intime = (endpoint * sub.intime) / last.intime
            sub.outtime = sub.intime + dur

    def write(self, filename=None):
        '''Write the layer to a file.'''
        if not self.filename:
            if filename:
                self.filename = filename
            else:
                raise ValueError(self.filename)
        with open(self.filename, 'w') as srtfile:
            srtfile.write(str(self))
