Project purpose: optimises how an LLM does `autoresearch`.

## Taxonomy

**Scientist level:** Multiple **Scientists** (inner agents) each optimise a solver in their own `scientist/{problem}/train.py` through a series of **trials** (plan-run-reflect cycles). A full series of trials (e.g. 10) for one problem is a **study**.

**Supervisor level:** The **Supervisor** (outer agent) optimises `scientist/guidance.md` — generic research methodology guidance shared across all problems. The Supervisor's job is to find how to do autoresearch for any problem, by improving the output of all Scientists. It does this by repeating studies (where Scientists go from baseline as far as they can) with different guidance to see what techniques matter.