---
{
  "id": "POS-011",
  "title": "The remaining action artifacts: reconcile, attach, connect-repo, capture",
  "project": "product-os",
  "status": "next",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "keywords": [
    "reconcile",
    "attach",
    "connect-repo",
    "capture",
    "artifact",
    "paste",
    "action",
    "manual-yaml",
    "repos-json",
    "scale"
  ],
  "evidence": [],
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

<!-- Why this matters. Then ## Acceptance, then ## Handoffs. -->

---

## Handoffs

### 2026-08-19 · work-laptop — three decisions, not tasks

The five action artifacts are built and each passed a cold test. What those
tests left behind is **three things only Marcelo can settle.** They are written
here rather than left in a chat because a decision that lives only in a chat
gets re-derived by every session that follows — this repo's founding failure,
and `DEC-201` exists because it already happened once.

**None of these is a task. Do not "do" any of them.**

#### 1 · `PROP-0003` must not be answered as written

Its headline claims twenty `done` items drop group D from **301 to 13**. The
real effect is **zero**, verified empirically: `audit_item()` returns early for
`done` items, group D excludes only SHAs a *finding* reports, and 0 SHAs are
reported across the six done items in the repo.

The clustering is still good — 288 of 301 commits genuinely fall inside those
globs. The arithmetic and the status are not.

**The decision:** rewrite it with real numbers, or withdraw it. Answering "yes"
as written creates twenty items and changes nothing, which is worse than
leaving group D alone, because it would look like coverage. The correction is
already at the top of the file so a future session cannot miss it. `R-064`.

#### 2 · `BROAD_GLOB_COMMITS = 12` does not scale, and the fix is a taste call

Measured on `genio`, which commits ~6.5×/day: **68 of 572 touched files each
exceed 12 commits on their own** — `server/repository.ts` at 111,
`server/research.ts` at 46. No glob, not even a bare filename, describes that
work in twelve commits or fewer.

So on an active codebase the too-broad check suppresses every honest rule, and
a *live* item can shrink group D by at most 12 no matter how well it is
written. **This blocks connecting more repos**, which is the stated end state.

**The decision is about what counts as honest evidence, which is why it is
his.** The options are not equivalent:

- **Raise or scale the threshold** — cheap, and it weakens the one check that
  stops a rule claiming a whole directory.
- **Make it relative** — a fraction of the repo's commit volume rather than a
  flat count. Harder, and it makes the number mean the same thing across a
  quiet repo and a busy one.
- **Accept coarse attribution on busy repos** and let group D stay large there,
  keeping the check strict where it works.

I have no recommendation I would defend, which is itself the reason to escalate
rather than resolve. `R-064` holds the measurement.

#### 3 · Five closures are still on my judgement alone

`EL-004`, `POS-002`, `POS-003`, `POS-004`, `POS-005` are marked `done` because
a machine decided so. **He has confirmed none of them.**

They are surfaced in three places now — `rank.py --unconfirmed`, `build/now.md`,
and a banner on the face of each brief — so this is visible rather than filed.
Confirming one is a sentence:

```bash
python3 tools/apply.py --decided POS-003=status:done --said "yes, that is done"
```

**The decision is whether to confirm them at all.** Leaving them unconfirmed is
a legitimate answer; the banner is not nagging, it is the record staying honest
about who decided.

**Next:** nothing from me. He uses the tool for real — `/next`, do the work,
`/handoff` — and what he hits is the next requirement, which is not something
either of us would pick.

**Ruled out this session:** `R-063` (a chat URL in a committed file on a public
repo), `R-064` (measuring a proxy instead of the tool's output).

**Reached:** product-os, gimbal-bench, engineered-lighting-site, HomeApp ·
**Could not reach:** `formd-t1` — bench-gated work is unaudited from here, which
is not the same as unchanged.
