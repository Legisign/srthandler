# srthandler

`srthandler` is a `.srt` (a.k.a SubRip) subtext file handler written in Python. A whole `.srt` file is represented as one `SubtextLayer` object, a `list` consisting of `SubtextEntry` objects.

## Copyleft

Copyright © 2019–2021, Legisign.org, Tommi Nieminen

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## New in version 0.9.6

In addition to internal changes, the public object names were changed. The new names are `Subtext` (was `SubtextLayer`) and `Entry` (was `SubtextEntry`).

## `Subtext`

`Subtext` is a `list` of `Entry` objects.

### Methods

* `check()` -- check integrity of the subtext layer
* `insert()` -- insert a new entry
* `move_by()` -- move given entries by given offset forwards or backwards
* `move_to()` -- move given entries to a given position in time
* `parse()` -- parse string as subtext layer
* `read()` -- read and parse a subtext file
* `sync()` -- tries to synchronize entries between given timepoints
* `write()` -- write a subtext

## `Entry`

`Entry` is an object holding a single subtext frame with its in- and out-times and lines of text (as a list of strings).

### Properties

* `dur` -- duration of entry
* `intime` -- intime of entry
* `outtime` -- outtime of entry
* `text` -- text of entry (as a string)

### Methods

* `move_by()` -- adjust times by offset
* `move_to()` -- set in- and outtimes

## Helper functions

### `to_secs()`

`to_secs(time_string)` converts a string in SubRip time format `[[[dd:]hh:]mm:]ss[,fff]` (days, hours, minutes, seconds, fractions of seconds) into seconds. If called with a numeric value, returns the value.

### `to_timestr()`

`to_timestr(seconds)` converts seconds (`float`) to SubRip time format `[[[dd:]hh:]mm:]ss[,fff]`.
