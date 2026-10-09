# I Hired an AI to Hack a Shop While I Made Coffee. Security Got Easy When I Wasn't Looking.

*Subtitle: In 2018 it took me a weekend of YAML. Now it's one line and one paragraph.*

---

I asked my new employee to break into a web shop.

It registered an account. It logged in. It searched for juice, filled a basket, opened the profile page. Then it came back with a list: seven things to fix, ordered by how much they matter, each with a one-line reason.

I had a coffee in that time. Not a good one. It was still too hot to drink, which is more patience than I've ever shown a scanner.

I come from application security, so I don't say this lightly: **the hardest part of security used to be getting started. That part is mostly gone.**

## I've been here before

In 2018 I wrote [Want to Write Good Code? Start Using Security Tests](../../archive/write-good-code-with-security-tests/), arguing that security checks belong in the pipeline. Two months later I pointed the tools at a deliberately broken shop in [Hacking Juice Shop, the DevSecOps Way](../../archive/hacking-juice-shop-the-devsecops-way/). In 2019 I was still [hand-wiring ZAP as a proxy](../../archive/debugging-ios-apps-with-zaproxy/) just to see my own traffic. And I spent an unreasonable number of words on [whether we even need threat modeling](../../archive/do-we-really-need-threat-modeling/), and then on [doing it as code](../../archive/threat-modeling-as-code/).

Eight years ago, that was a weekend of YAML, Docker flags and patience. A weekend I would otherwise have spent playing Civilization VII, so honestly, a loss for no one. (My CFO still says to wait for a sale.)

Today it boils down to this: **one line to install, one paragraph to ask.**

## Layer one: don't leak things

This website is a folder of Markdown on GitHub Pages. Nothing to hack, you'd think. But a repo can still leak, so it has three guards:

- **[Gitleaks](https://github.com/gitleaks/gitleaks)** runs in CI and fails the build if a secret sneaks into a commit.
- **[Snyk](https://snyk.io)** is connected through its GitHub integration and watches dependencies and code.
- **`main` is protected.** Everything goes through a pull request, and every GitHub Action is pinned to a commit SHA, so a compromised tag can't swap the code under me.

Setup time: an afternoon, most of it spent reading docs and pretending I'd already read them. Running cost: zero attention, until something is actually wrong.

That's the right shape for security: **silent when boring, loud when it matters.**

## Layer two: the part I always skipped

Scanning code is the easy half. The half I never did was testing a *running* app, because it needs someone to use it like a user would: register, log in, search, fill a basket. That's how a scanner sees real traffic.

It's also the most tedious job in security. For years my plan was "I'll do it next quarter." I have been saying next quarter since 2018. Which makes it a perfect job for an agent: it doesn't procrastinate, and it doesn't need a snack.

So I built [**zap-mcp**](https://github.com/omerlh/zap-mcp), a small [MCP](https://modelcontextprotocol.io) server with three tools:

| Tool | What it does |
|---|---|
| `zap_start` | Starts [ZAP](https://www.zaproxy.org) in Docker as a proxy |
| `zap_get_alerts` | Returns what ZAP found, grouped and sorted by risk |
| `zap_stop` | Cleans up |

The agent drives a real browser *through* ZAP. ZAP quietly watches every request and response. Nothing is attacked: it's passive scanning only, so it's safe by default.

Installing it is one line:

```bash
claude mcp add zap -- npx -y github:omerlh/zap-mcp
```

## The test drive

I pointed it at [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/), a shop that is vulnerable on purpose, so nobody gets hurt. My instruction, roughly: *register a user, log in, search, add things to the basket, open the profile, then tell me what matters.*

The browsing produced **63 alerts**. That is exactly the number at which a human closes the tab and remembers an urgent errand.

The server groups alerts by type, so the 63 became **7 findings**:

- Permissive CORS (`Access-Control-Allow-Origin: *`) across 27 URLs
- No Content Security Policy
- A session ID travelling in the URL
- A private IP address leaking from an admin endpoint
- A few missing headers and timestamp disclosures

Seven things is a to-do list. Sixty-three is a wall. **The grouping did more for me than any clever scanning trick.**

## Finding things is half the job

A list of findings isn't a report. It's homework you assign yourself.

So the repo also ships a **triage skill**. For each finding it decides: real, noise, or *needs a human to check*. Then it rates the real ones with the [OWASP Risk Rating Methodology](https://owasp.org/www-community/OWASP_Risk_Rating_Methodology): how likely is it, how bad would it be, so what do I fix first? And it writes a short report with the evidence and a concrete fix for each item.

Three things I like about it:

- **It rates in context.** ZAP rates the *type* of issue. The skill asks what it means *in this app*.
- **It says what it didn't test.** Passive scanning sees only the pages it visited, and the report says so up front.
- **It never calls a guess a fact.** "Needs verification" is a respectable answer. I know people who've never said it. I am, on a bad day, one of them.

Same Juice Shop run, but now the output is something I could hand to a developer without a meeting.

## What actually changed

Nothing here is new science. ZAP is old. Secret scanners are old. What changed is the cost of the boring bit:

1. **Setup collapsed.** One line to install a tool, one afternoon to wire CI.
2. **The manual labour moved to an agent.** It clicks, I read the verdict.
3. **The output got shaped for decisions.** A report nobody reads protects nothing.

There are limits, and they matter. Passive scanning finds hygiene problems, not deep logic bugs. It's a smoke detector, not a penetration test, and it belongs only on apps you're allowed to test. But a smoke detector in every house beats a fire inspector who visits once a year.

## Steal this

If you've been putting this off like I was, here's the smallest useful version:

1. **Add a secret scanner to CI.** Today. It takes less time than reading this post, and I'm not even sorry about the length.
2. **Protect `main` and pin your Actions.** Make the safe path the only path.
3. **Run the ZAP MCP against Juice Shop first.** Then against something that's yours.

Security used to feel like a project. It now feels like a habit you can start before lunch.

*Next: giving the same agent a harder job than clicking around. I'm told that's how it starts.*

*What's the security task you keep postponing? Tell me, and I'll tell you if an agent can take it.*
