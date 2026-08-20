---
{
  "id": "GB-012",
  "title": "Gate L — the fixture joins and holds as a light",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "keywords": [
    "gate-l",
    "zigbee",
    "join",
    "light",
    "soak",
    "drill",
    "ota-drill",
    "led",
    "parked"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/**"
      ],
      "note": "A dated owner-session capture: the fixture joined, held as a light, and the drills each stated what they could not prove."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-015",
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

> **Gate L MET = the fixture joins and holds as a light** (needs the LED path,
> §5).

The radio-live owner session. Two prerequisites are stated by §5 and are
modelled as confirmed edges into this item:

> **Two owner/BoM prerequisites for gate L** [§10 hole 8]: the **LED photometric
> path** (GPIO10/11/18 ledc — "join as a light" cannot be demonstrated as a
> *light* without it; today compile-only), and the **HA-side Zigbee OTA server**
> (Z2M/ZHA OTA provider + image index + the signer→server pipeline — the OTA
> drill presupposes it).

Those are EL-001 and GB-013. Note what that means for priority: **a $205 parts
order with a two-week lead is a hard prerequisite for a gate that is otherwise
pure firmware work.** That is the whole reason `urgency` is in the score.

The drills, each of which must state what it cannot prove: router join/rejoin ·
coordinator-loss · the OTA drill including the c-patch adversary proof · gesture
+ storm simulation · the radio-live soak, *"the first superloop-meets-preemptor
moment"*.
