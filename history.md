# `srthandler` History

## 0.9.5 (2021-07-18)

Utilizing f–strings.

## 0.9.4 (2021-07-15)

Stylistic changes in the parser.

## 0.9.3 (2019-02-27)

Bug fix: to_secs() couldn’t handle negative values unless they were “complete”, meaning had all the parts (hours, minutes and seconds).

## 0.9.2 (2019-02-15)

`text` in `SubtextEntry` is now a `@property` and always looks like a `str` from the user’s point of view; this makes it easier to find text (but also the parser method more complex). All functions that accept time arguments now accept both time strings and numerics. More nuanced parse error exceptions. Bug fix: `SubtextLayer.insert()` only modified a local reference; now it calls `super().insert()` which works.

## 0.9.1 (2019-02-14)

A small stylistic change.

## 0.9.0 (2019-01-30)

Started from older `srtfix` 1.3.1. Added `move_to()` method, renamed `move()` to `move_by()`.
