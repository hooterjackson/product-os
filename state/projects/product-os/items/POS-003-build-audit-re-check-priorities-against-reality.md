---
{
  "id": "POS-003",
  "title": "Build /audit: re-check priorities against reality",
  "project": "product-os",
  "status": "done",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 5,
  "confidence": 4,
  "effort_minutes": 480,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "keywords": [
    "audit",
    "evidence",
    "path-first",
    "attribution",
    "coverage",
    "proposal",
    "acceptance",
    "re-audit",
    "priorities",
    "unattributed"
  ],
  "evidence": [],
  "evidence_found": [
    {
      "kind": "file",
      "repo": "product-os",
      "path": "tools/audit.py",
      "date": "2026-08-19",
      "note": "Read-only. Path-first attribution, four groups, mandatory group D, coverage line by name, rule satisfiability classifier, paginated commit queries."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "tools/apply.py",
      "date": "2026-08-19",
      "note": "One accepted sentence applied. --field/--decided origin split; refuses done without pre-existing evidence."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "plugin/skills/audit/SKILL.md",
      "date": "2026-08-19",
      "note": "The skill: present four groups, read group D, accept in one sentence."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "state/audits/work-laptop/",
      "date": "2026-08-19",
      "note": "Four durable records from real runs, including a refusal."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19",
  "completed": "2026-08-19",
  "closed_origin": "inferred"
}
---

<!-- Why this matters. Then ## Acceptance, then ## Handoffs. -->
