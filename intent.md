---
{
  "provisional": true,
  "updated": "2026-08-18"
}
---

<!--
  PROVISIONAL. Claude drafted this on 2026-08-18 from your repos, docs and ledgers.
  It is a reading of your intent, not a statement of it.

  Rewrite it in your own words and set "provisional": false. Until you do, every
  proposal that cites this file will say out loud that it is citing a guess.
  The nag is deliberate.
-->

# Intent

I am building one thing: **a silent, high-CRI robotic spotlight that behaves like an
ordinary light** — a pan/tilt head on CAN servos, exposed to Home Assistant as plain
entities, that can also aim itself. Everything else in this portfolio either serves
that or is a tool I need in order to build it.

The fixture goes on a ceiling. It has no brake — de-energised, the head falls — and
once installed there is no power switch and no console. That single fact outranks
schedule, elegance and scope. **Whatever else fails, it stays a light.**

## What I actually value

**Evidence over assertion.** A claim without a measurement, a SHA or a capture behind
it is a guess wearing a fact's clothes. I would rather be told "I couldn't look" than
be told "no changes."

**Negative results.** The expensive knowledge is what *didn't* work. Six invented hole
positions made every part 11% oversized; a render showed a cradle as a clean solid
when its bolt holes overlapped nothing. Those cost real hours and they die with the
chat that found them unless someone writes them down.

**Adversarial review.** I overturn my own rulings when a review earns it, same day if
necessary. A tool that only ever agrees with me is a tool I stop believing.

## Order of precedence when things compete

1. Safety of the installed fixture.
2. A ruling in the engineering repo. Published docs are narrative; they never override
   a ruling or current bench evidence.
3. What unblocks the most downstream work.
4. What is cheapest to reverse.

## Not doing

Shipping to strangers — that changes the security answer, and I'll know when it's
time. Zoom hardware. A second control surface beside Home Assistant. Anything that
makes the light depend on a hub to be a light.

## How to talk to me

Tell me the thing, then the reasoning. If you think I'm wrong, say so once, plainly,
and then do what I asked. If it's going badly, tell me it's going badly.
