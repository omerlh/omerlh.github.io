# Nobody Wanted My Threat Models in 2019. Then We Started Writing for Agents.

*Subtitle: In 2019 the hard part was never the method. It was getting anyone to write the thing down.*
*Title: Threat Modeling for AI Agents: Four Questions, One ADR*
*Description: Threat modeling never got buy-in. AI agents changed that. Use Shostack's four questions to review ADRs, run pre-mortems and validate agent-written code.*

---

In 2019 I booked a three-hour threat modeling session. Six people came. We drew a diagram, argued about one arrow, and ran out of time before anyone asked what could go wrong. That was the good session.

I believed in threat modeling then, and I could not make it stick. The method was fine. Everything around it wasn't.

**Short version:** AI agents turned threat modeling from a meeting into a section of the architecture decision record (ADR). Adam Shostack's four questions still do the work. They just got a reader that never gets tired.

## What is threat modeling, and why did it never get buy-in?

Threat modeling means asking Shostack's [four question framework](https://shostack.org/files/papers/The_Four_Question_Framework.pdf) about a system: what are we working on, what can go wrong, what are we going to do about it, and did we do a good job?

In 2019 that started with a long session. Get the right people in a room, draw the system, argue about what is in the diagram, run out of time, book a second session.

Then came the part nobody mentions in the talks: **chasing developers.** For the diagram, for the answers, for the follow-ups, for someone to fix what we found. Every session cost a few hours from several people with a deadline, and the output was a document that was stale by the next sprint.

So there was no buy-in. Why would there be? To a developer, threat modeling was a meeting that produced homework. I tried to fix it from the tooling side: I wrote about [threat modeling as code](../../archive/threat-modeling-as-code/), with the model in a repo and changes reviewed in PRs, and about [scaling it with templates](../../archive/do-we-really-need-threat-modeling/), after watching [Izar Tarandach's](https://www.oreilly.com/library/view/threat-modeling/9781492056546/) talk on doing it continuously.

Good ideas, both. Both had the same hole: **someone still had to write and maintain the thing.** The someone was me, and I ran out of hours. (Turns out "I'll update the model next quarter" ages exactly like "I'll run the scanner next quarter".)

## How do AI agents change threat modeling?

Something changed, and it had nothing to do with security.

Working with coding agents is mostly **writing**. You write the spec. You write the context. You write down the decisions, because an agent has no hallway to overhear them in. On my team we keep [architecture decision records](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), the format Michael Nygard proposed in 2011, in a repo for exactly this reason: they make the agent better. It reads why we chose this database, what we ruled out and what we agreed never to do before it writes a line. Duncan Davidson [makes the same case](https://duncandavidson.com/agents-love-decisions): decision records give coding agents the intent they would otherwise guess from the code.

That's the buy-in I never had: nobody needs convincing to document a system when the documentation makes the agent work better.

And the second realization: **an agent is also good at the part I ran out of hours for.** Given the code and a diff, it can draft the diagram, propose what can go wrong, and point out when a change touches something the model doesn't cover. (I'm not the only one trying: OWASP has an incubator project, [Let's Threat Model](https://owasp.org/www-project-lets-threat-model/), that takes an agentic approach to the same problem.) No scheduling, no chasing, and far less drift, because the reader checks every PR.

What I needed in 2019 wasn't a better tool. It was a reader that never gets tired, and a team that writes things down anyway.

## Are the four questions useful beyond threat modeling?

Yes. They turned out to be bigger than a threat modeling method. They fit any change, and with agents in the loop I use them three ways.

### A. To judge an ADR

An ADR says what we decided. The four questions say whether it's a good decision.

- *What are we working on?* Does the ADR say what system it affects and where the boundaries are?
- *What can go wrong?* Does it name failure modes, or only the happy path?
- *What are we going to do about it?* Is each risk mitigated, accepted on purpose, or ignored by accident?
- *Did we do a good job?* How would we know in six months that this was right?

An ADR that can't answer these isn't done. An agent can run this review on every ADR PR and never feels awkward asking.

### B. As a pre-mortem

Borrowing from Gary Klein's [pre-mortem](https://hbr.org/2007/09/performing-a-project-premortem), where the team imagines the project already failed and asks why, question two becomes something you ask *before* the work, not after the incident.

Before an agent starts a task that touches auth, data flows or anything external, it answers "what can go wrong?" first, from the ADRs. Humans skip this step under deadline pressure. An agent can be instructed not to, and a CI check can verify that it didn't.

### C. To define how we validate AI work

This is the one I care about most. If agents write more of our code, the review can't be "a human reads every line". Teams are already pushing that way: Simon Willison [describes](https://simonwillison.net/2026/Feb/7/software-factory/) StrongDM's "software factory", where specs and scenarios drive agents and a harness (the tests that grade the agent's work) checks the result.

In that world, question four is the whole game: **did we do a good job?** (Shostack meant it as a retrospective question. Turning it into a machine-checkable test is my extension.) Which mitigations must hold? Which scenarios must never happen? Those answers go in the repo as tests and checks, written before the work.

Instructions alone won't hold them. Claude Code's own docs say CLAUDE.md is [context, not enforced configuration](https://code.claude.com/docs/en/memory), and recommend a hook to block an action for certain. So question four needs real enforcement: CI, hooks, and branch protection with required reviewers on the checks themselves. An agent that can rewrite the check to make its own PR pass hasn't done a good job. It has gamed the grader.

## Threat modeling is dead. Long live threat modeling.

The version I tried to sell in 2019, the workshop, the whiteboard, the separate document, is dead. I don't miss it.

What replaces it is nothing fancy, and that's the point. For most changes there's no separate threat modeling *process*. There's a design, and the design carries its threat model the way it carries a database choice: **it's part of the design, not a separate activity.**

In the repo that means:

- **The four questions live inside the ADR.** What we're working on, what can go wrong, what we'll do about it, how we'll know. An ADR with an empty "what can go wrong" is an incomplete ADR.
- **Same PR as the decision.** Same markdown, same review, same people. Nobody schedules anything.
- **Read by the agent like everything else.** It's context for the next change, so drift gets noticed faster, though not always noticed.

Nothing new for the developer to learn or open. The threat model is inherited from the design, the way a service inherits its logging setup.

### A GitHub Action that reviews the ADR

The automation I wanted is small: a GitHub Action that runs Claude Code on PRs that add or change an ADR, asks the four questions, and comments with feedback. It's a reviewer, not a gate. It drafts, people decide.

I put a ready-to-use example on GitHub: [omerlh/adr-threat-review](https://github.com/omerlh/adr-threat-review). It's a starting point, not a copy of what runs at work. Ours has tweaks that fit our own repos and conventions, so treat this one as the simple version: copy the workflow, the prompt and the ADR template, and adjust them to your team.

To try it, I wrote ADRs for [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/), the shop that is vulnerable on purpose. ADR 0001 is a decent one: the server owns the basket, with tests. Then I opened [a pull request](https://github.com/omerlh/adr-threat-review/pull/1) with a deliberately lazy ADR 0002, "keep the session token in local storage", where the answer to "what can go wrong?" is "Nothing. This is how most single-page apps do it."

The review pushed back on every question. On question two it said the template already rules out "Nothing" as an answer, and listed what was missing: a script injected into the page reading the token, tokens valid until logout with no way to revoke them, and tokens left on shared machines. On question four it pointed out that "login works in the manual test" checks that login works, not that any risk is controlled.

The comment I liked best was one no single-ADR review would give, because it read the other ADR too:

> ADR 0001 mitigates a stolen token with "Session tokens expire, and checkout asks for the token again." ADR 0002's tokens that never expire break that mitigation.

Its verdict was "needs a human threat modeler", because the ADR puts a long-lived credential somewhere scripts can read it. That's the kind of catch that used to need the six people in the room.

It's one example on a toy repo, written by me to be flawed, so treat it as a demo, not a benchmark, and not a report on our production setup.

The safety defaults are in the README. It runs on `pull_request` only, skips fork PRs, has a token that can only comment, treats the ADR text as untrusted data, and pins every action to a commit SHA. It also has no API key: the job trades its GitHub OIDC token for a short-lived Claude token through workload identity federation, so there's no static secret to leak. One catch when I set it up: GitHub's token subject now carries numeric IDs, so a rule written with the repo name alone never matched.

## Where I'm still unsure

- **One ADR is not the whole system.** This is the weakest part of the argument. Trust boundaries, data flows that span services and risks that appear only when decisions combine are invisible in any single ADR. Each can pass the four questions while the system is still vulnerable. So I'd keep a thin system-level view (diagram, trust boundaries, assets) that the ADRs link to and the agent re-checks. "No separate process" is true for the delta, not for the whole picture.
- **Know when to call a human.** A new trust boundary, a new class of sensitive data or a new external exposure still deserves someone who threat models for a living.
- **Confident garbage.** An agent will write a polished model of a system it misunderstood. One [study of LLMs classifying 5G threats into STRIDE categories](https://arxiv.org/abs/2505.04101) found them useful but in need of human oversight. Humans still own questions one and two.
- **It's non-deterministic and it costs tokens.** The same ADR may get different feedback twice. That's fine for a reviewer, and a reason it can't be a gate.
- **Keep it boring on purpose.** A threat model describes where you're weak. No hostnames, credentials or anything you'd hate to see in a leaked repo.
- **Agents are a new attack surface.** Prompt injection and over-trusted tools need their own threat model. Shostack [argues](https://shostack.org/blog/threat-modeling-technique-survives-ai-disruption/) the questions still apply, and his [second edition](https://shostack.org/blog/threat-modeling-2nd-edition/), due in February 2027, adds chapters on using LLMs to threat model and on threats to LLMs. That's another post.

## Steal this

1. Add the four questions to your ADR template, so every decision answers them.
2. Have an agent review your next ADR PR against them, for example by copying [the example Action](https://github.com/omerlh/adr-threat-review) and adapting it. Fix what it got wrong; the correction is the valuable part.
3. Before an agent task on something sensitive, make it answer question two first.
4. Write question four as a check before the work starts, and protect that check with required reviewers.

In 2019 I couldn't get anyone to join the session. In 2026 the team writes the inputs every day, and the reader doesn't need a calendar invite.

*Related: [Security got easy](../security-is-easy-now/), where I let an agent test a web app with ZAP.*

*What was the longest threat modeling session you ever sat through? Tell me, and I'll tell you whether an agent could have done it.*
