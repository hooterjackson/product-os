---
{
  "id": "GB-002",
  "title": "Rescue D1-D11 off formd-t1 and commit them",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "content",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "impact": 4,
  "confidence": 5,
  "effort_minutes": 90,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "ledger",
    "d1",
    "d11",
    "decisions",
    "formd-t1",
    "rescue",
    "uncommitted",
    "provenance"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/owner-decisions-*.md",
        "docs/*DECISION*"
      ],
      "note": "A committed file in gimbal-bench carrying D1-D11 in full prose, the way owner-decisions-20260814.md carries D12-D16."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**Eleven owner rulings exist in exactly one place, and it is not a repository.**

D12-D16 are safe: full prose, committed, `e4d71a9`. D1-D11 are not. They survive
only as one-line digests in a section headed:

> # 5. Owner decisions — D1 through D15 exist in §4; D16 exists only by
> reference; no D17–D20

§4 is a section of a planning file under the owner's `.claude/plans/` on
`formd-t1`, read during the 2026-08-15 session and never committed anywhere.
`reader-planV2.md` names the file it was read against in its own header.

So the reasoning behind eleven rulings — every rejected option, every "why not
the obvious thing" — is one disk failure away from being gone, and the digests
that remain are one line each. D11's premise is already known to rest on text
nobody can source (see GB-003).

`gate: none` on purpose: nothing about this needs the bench powered. It needs
the *machine*, which is why `machine_affinity` is set and why the honest answer
from this Mac is "resume on formd-t1", not a plan I cannot execute.

## Acceptance

D1-D11 committed in gimbal-bench in the same shape as D12-D16 — the ruling, the
reasons, the rejected options. A digest table is what we already have and it is
what is failing.
