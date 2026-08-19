---
{
  "slug": "robotic-spotlight",
  "name": "Robotic spotlight",
  "prefix": "EL",
  "north_star": "A silent, high-CRI pan/tilt head on CAN servos that behaves like an ordinary light and can also aim itself.",
  "phase": "bench proven; LED head unordered",
  "repos": [
    "gimbal-bench",
    "engineered-lighting-site"
  ],
  "decision_authority": "gimbal-bench",
  "may_rule": false,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

The fixture itself: the mechanical head, the motors, the LED payload and the
parts that have to arrive in the mail before anything else can happen.

Both motors were proven answering on CAN on 2026-08-15 (EL-005). The LED head is
the open front: Doc 4's BoM is unordered, and the Zigbee phase's own plan says
gate L cannot be demonstrated without it.

This project holds no rulings. Rulings live in `gimbal-bench`.
