---
name: chaos-engineering
description: >
  Design, evaluate, and debrief chaos engineering experiments. Use when the user is
  planning a fault-injection experiment, calculating blast radius, choosing a chaos
  tool, reviewing an experiment plan for safety, or writing a Game Day postmortem.
  Trigger on: "chaos experiment", "fault injection", "gameday", "game day",
  "resilience test", "blast radius", "steady state", "abort criteria",
  "Chaos Toolkit", "Chaos Mesh", "Litmus", "Gremlin", "AWS FIS", or any question
  about deliberately injecting failures into a system. Do NOT use for: general
  incident response, threat hunting / red-team exercises, performance load testing,
  or post-incident debugging of production issues.
---

# Chaos Engineering

Design experiments that surface real weaknesses in production systems — without
becoming outages. Most "chaos engineering" attempts skip steady-state measurement,
define no abort criteria, and leave blast radius unbounded. This skill enforces the
discipline that makes chaos experiments safe and repeatable.

The foundational reference is `references/chaos_principles.md`. The 4 Principles of
Chaos Engineering (Netflix, 2016) apply to every experiment this skill produces.

---

## When to use this skill

| User says | Use skill |
|---|---|
| "Design a chaos experiment for my checkout service" | Yes |
| "Is my blast radius acceptable?" | Yes |
| "Which chaos tool should I use?" | Yes |
| "Write a postmortem for our Game Day" | Yes |
| "We had an outage last night, help me debug it" | No — use incident-response |
| "Simulate load to find my capacity ceiling" | No — that is load testing, not chaos |
| "Red-team our auth service" | No — use red-team / threat-detection |

---

## Inputs to gather

Ask once if not provided. Do not proceed on assumptions for starred fields.

| Input | Required | Default |
|---|---|---|
| Target service or component | Yes★ | — |
| Hypothesis (what should hold under the fault) | Yes★ | — |
| Steady-state metric and baseline value | Yes★ | — |
| Attack type (latency / error / resource / partition / dependency / time / infra) | Yes★ | — |
| Magnitude (e.g. "+200 ms", "50% packet loss", "1 of 3 replicas killed") | Yes★ | — |
| Blast radius (% of traffic / user segment / single AZ) | Recommended | 5% of traffic |
| Duration | Recommended | 15 minutes |
| Abort criteria (concrete threshold that triggers immediate rollback) | Recommended | p99 > 2× baseline OR error rate > baseline + 2 pp |
| User population (for blast radius calculation) | Recommended | required if calculating affected users |
| Baseline availability SLO | Recommended | 99.9% |
| Chaos tool preference | Optional | determined from stack |
| Output mode (plan / blast-radius / postmortem / all) | Optional | all |

For **postmortem mode**, also gather: experiment plan used, result log or summary,
whether abort criteria were hit, and observed vs. expected behavior.

---

## Core principle: no abort criteria = outage

A chaos experiment without abort criteria is an outage with better PR. Before
Claude produces any experiment plan, abort criteria must be present. If the user
hasn't provided them, Claude proposes concrete defaults and asks for confirmation —
never silently omits this section.

---

## Output modes

This skill has three output modes. Produce all three unless the user requests a specific one.

### Mode 1 — Experiment plan

A structured markdown plan with these required sections (none are optional):

```
## Chaos Experiment: <short name>
Date: <planned date>
Facilitator: <name or TBD>
On-call notified: Yes / TBD

### Hypothesis
When [fault description], [steady-state metric] stays within [threshold].

### Steady-state (measure BEFORE the experiment)
Metric: <name>
Baseline: <value>
Source: <dashboard URL or monitoring query>

### Attack
Type: <attack type from taxonomy>
Target: <service / node / network path>
Magnitude: <quantified — never vague>
Duration: <minutes>
Tool: <specific tool and version>
Inject command / config:
  <concrete command or CRD snippet>

### Blast radius
Traffic share: <N>%
User population: <N>
Expected affected users: <blast_radius_pct × user_pop>
Risk score: GREEN / YELLOW / RED  (see calculation below)
Error budget consumed: <minutes>

### Abort criteria (monitor continuously — abort immediately if hit)
- <metric> > <threshold>
- <metric> < <threshold>
Kill switch: <feature flag name or rollback command>

### Rollback procedure
1. <step>
2. <step>

### Monitoring
Dashboards: <URLs>
Alerts to watch: <list>

### Learning question
What will we know after this experiment that we don't know now?
```

Do not produce a plan that omits any of these sections. If a value is genuinely
unknown, mark it `[REQUIRED — fill before running]` rather than silently omitting it.

---

### Mode 2 — Blast radius calculation

Given traffic share, user population, duration, and expected availability impact,
compute the following. Show the arithmetic inline so the user can sanity-check.

**Inputs:**
```
traffic_share            = <e.g. 0.05 for 5%>
user_population          = <N>
duration_min             = <N>
baseline_availability    = <e.g. 0.999 for 99.9%>
expected_availability    = <e.g. 0.95 under the fault>
```

**Calculations:**

```
affected_users           = user_population × traffic_share
                         = <result>

monthly_error_budget_min = user_population × (1 - baseline_availability) × 43800
                         = <result> minutes

experiment_errors_min    = affected_users × (baseline_availability - expected_availability)
                             × duration_min
                         = <result> minutes

error_budget_consumed_%  = (experiment_errors_min / monthly_error_budget_min) × 100
                         = <result>%
```

**Risk score:**

| error_budget_consumed | Score | Recommendation |
|---|---|---|
| < 1% | GREEN | PROCEED |
| 1% – 10% | YELLOW | REDUCE blast radius or shorten duration |
| > 10% | RED | ABORT — redesign the experiment |

State the score and recommendation explicitly. If RED, suggest the minimum change
needed to reach GREEN (e.g., "reduce traffic share from 5% to 0.4%").

---

### Mode 3 — Experiment postmortem

Produce a structured postmortem from the experiment plan and result summary.
Avoid blame-laden language throughout — record causes and system behavior, not
individual fault. Flag if the user's draft contains blame framing and offer
a rewrite.

Required sections:

```
## Experiment Postmortem: <name>
Date run: <date>
Facilitator: <name>
Participants: <list>

### Summary (3 sentences max)
What we tested, whether the hypothesis held, and the single most important finding.

### Hypothesis
State: CONFIRMED / REFUTED / INCONCLUSIVE
Evidence: <metric values observed vs. expected>

### What abort criteria did (if triggered)
Did abort criteria fire? Yes / No
If yes: what triggered it, how quickly was it detected, how quickly was rollback complete?

### What we learned
<bullet per finding — specific, not generic>

### What surprised us
<anything the hypothesis didn't predict>

### System behavior under fault
<describe what actually happened — no blame, pure mechanics>

### Follow-up actions
| Action | Owner | Due | Priority |
|---|---|---|---|
| <action> | <name> | <date> | P1/P2/P3 |

Each action must map to a specific weakness found. If no actions are generated,
that is a signal the postmortem is too vague — push the user to be more specific.

### Next experiment
What is the logical follow-up experiment based on what we learned?
Link to draft plan if one is started.
```

---

## Attack taxonomy

Pick the attack type that matches the hypothesis. See `references/attack_taxonomy.md`
for full detail, tooling flags, and worked examples for each type.

| Attack | What it tests | Primary tooling |
|---|---|---|
| Latency | Timeouts, retries, circuit breakers | `tc netem`, Chaos Mesh `NetworkChaos` |
| Error | Error handling, fallback paths | Chaos Mesh `HTTPChaos`, Toxiproxy |
| Resource (CPU / memory / disk) | Saturation, autoscaling response | Chaos Mesh `StressChaos`, stress-ng |
| Network partition | Split-brain, consensus, failover | Chaos Mesh `NetworkChaos partition` |
| Dependency failure | Graceful degradation, fallbacks | Service mesh fault injection |
| Time / clock skew | NTP issues, TTL bugs, scheduled jobs | libfaketime, Chaos Mesh `TimeChaos` |
| Infrastructure kill | Auto-recovery, failover, restart policy | AWS FIS, Chaos Monkey |

Selecting the attack: map the hypothesis verb to the type. "What if X is slow?" → Latency.
"What if X is unreachable?" → Network partition or Dependency failure. "What if X dies?" → Infra kill.

---

## Tooling chooser

See `references/tooling_landscape.md` for full trade-off analysis.

| Tool | Best for | Model |
|---|---|---|
| Chaos Toolkit | Lightweight, language-agnostic, JSON/YAML experiment files | OSS |
| Chaos Mesh | Kubernetes-native, rich CRD library, in-cluster | OSS |
| Litmus | Kubernetes, Argo-integrated, large pre-built experiment library | OSS + Enterprise |
| Gremlin | Enterprise SaaS, multi-cloud, audit trails | Paid |
| AWS FIS | AWS-native, IAM-integrated, EC2 / ECS / EKS | Paid (per resource) |
| Custom scripts | Niche needs, single-cloud, minimal budget | None |

Decision rules (apply in order, stop at first match):

1. Kubernetes-only + OSS budget → Chaos Mesh if you need fine-grained network/time/stress;
   Litmus if you want a pre-built experiment library with Argo scheduling.
2. Multi-cloud + OSS budget → Chaos Toolkit (tool-agnostic; drives Mesh/Litmus/FIS as backends).
3. AWS-heavy + simple infra-kill / resource experiments → AWS FIS (IAM-native, no extra agents).
4. Enterprise + audit / compliance requirements → Gremlin.
5. None of the above → Custom scripts with Chaos Toolkit as the experiment runner.

---

## Workflows

### Design and run a single experiment

```
1. State a hypothesis: "When [fault], [metric] stays within [threshold]."
2. Confirm the steady-state metric is measurable RIGHT NOW, before the experiment.
3. Run Mode 2 (blast radius) — confirm GREEN before producing the plan.
4. Run Mode 1 (experiment plan).
5. Peer review the plan; confirm abort criteria are concrete and testable.
6. Notify on-call in the team's incidents channel.
7. Run with monitoring dashboards open.
8. If abort criteria fire, stop immediately; record what triggered them.
9. Run Mode 3 (postmortem) to capture learnings.
10. File follow-up actions with owners; link to next experiment.
```

### Game Day exercise

```
1. Pick a scenario (e.g., "primary database fails over to replica").
2. Identify all dependent services that should continue functioning.
3. Build a multi-experiment plan covering each layer of the system.
4. Schedule with stakeholders; on-call coverage is not optional.
5. Run with a facilitator who manages the scenario and watches abort criteria.
6. Capture observations in a shared doc as they happen (not after).
7. Single combined postmortem covering all observations from the day.
8. Track follow-up actions in a board with owners and due dates.
```

### Continuous chaos (maturing from game days)

```
Stage 1: Weekly Game Day in staging. No production blast radius yet.
Stage 2: Weekly Game Day in production, traffic share ≤ 5%, GREEN risk score required.
Stage 3: Scheduled continuous experiments (Litmus ChaosSchedule, Gremlin scenarios).
Stage 4: Wire to deployment pipeline — every prod deploy triggers a baseline sweep.
Metric to track: experiments per week, weaknesses found, MTTR trend over quarters.
```

---

## Composition with other skills

| Skill | How they compose |
|---|---|
| `feature-flags-architect` | Kill switches defined there are the abort triggers here; always name the feature flag in the experiment plan's abort section |
| `kubernetes-operator` | Operators are common chaos targets; test reconcile loop behavior under fault conditions |
| `incident-response` | Chaos experiments that hit abort criteria and cannot be contained escalate to incidents; hand off immediately |

---

## Anti-patterns

Refuse to produce experiment plans that exhibit these. Explain why and offer a corrected version.

- **No hypothesis** — "let's break things and see what happens" is sabotage, not engineering.
- **No steady-state metric** — without a pre-experiment baseline, there is no way to know if anything broke.
- **No blast radius bound** — a full-production experiment with no traffic limit is an outage waiting for a name.
- **No abort criteria** — mandatory, not optional. Propose defaults if the user hasn't provided them.
- **No on-call coverage** — chaos without monitoring is just unmonitored production.
- **Chaos in staging only** — staging never replicates production failure modes; findings are misleading.
- **Chaos in dev** — completely useless; dev has nothing in common with production failure behavior.
- **One-off experiments** — a single chaos experiment is a press release; learning requires recurrence.
- **Blame-laden postmortem** — record system causes, not individual fault; teams stop running chaos if postmortems assign blame.

---

## Verifiable outcomes

A team using this skill correctly should reach:

- 100% of experiments have a written hypothesis, concrete abort criteria, and a blast-radius calculation
- No single experiment consumes > 10% of monthly error budget (GREEN risk score)
- Mean time between experiments < 14 days (continuous, not one-off)
- Each experiment produces ≥ 1 follow-up action that gets shipped
- Zero chaos experiments escalate to customer-impacting incidents in the trailing 90 days

---

## Reference map

Read on demand, not upfront:

- `references/chaos_principles.md` — the 4 principles, history, when to start chaos engineering
- `references/experiment_design.md` — hypothesis structure, steady-state metrics, abort criteria patterns
- `references/attack_taxonomy.md` — 7 attack types with tooling flags, magnitudes, and worked examples
- `references/tooling_landscape.md` — Chaos Toolkit / Mesh / Litmus / Gremlin / FIS trade-off analysis

Templates:
- `assets/experiment_template.md` — blank fill-in experiment plan
- `assets/postmortem_template.md` — blank fill-in postmortem
