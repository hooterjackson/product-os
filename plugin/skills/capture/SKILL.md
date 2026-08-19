---
name: capture
description: Write a raw thought into the product-os inbox. Use when the user says /capture, or says something like "capture that", "note that down", "remember this for later" while working on something else. Takes the words verbatim and asks nothing.
---

# capture

Write the user's words into `state/inbox/` and stop.

```bash
python3 tools/new.py capture "<the user's words, verbatim>"
```

Print the path the command returns. Say nothing else.

## Ask nothing

**If capture asks a question, capture is broken.** No project. No priority. No
"should I file this as an item?". No clarifying what they meant. No tidying the
grammar.

The whole value of a capture is that it costs nothing at the moment of having
the thought — the user is mid-way through something else, and every question you
ask is a reason not to bother next time. Triage does all of that later, in
batch, when they have chosen to do triage.

## Verbatim means verbatim

Pass the words through unchanged, including the swearing, the half-sentences and
the shorthand. `tools/new.py` stamps the time, the machine and the working
directory around them; the body is theirs.

Do not expand an abbreviation. Do not resolve a pronoun. Do not "clean it up".
A capture that has been improved is a capture the user cannot recognise in three
weeks, and recognising it is the entire job.

## The one exception

If the text is empty, `new.py` exits 2 and says `nothing to capture`. Report
that and stop. Do not invent something to capture.
