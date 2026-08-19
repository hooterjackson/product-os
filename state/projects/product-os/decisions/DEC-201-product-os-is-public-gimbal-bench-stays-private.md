---
{
  "id": "DEC-201",
  "title": "product-os is public; gimbal-bench stays private",
  "project": "product-os",
  "status": "done",
  "ruling_id": "M1",
  "decided": "2026-08-19",
  "revisit_if": "A future register entry would publish a credential, an identifier, or a third party's information. Then this decision is reopened before that entry is committed, not after.",
  "supersedes": [
    "R-050"
  ],
  "superseded_by": null,
  "propagates_to": [],
  "keywords": [
    "public",
    "private",
    "visibility",
    "disclosure",
    "publication",
    "gimbal-bench",
    "product-os",
    "ruled-out",
    "third-party",
    "settled"
  ],
  "evidence": [
    {
      "repo": "product-os",
      "path": "wiki/ruled-out.md",
      "sha": null,
      "date": "2026-08-19",
      "note": "The content in question: 59 entries, ~84 verbatim quoted lines, paths and SHAs derived from the private gimbal-bench."
    },
    {
      "repo": "product-os",
      "path": "tools/validate.py",
      "sha": null,
      "date": "2026-08-19",
      "note": "The disclosure screen that finds no credential, email, tailnet identifier or MAC in any of it."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**Decided by Marcelo, 2026-08-19, in his own words:**

> product-os is public by my decision on 2026-08-19, including wiki/ruled-out.md
> and the ~84 verbatim lines, paths and SHAs derived from the private
> gimbal-bench. The disclosure screen finds no credential, email, tailnet
> identifier or MAC. gimbal-bench itself stays PRIVATE, for one reason only: a
> capture names a third party's personal email beside a tailnet incident, and
> that is not mine to publish on their behalf. Do not re-raise the product-os
> visibility question.

## Why this is a decision record and not a note

It kept coming back. `grep -ril public state/decisions/` returned **nothing**,
and it was raised in three consecutive recaps — each time re-derived from
scratch, each time reaching the same place, each time costing a paragraph.

That is this repository's founding failure happening **to this repository**: a
decision that lives only in a chat gets re-derived by every session that
follows. `PROJECT-STATE.md` listing two prompts as pending that had already
shipped is the same shape. The fix is the one this repo exists to apply — write
it down where the next session reads it.

## What this supersedes

`R-050` recommended product-os start private, for exactly this content. That
recommendation was reasonable and it is now **overtaken**. The register entry
stays as the record of the reasoning; this ruling is what governs.

## The two halves are decided on different grounds, and that matters

- **product-os public** — a judgement about engineering disclosure, made with
  the screen's result in hand. Reversible in one command if the calculus
  changes, which is what `revisit_if` is for.
- **gimbal-bench private** — *not* a judgement about engineering disclosure at
  all. One reason only: a third party's personal address sits beside an incident
  on their network, with no indication they were told. That is not reversible
  and not his to publish on someone else's behalf. `R-049` holds the detail and
  the pre-flip checklist.

Conflating those two would be the error. The first is a preference; the second
is somebody else's.

## Not a gag

`revisit_if` is real. If a register entry would publish a credential, an
identifier, or a third party's information, this decision reopens **before that
entry is committed** — not after it is public. The screen in `validate.py` is
the mechanical half of that trigger; a person noticing is the other half.

Short of that: **stop reporting it.**
