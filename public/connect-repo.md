# Connect a new repo to product-os

**PASTE THIS INTO AN EXISTING CHAT THAT HAS REPO ACCESS** — it needs
to read the new repo and write to `product-os`. A fresh chat with no
filesystem cannot do either.

---

## 1 · Register it

`state/repos.json` is five keys. Add one entry:

```json
"<repo-name>": {
  "owner": "<github owner, or null if there is no remote>",
  "local": "~/path/to/clone",  // or null if not cloned here
  "default_branch": "main",    // CHECK IT — gimbal-bench uses master
  "authority": false,          // true only if it holds rulings
  "public": false
}
```

Already registered: `HomeApp`, `engineered-lighting-site`, `genio`, `gimbal-bench`, `home-ai-infra`, `product-os`.

No code changes anywhere. `audit.py` iterates whatever is configured.

## 2 · Then model the work, or you have made things worse

**Coverage scales with ITEMS, not repos.** Registering a repo without
items that name its paths does one thing: it grows group D — the
commits no item claims — until the one honest signal in the audit
becomes a number that gets scrolled past.

That number is currently **153**.
 Adding a repo without items makes it bigger, not smaller.

So, in the same sitting:

1. **Read the last ~45 days of its commits** and cluster them by what
   the work actually was — not one item per commit. Aim for a handful
   of items covering most of the volume.
2. **Give each item `evidence` paths specific enough to fire.** Run
   them past the classifier: a glob matching a whole directory
   identifies the subsystem, not the item's work. A glob matching no
   file in the tree can never fire at all.
3. **Propose, do not create.** An item needs `impact`, `confidence`
   and `effort_minutes` to validate and all three are mine. Write
   `state/proposals/PROP-NNNN-<slug>.md` with the full set so I can
   answer in one sentence.
4. **Report the coverage you achieved as a fraction** — commits
   attributable before versus after. And name what you could not
   model rather than inventing items to drive it to zero. A coverage
   figure gamed by fake items is worse than a low one.

## 3 · Verify

```bash
python3 tools/validate.py      # 0 errors
python3 tools/audit.py         # the new repo appears in Coverage
python3 tools/publish.py       # regenerate the public surface
```

The coverage line must name the new repo under **reached** or under
**unreachable**. If it is unreachable, say "I couldn't look" — never
let that render as "no changes".

