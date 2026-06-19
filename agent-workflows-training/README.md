# Agent Workflows Training

A hands-on path to understand **dynamic workflows** by building one tiny, runnable
example of each pattern — from a single API call up to a full autonomous agent.

Each lesson is a self-contained Python script that you can run on its own. They
all share one running theme: **turn a customer-support question into a good answer.**
You see how each pattern changes the same task.

## The patterns (run them in order)

| File | Pattern | New idea it adds |
|---|---|---|
| `lesson_0_single_call.py` | Single call | The baseline — one prompt, one answer |
| `lesson_1_prompt_chaining.py` | Prompt chaining | Fixed sequence; output of step N feeds step N+1 |
| `lesson_2_routing.py` | Routing | An agent classifies input and picks the path |
| `lesson_3_parallelization.py` | Parallelization | Run calls at once, then combine/vote |
| `lesson_4_generator_critic.py` | Generator–Critic | Produce → challenge → revise, looping until approved ⭐ |
| `lesson_5_tools_rag.py` | Tools & RAG | The agent retrieves from docs on demand |
| `lesson_6_orchestrator_workers.py` | Orchestrator–workers | Lead agent splits work at runtime, dispatches workers |
| `lesson_7_autonomous_agent.py` | Autonomous agent | Everything combined: research → draft → self-critique → loop |

Lesson 4 is the heart of your colleague's app ("agents to challenge it").
Lessons 5 + 6 are the "make content based on doc and code base" half.

## Static vs dynamic

- **Lessons 0–1** are *static*: the steps are fixed in advance.
- **Lessons 2, 4, 6, 7** are *dynamic*: the model decides what to do at runtime
  (which branch, how many revision rounds, which subtasks, which tools).

That shift — from a hardcoded path to one the model chooses — is what "dynamic
workflow" means.

## Setup

```bash
# 1. Install the one dependency
pip install -r requirements.txt

# 2. Provide your Anthropic API key (get one at https://console.anthropic.com)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Run any lesson
python lesson_0_single_call.py
python lesson_4_generator_critic.py
```

> **Running from a phone (Claude Code on the web):** you don't type any of this.
> Just tell Claude `run lesson 2` or `explain what lesson 4 is doing` and review the
> output. The only requirement is that this environment can reach `api.anthropic.com`
> and has `ANTHROPIC_API_KEY` set — if the network policy blocks it, the code is still
> here to read, it just can't execute.

## Models used

These lessons follow a cost-tiered convention (set in `common.py`):

- `FAST`  = `claude-haiku-4-5`  — cheap/fast steps (classification, simple sub-tasks)
- `SMART` = `claude-sonnet-4-6` — the reasoning steps (drafting, critiquing)
- `BEST`  = `claude-opus-4-8`   — swap any `SMART` to this for the hardest reasoning

Bump `SMART` up to `BEST` in `common.py` if you want maximum quality everywhere.
