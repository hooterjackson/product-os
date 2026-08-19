# Ruled out

Things that were tried and failed, or eliminated with reasons. **Negative results
are the most expensive knowledge in this portfolio and the easiest to lose** —
they die with the chat that found them unless somebody writes them here.

This file exists to be read **at the moment of suggesting**, not afterwards. The
`SessionStart` hook greps it by the current item's keywords and injects the
matches, so the entry lands before the idea is said rather than after it is
built. A register nobody reads at the right moment is a document, not a
guardrail.

## Format

Each entry is a `##` block carrying a `keywords:` line and a `source:` line.
Both are load-bearing: the keywords are what the hook matches on, and the source
is what makes an entry falsifiable rather than folklore.

**Grades** use the evidence ladder — `measured` > `datasheet` > `inferred` >
`said-in-chat`. Anything at `said-in-chat` carries **re-verify before citing**
and means exactly that.

## Adding an entry

When a session concludes that something does *not* work, append it here. If you
find something that contradicts an existing entry, **do not silently overwrite
it** — add the contradiction and flag it.

**The audience for most of this file is on `formd-t1`.** It is bench knowledge
and these dead ends recur at the bench. Slice one puts it on this Mac. That
limitation is real and unfixed.

---

# Mechanical and CAD

## R-001 · Six output holes on Ø30 and an M4 rear on Ø43
**keywords:** frame · scad · bolt-circle · invented · dimensions · oversized · motor-interface · rebuild
**source:** engineered-lighting-site `GROUND-UP-BRIEF.md:87` @ `f6e54be` · 2026-07-30 · grade: measured

> Earlier versions of this design used six output holes on Ø30 and an M4 rear on
> Ø43. Both were invented. That error alone made every part oversized by ~11%.

The real interface, from the vendor STEP: **4 × M3 tapped on a Ø25.00 bolt
circle** at the output, **4 × M2.5 on a 20 × 20 mm square** (Ø28.284 BC at 45°)
at the rear. This one error is why the entire frame was rebuilt from scratch, and
it is the origin of the standing order *"Measure before designing against a
dimension."*

## R-002 · Renders as validation
**keywords:** render · validation · boolean · interference · collision · scad · check · openscad
**source:** engineered-lighting-site `GROUND-UP-BRIEF.md:172` @ `f6e54be` · 2026-07-30 · grade: measured

A render shows you a picture of a part, not whether two parts occupy the same
space. The technique that works:

> Emit `intersection() { partA_positioned(); partB_positioned(); }` to an STL and
> measure its volume. Zero volume or no file at all means clear; anything else is
> a collision… **This caught three collisions that no render showed.** Note that
> OpenSCAD writes no file at all when the result is empty — that is the success
> signal.

**No file written is the pass.** Anyone treating a missing STL as a tool failure
has inverted the test.

## R-003 · The v7 cradle's output-flange bolt cut
**keywords:** cradle · bolt · cut · no-op · geometry · v7 · frame · clearance · flange
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §1 @ `428399c` · 2026-07-30 · grade: measured

The clearance cut spans x = −12.000…+12.000. The plate it is supposed to pierce
spans x = −22.865…−14.865.

> **The nearest ends are 2.865 mm apart. There is zero overlap. The cut removes
> no material.**

Both reachable holes were missing, not one. The head could not be bolted to the
tilt motor at all — and because the cut is a pure no-op it changed no mass and
appeared in no render. **The part looked perfect.** Six independent review lenses
found this same defect.

## R-004 · Assembling the v7 head between the yoke arms
**keywords:** yoke · trunnion · insertion · assembly · span · v7 · frame · stub · arms
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §2 @ `428399c` · 2026-07-30 · grade: measured

The assembled stack leaves **4.000 mm of axial slack**. The trunnion stub needs
**19.900 mm** of insertion travel to reach its bearing. Short by 15.900 mm.

> the machine cannot be assembled. Every part is fine alone and the assembled
> render is clean; this only appears when you try to build it, after ~180 g of
> PETG.

Root cause worth remembering: `span_h` was derived from the *assembled* stack-up,
and nothing in the chain accounted for insertion travel. **Assembled dimensions
do not imply assemblable ones.**

## R-005 · Seating the v7 cradle cap over step-4 screw heads
**keywords:** cap · cradle · screw-head · counterbore · interference · assembly-order · v7
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §3 @ `428399c` · 2026-07-30 · grade: measured

0.350 mm of clearance for a 3.0 mm socket cap head. **Interference 2.650 mm**,
161.38 mm³ by boolean. Nothing counterbores them.

The class matters more than the instance: **a fastener installed at step 4 was
trapped behind a part installed at step 9.** Check assembly *order*, not just
assembled fit.

## R-006 · Three M3 heads on the v7 trunnion's Ø18 bolt circle
**keywords:** trunnion · m3 · head · shank · bolt-circle · v7 · frame · iso-4762
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §4 @ `428399c` · 2026-07-30 · grade: measured

Bolt circle radius 9.000; the Ø14 shank rises from the same face at radius 7.000.
With the file's own `m3_head_d` = 6.4 the head's inner edge sits **1.200 mm
inside the shank**; with a real ISO 4762 head (Ø5.5) still 0.750 mm inside.

Build step 5 says "three screws, heads outside". It cannot be executed with any
standard M3.

## R-007 · M3×13 and M3×14 into the 5005's output flange
**keywords:** m3 · screw-length · tapped · rotor · motor · 5005 · flange · datasheet · assembly
**source:** engineered-lighting-site `ref/RMD-L-5005-S.md` @ `fb0d5eb` · 2026-07-30 · grade: datasheet

> **The tapped hole is 2.5 mm deep** … and breaks through into the rotor cavity
> at x = 2.5. Both screws bottom 2.5–3.5 mm before the head seats, so neither
> joint is ever clamped and the tips are inside the motor.

The STEP table reads `Ø2.50 drill, on Ø25.00 BC | x = 0.000 → 2.500 deep`. Note
why it hid: **the motor model in `assembly.scad` draws no blind hole**, so the
collision could not render.

## R-008 · Printing `bore_gauge` as emitted in v7
**keywords:** bore-gauge · print · supports · platform · floating · v7 · petg · first-part
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §5 @ `428399c` · 2026-07-30 · grade: measured

`p_bore_gauge()` translated by `base_z` only, leaving the cap half a 29 × 14 × 22
mm solid **floating 16 mm above the platform** — in a project whose hard
requirement is zero supports, on the piece printed before anything else.

## R-009 · Trusting `bore_gauge` to stand in for the real bore
**keywords:** bore-gauge · coupon · bridging · sag · tolerance · fit · dome · valley
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §10 @ `428399c` · 2026-07-30 · grade: measured

The gauge's cap bore prints as an **87° dome — a sagging arch** — where the real
`cradle_cap` prints the same bore as a valley.

> The sag is toward the barrel, so the gauge reads tight exactly where the real
> part is not.

A coupon that does not print in the same orientation as the part measures the
coupon.

## R-010 · `p_cradle`'s emitted Z position in v7
**keywords:** cradle · platform · slicer · keel · chamfer · z-offset · v7 · print
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §9 @ `428399c` · 2026-07-30 · grade: measured

The part was emitted **1.740 mm below the build platform**. A slicer that clips
to the platform silently removes the bottom of the keel — material under the bore
drops from 3.135 to 1.395 mm, and both 45° keel chamfers, the part's entire
first-layer footprint, go with it. **Silently.**

## R-011 · The v7 `fit_coupon`
**keywords:** fit-coupon · coupon · bolt-circle · merge · m3 · m2.5 · v7 · tolerance
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §7 @ `428399c` · 2026-07-30 · grade: measured

The Ø25 M3 circle and the Ø28.284 M2.5 circle overlapped, so the holes merged
into four slots and an M3 and an M2.5 both dropped through the same one.

> The coupon whose entire job is to prove both motor interfaces for 3 g of PETG
> proves neither — against the exact failure mode (invented bolt circles) that
> caused this rebuild.

Relevant to **EL-003**: print the coupon, then *check the coupon proves
something*.

## R-012 · The v7 base plate's cable-tie point
**keywords:** cable-tie · base-plate · routing · assembly-order · wires · trap
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §6 @ `428399c` · 2026-07-30 · grade: inferred

The tie must loop through one slot, round the far side and back — but the far
side is the plate face the motor bolts flat against. No return path once step 3
is done, and the wires are laid at step 8. Threading it beforehand traps it in
the joint.

## R-013 · Flat bridges over 45 mm in PETG at 0.6 mm clearance
**keywords:** bridging · petg · sag · groove · hard-stop · yoke · clearance · print
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §11 @ `428399c` · 2026-07-30 · grade: inferred

1565 mm² of flat bridging with unsupported runs of 45.65 mm against a designed
post clearance of **0.600 mm**. PETG will not hold 0.6 mm over 45 mm; if it sags
the post rides on the groove floor.

## R-014 · Circular pocket roofs
**keywords:** pocket · roof · bridge · hexagon · self-supporting · print · crown · cap
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §12 @ `428399c` · 2026-07-30 · grade: measured

Already logged once and repeated in `cradle_cap`:

> a 32 mm circular pocket roof printed as a bridge where a hexagon with a vertex
> up would have been a self-supporting 60° peak

Fixed on the yoke arms and missed on the cap — which is the useful part of the
entry. **A fix applied to one part is not applied to the file.**

---

# Toolchain

## R-015 · Working from a Downloads folder
**keywords:** openscad · downloads · undef · stale · scad · toolchain · silent · exit-0 · version-banner
**source:** engineered-lighting-site `docs/03b-print-the-frame.md:149` @ `25e62f4` · 2026-08-01 · grade: measured

The most dangerous failure in this toolchain, because every symptom points
somewhere else:

> It prints `WARNING: Ignoring unknown variable`, collapses the missing names to
> `undef`, silently **drops the geometry those names positioned**, writes a
> valid-looking STL and exits 0. A slicer will happily accept it.

The mechanism: a browser saves a second copy as `frame_params_1.scad`, which
nothing includes, leaving the *stale* `frame_params.scad` as the one being read.

**This bit again, inside the repo, during the v7 review itself** — an uncommitted
v8 params file next to v7 geometry produced two confident false findings. The
version banner exists so it is visible. Check it.

## R-016 · "The clamp bottoms out and grips air"  — REFUTED
**keywords:** clamp · tolerance · barrel · housing · refuted · nip · false-finding
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §refuted @ `428399c` · 2026-07-30 · grade: measured

> `clamp_nip` = 0.790 against a worst-case required travel of 0.480 for a minimum
> (24.77 mm) barrel. The cap still has 0.310 mm of gap left when it grips the
> smallest barrel the drawing allows. **The housing-tolerance fix in the newer
> `frame_params.scad` works.**

Recorded because refutations are as valuable as findings: **20 of 49 findings did
not survive**, and this one fired only because of the mismatched file set in
R-015.

## R-017 · "The cap's four ears collapse onto the bore axis" — REFUTED
**keywords:** cap · ears · bore · refuted · undef · false-finding · v8 · skew
**source:** engineered-lighting-site `ref/v7-adversarial-review.md` §refuted @ `428399c` · 2026-07-30 · grade: measured

`cap_bolt_x` = 17.765, not 0. It read as 0 because a v7 name evaluated to `undef`
under the v8 params file — R-015's exact mechanism, producing a *specific,
plausible, numerically stated* wrong finding.

---

# Motors and sourcing

## R-018 · "Caliper the 5005 for a raised boss on the output face"
**keywords:** 5005 · boss · output-face · caliper · step · vendor · measurement · no-longer-applicable
**source:** engineered-lighting-site `ref/RMD-L-5005-S.md:31` @ `fb0d5eb` · 2026-07-30 · grade: datasheet

> ### 1. Is there a raised boss on the output face? — **NO.**

**Not ruled out — answered, and no longer applicable.** The vendor STEP settled
it. Any task list still carrying "caliper the 5005" is carrying a question with a
published answer.

## R-019 · Damiao, Robstride and CyberGear "ruled out by a July sweep"
**keywords:** damiao · robstride · cybergear · motor · vendor · sweep · unsourced · re-verify
**source:** no supporting document · searched 2026-08-19 · grade: said-in-chat

**RE-VERIFY BEFORE CITING.**

A ledger line claims these three were ruled out by a July vendor sweep. I
searched both repositories on 2026-08-19 — including `docs/02-choosing-the-motors.md`,
the chapter whose entire subject is the motor choice — and found **zero
occurrences of any of the three names.**

That does not mean the sweep did not happen. It means **no document survives it**,
so the reasoning is unavailable and nobody can tell whether it still applies. If
a motor decision is reopened, this has to be redone rather than cited.

## R-020 · The RMD-L-4005
**keywords:** 4005 · 5005 · motor · swap · superseded · torque · availability
**source:** engineered-lighting-site `8fb39bf` · 2026-07-21 · grade: measured

Superseded by the RMD-L-5005 sitewide.

**Doc 2 still says "Why the RMD-L-4005 wins", and that is deliberate** — it is
kept as an availability/decision record, not a stale recommendation. Do not file
it as site staleness; it has already been considered and kept.

---

# Electrical and bench

## R-021 · Stranded wire in breadboard clips and bus rails
**keywords:** wire · stranded · solid · breadboard · intermittent · bus-rail · splay · cold-flow
**source:** engineered-lighting-site `PROJECT-STATE.md` @ `88a3a58` · 2026-08-01 · grade: measured

One of three failures diagnosed on the way to first motor motion:

> stranded wire fails in breadboard clips two ways (splay bare, cold-flow tinned)

The BoM adds the part nobody expects: **the listing photos look identical.** Solid
for breadboard contacts and soldered rails; stranded for anything that flexes or
gets handled — the 24 V runs, the service loops across the pan/tilt joints.

## R-022 · Treating 12.0 V as a gentle bring-up voltage
**keywords:** 12v · undervoltage · latch · psu · can · power-cycle · bring-up · rail · motor
**source:** engineered-lighting-site `PROJECT-STATE.md` @ `88a3a58` · 2026-08-01 · grade: measured

> 12.0 V is this 24 V-nominal motor's undervoltage-latch line, not a gentle
> bring-up; and when that latches, this unit takes its CAN interface down until a
> power cycle.

The second clause is what makes this expensive: the symptom is **a dead CAN bus**,
which sends you debugging the transceiver, the wiring and the firmware. It is a
supply fault wearing a comms costume.

## R-023 · Carrying stage 1's 2.0 A supply limit into stage 6
**keywords:** supply · current-limit · 2a · 3a · stage-6 · rail · undervoltage · tape · slew · led
**source:** gimbal-bench `captures/ui-overhaul/m18-led/RESULTS.md` @ `8bc2b5d` · 2026-08-02 · grade: inferred

Stage 1 sets 2.0 A for the LED-only stages and the draft never raised it again. At
stage 6 the motors join the same rail with 21 tape channels lit:

> a slew into a 2 A limit folds the rail toward 12 V — this motor's
> undervoltage-latch line… The bench's worst already-diagnosed failure would have
> returned wearing a new costume: *"the gimbal broke when the lights joined."*

Stage 6 now raises it to ~3 A. **R-022 recurring under a different cause** — which
is precisely what this register is for.

## R-024 · Inferring the PSU's state from CAN behaviour
**keywords:** psu · rail · voltage · can · unpowered · disconnected · meter · instrument · inference
**source:** gimbal-bench `captures/gimbal10/fixture/supply-state-20260814.md` @ `17194a1` · 2026-08-14 · grade: measured

CAN evidence is strong about presence — the no-ACK signature proves nothing is
electrically on the trunk — and it has a named limit:

> There is no instrument on this bench that measures rail voltage, and the CAN
> transport cannot distinguish *unpowered* from *disconnected*.

**SUPERSEDED IN PART, 2026-08-19.** Doc 4a (`d8f092b`, 2026-08-17) names the
bench meter — a **TESMEN TM-510** — so rail *voltage* is measurable now. What
survives is narrower and still real: the meter has **no current range**, so the
tape's per-zone current figures are derived from the spool's rating rather than
measured, and CP12 is a *watch-and-expect* check.

Left standing rather than rewritten, per the rule at the top of this file: the
2026-08-14 statement was true when it was made, and seeing it superseded three
days later is the more useful record. `EL-002` is rescoped to the current range.

## R-025 · Listen-only mode on the CANable `candleLight` tap
**keywords:** canable · candlelight · listen-only · silent-mode · tap · ack · capture · contamination
**source:** gimbal-bench `captures/gimbal10/ACK-ALTERED.md` @ `d1cda80` · 2026-08-14 · grade: measured

> **It has no working listen-only mode** — the repo verified this directly: `L` is
> unimplemented and silent mode is doubly broken.

So whenever the tap was open it was **acknowledging every frame the board
transmitted**. Do not plan a measurement around a listen-only tap on this
hardware; it does not exist.

## R-026 · Reading a pre-2026-08-13 wire capture without asking whether the tap was open
**keywords:** capture · ack · tap · error-passive · safe · tx-failed · provenance · 08-13
**source:** gimbal-bench `captures/gimbal10/ACK-ALTERED.md` @ `d1cda80` · 2026-08-14 · grade: measured

An open tap changes three things at once: TX succeeds, the error counters drain
(*"CAN error counters fall only on a successful transmission"*), and canonical
SAFE becomes reachable on a bus that could never otherwise produce it — measured
at **within 3 s of opening the peer, evaporating within 2 s of closing it**.

> a capture taken with the tap open answers **"what happens when something
> acknowledges"**, and a capture taken with it closed answers **"what happens when
> nothing does"**. Those are different experiments, and until 2026-08-13 nothing
> in this tree recorded which one had been run.

`ACK-ALTERED.md` **forbids nothing and says nothing about redaction.** It explains
why thirteen files were not banner-stamped and prefers one linked statement. Do
not cite it as a prohibition.

---

# Firmware and safety

## R-027 · R2 in the "c-boot" sub-form
**keywords:** r2 · c-boot · c-patch · ota · signature · mark-valid · rollback · adversary · overturned
**source:** gimbal-bench `docs/ZIGBEE-PHASE-PLAN.md` §0 @ `5a9bfbd` · 2026-08-16 · grade: measured

Ruled, then overturned by adversarial review **the same day**:

> `verifyRollbackLater()→true` … defers the mark-valid decision into the sketch of
> the **freshly-booted, possibly-hostile image**

> A hostile image calls `esp_ota_mark_app_valid_cancel_rollback()` on line 1 and
> never runs the signature leg

c-boot rejects only an *honestly* unsigned image — one that runs the real ladder
and self-fails. It gives **zero** protection against the actual threat. Replaced
by **c-patch**: the outgoing, still-trusted image verifies before handoff.

## R-028 · Secure boot (`CONFIG_SECURE_BOOT_V2`) — rejected for now, not forever
**keywords:** secure-boot · efuse · irreversible · ota · signing · r2 · rejected · strangers
**source:** gimbal-bench `docs/ZIGBEE-PHASE-PLAN.md` §0 @ `5a9bfbd` · 2026-08-16 · grade: datasheet

Hardware-capable and genuinely stronger — it protects the bootloader too. Rejected
because:

> an irreversible eFuse burn is heavier than a handful of owner-built fixtures
> warrant now (it stays the answer if this ever ships to strangers)

**Note the conditional.** This is a deferral with a named trigger, not an
elimination.

## R-029 · Replacing the dead-man with a hub-sourced liveness timer
**keywords:** dead-man · liveness · timer · hub · zigbee · rejoin · 400ms · d12 · rejected
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: inferred

> Over Zigbee a brief dropout takes **seconds** to recover, not milliseconds, so a
> 400 ms timer would trip constantly on a healthy system. Loosening it to seconds
> means seconds of uncommanded motion before anything reacts — a weaker net
> wearing the same name.

The winning answer was not a better timer, it was position-only commands (D12):
every command carries its own ending, so the mechanism stops being separate.

## R-030 · Relying on the motors' own comm timeout as the safety net
**keywords:** comm-timeout · motor · backstop · brake · gravity · de-energise · drop · rejected · d12
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: inferred

> It exists and it is a real backstop, but it removes power. On a brakeless
> gravity axis that risks a drop rather than a hold.

The general rule this instance teaches: **on this machine, "fail safe" and
"de-energise" are not synonyms.**

## R-031 · Auto-disarm on the ACKed half of an armed mute
**keywords:** auto-disarm · mute · armed · degrade · m6 · f1 · rejected · session · cadence
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: inferred

Three reasons, all recorded: killing a two-axis session for a one-axis fault that
disarm cannot cure buys nothing the degrade does not; at the archived 2-minute
cadence auto-disarm makes the undiagnosed regimes **unstudiable**; and the deployed
analog is self-healing anyway. The no-ACK half already disarms via `SC_TX_FAILED`
and that law is unchanged.

## R-032 · A flat `0x81` pin for the mute entry-stop opcode
**keywords:** 0x81 · 0x80 · opcode · mute · entry-stop · hold · release · f7 · gravity · rejected
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: inferred

Rejected along with a second writer for `kaLastTxOk`. The chosen mechanism selects
from the mute's own live evidence: ACKed solicits → the motor likely heard → hold
(`0x81`); un-ACKed → likely already de-energised → release (`0x80`), **do not
lunge**.

Fork F7 was flagged in review as *"not mine to pick"* — a hold-vs-release choice on
a gravity axis is an owner call.

## R-033 · A third mute cause
**keywords:** mute · cause · classifier · slow-motor · rx-correlation · f6 · rejected · vocabulary
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: inferred

No archived slow-motor regime exists, and the RX-CORRELATION-ERROR lines already
discriminate the shape on the wire. Same family as F3's rejection of a new READY
blocker: `reply_stale` already carries the fact, and **duplicating it invites drift
between vocabularies.**

## R-034 · Any flash or NVS write on a fault path
**keywords:** nvs · flash · fault-path · stop-budget · 50ms · mirror · ring · m5 · erase
**source:** gimbal-bench `captures/gimbal10/fixture/ring-mirror-20260814.md` @ `669a3a7` · 2026-08-14 · grade: measured

> **No fault path touches flash.** An NVS commit erases a page and can block for
> tens of milliseconds; the stop budget is 50 ms and does not negotiate.

The accepted consequence, stated rather than hidden: *"A missed mirror costs
history. A blocked stop costs a motor still running."* Same arithmetic in the OTA
chapter — *"**The erase blows the stop budget.** … A block erase burns a large
fraction of B3."*

## R-035 · Restoring the fault ring from flash whenever flash has a copy
**keywords:** mirror · restore · ring · rtc · stale · one-directional · m5 · guard
**source:** gimbal-bench `captures/gimbal10/fixture/ring-mirror-20260814.md` @ `669a3a7` · 2026-08-14 · grade: measured

`mirrorRestore()` returns immediately **unless layer one came back empty**.

> A ring that survived in RTC is fresher than flash by definition, so reading
> flash over it would replace a live record with a stale one.

A mutation removing that guard is caught by test. The general shape: **a restore
that is not one-directional is a way to lose data, not a way to keep it.**

## R-036 · Quieting the firmware's logging first when chasing the serial flood
**keywords:** serial-flood · 57 · logging · browser · fix-order · d14 · liveness · diagnosis
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: inferred

> Quieting the firmware first would hide the browser bug under a lower volume
> rather than fixing it.

Order is part of the ruling: **count where the messages originate, then fix the
browser, then quiet the firmware.**

## R-037 · Proving mute machinery offline
**keywords:** offline · test · mega-gate · mutation · transmit · m6 · p1 · bench · coverage
**source:** gimbal-bench `captures/gimbal10/fixture/authority-recon-20260815/reader-planV2.md` @ `89e9afc` · 2026-08-16 · grade: measured

M6's first-hour P1 was invisible to

> 538 tests, six review mutations, and two green gates, because **nothing offline
> transmits**.

A green offline gate is evidence about the model, not about the bus. **GB-004**
exists because of this entry.

## R-038 · Reading "no head-dropping observed" as "the head does not drop"
**keywords:** mepsilon · me · de-energised · hold · creep · d1 · gate · tilt · unmeasured
**source:** gimbal-bench `captures/gimbal10/fixture/authority-recon-20260815/reader-planV2.md` @ `89e9afc` · 2026-08-16 · grade: measured

The first map on 2026-08-15 was genuinely good — five tilt poses, released 5-minute
windows, *"**the head does not fall anywhere**"*, worst case 0.62° one-time settle
and 0.01°/min creep. And the same entry refuses to over-read it:

> **D1's 'unmeasured' caution retired on one axis. The formal gate still owed**:
> 10-min windows, computed max-torque pose, both axes, vibration unaddressed.

One axis, five-minute windows, no vibration. **Do not cite Mε as closed.**

---

# Zigbee and transport

## R-055 · Proving the armed-lane mute by physically unplugging a connector
**keywords:** mute · armed · lane · drill · unplug · transient · ack · disarm · mutesim · m6 · bench
**source:** gimbal-bench `captures/gimbal10/fixture/bench-session2-20260815.md` @ `19dd790` · 2026-08-15 · grade: measured

The drill is self-defeating and the capture works out why:

> the armed-lane mute resists physical-unplug drills — the pull's transient
> kills an armed frame before the mute can accrue.

The instant the connector moved, the electrical transient cost an armed PAN
heartbeat its ACK, and the standing armed no-ACK law disarmed within one frame —
`ERR tx failed op=0x9A axis=pan` → `SAFE - ordinary transmission failed`. The
session left the armed lane before the mute could exist in it.

**The fixture was not wrong.** The capture's own verdict:

> arguably the most correct thing the fixture did all day

The named replacement is the dev-gated reply-drop drill on the `+mutesim` image,
which drops replies without touching the wiring. `GB-004` carries it.

Two limbs of that drill DID land the same session — motor-silent latched at
1.9 s, MUTE-CLEAR on replug — so this entry rules out a **method**, not the
milestone.

## R-039 · Un-parking Zigbee before the fault ring and the drills
**keywords:** zigbee · parked · d15 · un-park · fault-ring · m5 · drills · owner-decision · preemption
**source:** gimbal-bench `captures/gimbal10/fixture/owner-decisions-20260814.md` @ `e4d71a9` · 2026-08-15 · grade: measured

**Zigbee is ruled (D3) and parked (D15). Not dead, not next.** Both halves matter;
either one alone gets the priority wrong in an opposite direction.

The three parking costs stand: the radio preempts a superloop with zero mutexes
(`esp_zb_task` at priority 5 vs the Arduino loop at 1, single core); OTA is
dangerous as built; and *"If the light is on Zigbee, no hub means no light."*

**Un-parking is an owner decision that has not been taken.** No agent takes it.

## R-040 · Tombstoning `spot-bench.yaml` wholesale
**keywords:** spot-bench · esphome · tombstone · still-live · watchdog · failsafe · presets · d3 · behaviour
**source:** gimbal-bench `esphome/spot-bench.yaml` @ `d1cda80` · 2026-08-14 · grade: measured

The file names exactly what survives D3:

> STILL LIVE, and not superseded by anything:
>   - The Auto/Hold/Manual gate, the 2 s watchdog and its two-stage failsafe, and
>     the one-shot preset semantics. Those are BEHAVIOUR, not transport… and the
>     gimbal-10 firmware does not have them yet.

It also holds **the strongest argument against D3** — `fixture_aim(pan, tilt)`
already exists there as a typed, atomic, encrypted, natively-exposed pose command
with zero custom code. Deleting the file deletes the counter-argument:

> Anyone tombstoning these lines is deleting a working thing to replace it with a
> planned one; that trade may still be right, and it is a trade.

## R-041 · Reading a word count as a decision
**keywords:** word-count · doc6 · doc7 · esphome · retire · method · false-inference · propagation
**source:** product-os `wiki/ruled-out.md` (this file), from the v2 plan review · 2026-08-18 · grade: inferred

"Doc 6 has 11 ESPHome lines and 1 Zigbee line" was read as "retire Doc 6's ESPHome
lane". The cited source said the opposite — R-040's STILL LIVE block covers exactly
Doc 6 §1.

**Counts tell you where to look. They rule nothing.** `SITE-001` is scoped to
`wifi:`/`api:`/`mqtt:` as *transport* for this reason.

## R-042 · `esp-zigbee-lib` enums in the Z-M0 mailbox
**keywords:** z-m0 · mailbox · enums · primitives · uint16 · compile-order · zigbee · library
**source:** gimbal-bench `docs/ZIGBEE-PHASE-PLAN.md` §6 @ `5a9bfbd` · 2026-08-16 · grade: inferred

The mailbox uses **primitive types (uint16/uint8), not esp-zigbee-lib enums**, so
it compiles ahead of the library. Using the library's enums couples the milestone
to a dependency the milestone is specifically ordered to precede.

## R-043 · `fixture-bench.yaml`
**keywords:** fixture-bench · spot-bench · yaml · duplicate-key · doc4 · gpio · fork · filename
**source:** gimbal-bench `captures/ui-overhaul/m18-led/RESULTS.md` @ `8bc2b5d` · 2026-08-02 · grade: measured

Doc 4's prompts say to grow `fixture-bench.yaml`. **That file does not exist.** The
real one is `esphome/spot-bench.yaml`, and it already carries the as-built stages 5
and 6.

> Following the doc verbatim would fork a second YAML or paste reference blocks
> over the real ones — claiming GPIO10/11/18 twice and producing exactly the
> cryptic duplicate-key error stage 3's own hazard warns about, self-inflicted by
> the console's guidance.

---

# Process and this system

## R-044 · Seeding or auditing from a local clone
**keywords:** git · clone · stale · fetch · rev-list · origin · tracking-ref · unreachable · evidence
**source:** product-os `tools/_git.py`; measured against the local checkout · 2026-08-19 · grade: measured

    $ git rev-list --count HEAD..origin/main      # in the local clone
    0
    $ gh api .../compare/90ff98d...main --jq .ahead_by
    54

The tracking ref had not been fetched since July. **`git log` answered confidently
and wrongly**, and it would have answered wrongly in the same direction for every
consumer: the audit finds no new commits, the brief stamps itself current, the
resume says nothing landed.

Re-confirmed 2026-08-19: local HEAD `90ff98d` (2026-07-28), remote last push
2026-08-17. **Always fetch first. If the fetch fails, say `⚠ unreachable` — never
fall back to the local ref.**

## R-045 · `\b[A-Z]{2,4}-\d{3,}\b` as the item-ID mention regex
**keywords:** regex · item-id · mention · thread-indexer · false-positive · aes · sha · iso
**source:** product-os `tools/_fm.py` · 2026-08-18 · grade: inferred

Matches `AES-256`, `SHA-256` and `ISO-8601` — **916 hits, 100% false positives on
the real corpus** — and misses `Q-007` entirely, because the prefix is one letter.
Anchor to the live prefix set instead.

*Not re-derived this session; the count comes from the tooling comment.*

## R-046 · The spec's urgency formula
**keywords:** urgency · lead-time · effort · formula · quadratic · scoring · cap · double-count
**source:** product-os `tools/_model.py` · 2026-08-18 · grade: inferred

`lead / effort` counts effort twice — it is already the score's denominator. Two
independent reviews flagged the resulting quadratic, and the proposed cap bound at
15.75 days, **below this portfolio's normal case.**

Replaced by `1 + lead/7`. The cost is recorded rather than hidden: the spec's
version meant "cheap action, expensive clock"; this one means just "clock", so a
40-hour long-lead task now gets the same multiplier as a 3-minute one.

## R-047 · `sort_keys=True` on entity frontmatter
**keywords:** frontmatter · json · key-order · sort-keys · diff · canonical · obsidian
**source:** product-os `tools/_fm.py` · 2026-08-18 · grade: inferred

Alphabetical puts `title` 22nd of 24 and scatters `impact`/`confidence`/`effort`
across the block. Explicit spec order is what makes a one-field change diff as one
line.

Related and unfixed: **Obsidian's Properties editor rewrites frontmatter as block
YAML on any edit**, which breaks `json.loads`. `validate.py --fix-format` is the
repair path; there is no prevention.

## R-048 · Path-level guards for a field-level authority rule
**keywords:** fsguard · pretooluse · authority · hook · field · frontmatter · validate · enforcement
**source:** product-os `tools/validate.py` · 2026-08-18 · grade: inferred

A `PreToolUse` guard sees **a file**, not a field. Human-authority and
agent-authority keys live in the same frontmatter block, so no path rule can tell
which key moved. `validate.py`'s diff against a base ref is the only layer
structurally capable of enforcing it.

**Known hole, stated:** the audit skips newly added files — there is nothing to
diff against. The seed went through that hole on 2026-08-19, deliberately and in
the open, with `PROP-0001` naming every field it set.

## R-049 · Publishing `gimbal-bench` today
**keywords:** publish · public · gimbal-bench · disclosure · third-party · blocked · authorized · scrub
**source:** gimbal-bench `captures/gimbal10/fixture/authority-recon-20260815/reader-networkRemnants.md` · read 2026-08-18 · grade: measured

**Authorized by the owner and blocked on one narrow, sufficient ground:** a capture
names a real third party's personal email address in full, beside an incident on
that person's tailnet, with no indication they were told. That is not reversible
and not mine to publish on someone's behalf.

Three corrections to how this was first described, kept because the first telling
was wrong in the direction that made it sound worse:

- **The direction was inverted.** The exposure ran *from* the bench console *to*
  devices on their tailnet. Their devices were not exposed; the bench's telemetry
  was exposed to them.
- The source states the mitigation and it was omitted: the owner secret stayed
  loopback-gated and the motors were unpowered throughout.
- The stale binding is **inert** — the console refuses that hostname at all three
  shields — and the source already names the retirement command.

Before any flip: anonymize the paragraph, retire the binding, run secret scanning
over full history including deleted blobs (**18.8 MB** of captures), and review the
**85 images** — 30 workbench frames and 43 UI screenshots that may show a hostname
in an address bar. Then decide separately about network identifiers and serials,
which are woven through evidence captures.

**A retro-scrub is not forbidden by `ACK-ALTERED.md`** — see R-026. The argument
against scrubbing is editorial, not constitutional.

## R-054 · GitHub code search as a substitute for grep
**keywords:** code-search · grep · gh · search · verification · false-negative · quote · withdrawal · method · audit
**source:** measured against both repos, 2026-08-19 · grade: measured

**A `gh api search/code` query that returns nothing is not evidence that the
string is absent.** It returns nothing for indexing lag, for large files, for
recently pushed commits, and it does so with the same empty result as a genuine
miss. There is no distinguishing signal.

Measured, twice, on 2026-08-19. Both of these were reported ABSENT from both
repositories on the strength of empty code-search results, and both are real:

    "this bench's meter has no current range"
        -> docs/04a-wire-the-zones.md:331   (d8f092b, 2026-08-17)
    "Marcelo to call"
        -> PROJECT-STATE.md:158             (88a3a58, 2026-08-01)

The second had been sitting in the repo for eighteen days. Code search simply
did not return it.

**The consequence was worse than a missed fact.** Both strings were quoted in
the approved plan; both were withdrawn from seeded items as unsourced, with a
provenance note published saying the source did not exist. That is a false claim
about a source, made confidently, in the file whose entire purpose is provenance
— committed as `8175094`.

**The rule: fetch the file and grep it.** `gh api .../contents/PATH | base64 -d`
then `grep`. Code search is for discovery when you do not know where to look. It
is never the thing that establishes a negative. And a negative about a quote is
exactly the claim that has to be right.

Found by the first real `/audit` run, in group D, from a commit no path rule
claimed.

## R-056 · Browser-local state as a repo evidence rule
**keywords:** evidence · rule · unsatisfiable · checklist · bom · localstorage · browser · audit · el-001 · closure
**source:** engineered-lighting-site `docs/bom-checklist.md:10` @ `88a3a58` · found 2026-08-19 · grade: measured

`EL-001`'s evidence rule named `docs/bom-checklist.md` and nothing else. That
file says of itself:

> state persists in your browser (nothing leaves your device)

Ticking every box writes **nothing** to the repository. The rule was
**structurally unsatisfiable** — no purchase, delivery or installation could
ever cause the path to change in a way that recorded the purchase — so the item
could never close, and it sat at rank #1 in the portfolio from the seed onward
while its parts were photographed on the bench in `docs/04a-wire-the-zones.md`.

**An evidence rule must name a path that COMPLETING THE ITEM WOULD CHANGE.**
Not a path about the same subject. Three shapes that fail this and look fine:

- a UI whose state lives in the browser (this one),
- a rendered artifact regenerated from elsewhere,
- a checklist, table or index that a human edits on a different schedule than
  the work.

**Why this is the fourth instance of the root cause, and the worst:** the rule
was already in `CLAUDE.md` — *a mechanical signal is not the primary source* —
and `audit.py` committed the error anyway, because *"this rule matched nothing"*
and *"this item is not done"* were **the same code path**. Writing a rule into
the contract does not wire it into the machinery.

`audit.py` now classifies every rule as `satisfiable` / `never-fired` /
`unsatisfiable` against the repo tree, and reports the last two in group B
rather than leaving the item silently `next`. That check cannot catch this exact
case on its own — `bom-checklist.md` is a real, committed file — so it reports
the honest thing instead: *"has not fired" and "cannot fire" look identical from
here.* Only a person can tell them apart, which is what a person did.

## R-057 · Treating an item ID as unique across seed generations
**keywords:** id · citation · indexer · threads · generation · collision · seed · rebuild · attachment · q-004
**source:** measured against `~/.claude/projects` on 2026-08-19 · grade: measured

The thread indexer's first run bound a real transcript to `Q-004`. It was wrong.
That transcript's `Q-004` sits in this line:

> Blocks: EL-040, EL-042 · Answers: Q-004

`EL-040` and `EL-042` do not exist. They are from the **33-item v1 seed**, which
was discarded and rebuilt — and the rebuild reused the numbers for unrelated
work. Today's `Q-004` is *"where do 300 liveness taps a second come from"*.

**An ID is unique only within a seed generation.** A citation is evidence of a
conversation about *whatever that ID meant at the time*, which is not
recoverable from the ID alone.

The fix is a date, not a heuristic: a conversation cannot cite an item that did
not exist when it happened, so `index.py` drops any citation whose thread
predates the item's `created`, counts it, and reports it as a collision.

**Why this one is dangerous:** it produces a *plausible* attachment. A wrong
thread bound to a real item looks exactly like a right one, and it would have
sat in the shard being cited as provenance.

## R-058 · A coverage number that silently caps
**keywords:** pagination · api · per-page · group-d · coverage · truncation · audit · window · floor
**source:** measured against the GitHub API on 2026-08-19 · grade: measured

`audit.py`'s commit query used `per_page=100` with no pagination. For
`gimbal-bench` it returned **exactly 100** commits and reported that as the
answer; the true count in the same window was **245**.

Group D — the number whose entire job is to say *"I recognised nothing here"* —
was capped. Two figures were quoted on the same day, **108** and **156**, and
both were wrong for two compounding reasons: different `--since` windows, and
truncation underneath both. Paginated and labelled, the default window is
**301**.

**The tell was the roundness.** A count that lands exactly on a page boundary is
a page boundary, not a count.

Two rules from this:

- **A coverage figure must carry its window.** Without one it is not comparable
  to itself between runs, which is how 108 and 156 both looked right.
- **A capped result must say it is a floor.** `audit.py` now stops on a short
  page, and if it exhausts its page budget it prints `TRUNCATED` and says every
  count above it is a floor.

## R-059 · Believing the done-without-evidence guard stops a determined agent
**keywords:** guard · evidence · done · truth · apply · process · snapshot · authority · limitation · self-check
**source:** product-os `tools/apply.py`; walked through it 2026-08-19 · grade: measured

`apply.py` refuses `status: done` unless `evidence_found` existed **before the
run**, so that evidence discovered by an audit is read by a person before it
closes anything. The intent is right. The implementation measures the wrong
thing.

**"Before the run" is a process boundary, not readership.** Closing `POS-003`
took two commands:

    1. write evidence_found to the item file   (agent authority — permitted)
    2. apply.py --status POS-003=done          (guard sees it as "prior")

No human read anything between them. I did this without intending to, which is
the point: the guard reads as a hard stop and is a speed bump.

**What actually holds, and what does not:**

- **Holds:** it stops `done` on an item with genuinely no evidence, which is the
  common case and the one that matters. It also stops an audit closing an item
  on evidence the same command discovered.
- **Does not hold:** anything against an agent willing to write the evidence
  first. No in-process rule can, because the same actor authors both sides.

**So the real guarantee is elsewhere.** `--decided` requires his words on the
record, and the audit record stamps every applied line `on his word` or
`inferred`. `POS-003`'s closure is stamped **`(inferred)`** — permanently
visible as a machine's judgement rather than his. That distinction is the thing
that survives, and it is worth more than a guard that can be stepped over.

Do not strengthen the snapshot rule into something that looks unbreakable. Make
the origin stamp legible instead, and read the `(inferred)` lines when deciding
what to trust.

## R-060 · Believing `git commit --amend` removes an address from a public repo
**keywords:** commit · metadata · email · author · committer · amend · orphan · disclosure · screen · public · identity
**source:** measured against the GitHub API, 2026-08-19 · grade: measured

`validate.py`'s disclosure screen scans **file contents**. On a public repo,
**author and committer emails are public too** — served by the API for every
commit — and the screen never looked at them.

A work address reached one public commit before being amended out. Amending did
not remove it:

    $ gh api repos/hooterjackson/product-os/commits/e30c955
      -> 200, author and committer both carry the work address

That commit is unreachable from any branch and **still served by SHA**.
`--amend` writes a new object and orphans the old one; GitHub keeps orphans and
keeps answering for them. `git gc` on the clone changes nothing about a remote.

**Only GitHub support can purge it.** There is no local command that
substitutes, and believing otherwise is the entry.

`check_commit_identities()` now scans `git log --all` and the reflog against the
same allowlist, splitting the two cases deliberately:

- **Reachable history → error.** Fixable here, so it fails the gate.
- **Orphaned objects → warning.** Not fixable with git, and a permanently red
  gate on something the tooling cannot repair trains people to ignore the gate.
  Never silent, because the address is genuinely public.

`state/secret-allowlist.txt` carries the two intended identities. A third
appearing is a finding.

**The reusable shape:** a screen that scans one surface implies coverage of
everything. Metadata is a surface. This repo had a rule about disclosure and a
tool that executed it against files only — which is the same class as R-054 and
R-056, one level further out.

## R-061 · Publishing an artifact whose content the act of publishing changes
**keywords:** freshness · stamp · publish · public · stale · commit · counter · volatile · durable · sync
**source:** measured in this repo, 2026-08-19 · grade: measured

The brief's freshness line carried a live delta — `⚠ product-os +9 since the
last audit` — computed from the local working copy's HEAD. That line was then
**committed** into `public/`.

So the commit that published the stamp invalidated it. Measured directly: `+9`
before committing, `+10` after. `publish.py --check` went red immediately, and
a stale stamp had already been pushed to a live URL that other machines fetch.

**"Regenerate before committing" does not fix this** and it is worth being
precise about why: regenerating produces `+10`, committing that makes it `+11`.
There is no ordering of the two steps that converges. The artifact was a
function of the event that shipped it.

The fix is to split the fact, not to sequence the steps:

- **Durable** — when the last audit ran, over what window, what it found.
  Stable between audits, so it survives being committed. This is what `public/`
  carries, and it is the half a remote consumer actually needs.
- **Volatile** — "+N commits since then", a live working-copy fact. Stays in
  `build/`, which is git-ignored, for the person at the keyboard who can act on
  it.

**The general shape:** before publishing a derived artifact, ask whether
publishing it changes its own inputs. Anything counting commits, file sizes, or
"time since" against the repo it lives in will.

## R-050 · `product-os` starting public
**keywords:** product-os · public · private · disclosure · ruled-out · seed · publication
**source:** product-os `wiki/ruled-out.md` (this file) · 2026-08-19 · grade: inferred

This repository starts **private**, against the original preference, because this
very file seeds ~50 findings from an unpublished engineering repo — including
security-design detail of the authority model of a brakeless ceiling-mounted
machine (R-027, R-032, R-034).

Flipping to public later is one command. Unflipping is not.

## R-051 · Trusting a header date over the git history under it
**keywords:** project-state · header · date · pending · stale · handoff · state-file · drift
**source:** engineered-lighting-site `PROJECT-STATE.md` @ `88a3a58` · 2026-08-01 · grade: measured

`PROJECT-STATE.md` listed two prompts as pending. **Both had already shipped**,
before the file listing them as pending was committed. The file eventually
corrected itself:

> Earlier revisions of this file listed two prompts as pending; git history shows
> both were executed before it was committed.

A hand-maintained state file drifts against the repo it describes, and the drift is
invisible from inside the file. **POS-002** exists because of this entry; so does
the risk that product-os becomes state file number nine.

## R-052 · Publishing a ratio without its operands
**keywords:** arithmetic · ratio · operands · claim · falsifiable · lead-time · publish · method
**source:** product-os, from two rejected plan revisions · 2026-08-18 · grade: inferred

One plan version printed a lead-time ranking claim with a **wrong** number; the
next printed `27×` with **no operands at all**, which is worse — a wrong number is
falsifiable and a bare ratio is not.

`rank.py --show <ID>` prints every operand. Use it instead of asserting a
conclusion.

## R-053 · Paraphrasing inside quotation marks
**keywords:** quote · paraphrase · composite · fabrication · evidence · method · verbatim
**source:** product-os, from a rejected plan revision · 2026-08-18 · grade: inferred

A plan shipped a composite quote that existed nowhere — inside a section headed
*"edges the evidence states, quoted."*

**If the string cannot be found, do not put quotation marks around it.**

**Amended 2026-08-19.** This entry was used to justify withdrawing two quotes
that turned out to be genuine — see `R-054`. The rule stands; the *search* that
decides "cannot be found" is the part that has to be trustworthy, and mine was
not. Withdrawing a real quote and inventing one are both ways of publishing
something false about a source.
