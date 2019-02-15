# History

## subrip

### 2019-02-15, version 0.9.2

‘text’ in SubtextEntry is now a @property and always looks like a string from the user’s point of view; this makes it easier to find text (but also the parser method more complex). All functions that accept time arguments now accept both time strings and numerics. More nuanced parse error exceptions. Bug fix: SubtextLayer.insert() only modified a local reference; now it calls super().insert() which works.

### 2019-02-14, version 0.9.1

A small stylistic change.

###  2019-01-30, version 0.9.0

Started from srtfix 1.3.1. Added move_to() method, renamed move() to move_by().

## submanip

### 2019-01-30, version 0.9.1

A new name and a new structure; all class-specific moved to a module. Replaced backwards- and forwards-moving commands with -m, --move-by. Added -t, --move-to. Added -n, --numbers-from.
