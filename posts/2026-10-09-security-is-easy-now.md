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

## The real pain: the pile

Ask anyone who has run a security tool what they hate most. It's not the setup. It's the output.

Hundreds of alerts. Half of them noise, a quarter "informational," and the one that matters sits on page nine. So the report gets filed under "later," which is where security reports go to retire.

**The problem was never finding things. It was drowning in the list.**

This is where AI is genuinely good now. It doesn't get bored on alert 40. So the repo ships a **triage skill**, and it plays by the oldest rule in the trade: **PoC or GTFO.**

Every alert is a hypothesis. Before anything reaches the report, the agent tries to prove it: replays the request, looks at the real response, and keeps only what it can demonstrate. Then it rates what survived with the [OWASP Risk Rating Methodology](https://owasp.org/www-community/OWASP_Risk_Rating_Methodology): how likely, how bad, so what do I fix first?

- **No proof, no finding.** What it can't reproduce goes in a one-line "dismissed" list, not in my face.
- **Proof comes attached.** The request and the response, so a developer can see it in ten seconds without a meeting.
- **It admits what it couldn't verify.** "Unproven" is a respectable answer. I know people who've never said it. I am, on a bad day, one of them.

The proofs are minimal and read-only, on apps you own or are allowed to test. This isn't an attacker; it's the colleague who checks before filing the ticket.

The goal: 63 alerts in, a short report out, and every line in it something you can reproduce. **I can worry less, because the list is short and true.**

## Don't be the madman with the list

Security has an image problem. It's the person who shows up at the end, points at your code, and leaves a PDF.

In *[The Unicorn Project](https://itrevolution.com/product/the-unicorn-project/)*, the heroes win by making the right thing part of the daily flow, not a gate at the end of it. Security should work the same way. Nobody enjoys the outside madman pointing at issues. Everybody enjoys the teammate who sends a fix.

So the second prompt in the repo is for a **coding agent that lives in your repo**. Same idea as a bug-bot that fixes what it finds, but for a running app. Paste it in, and the loop goes:

1. Run the app and scan it through ZAP.
2. Prove each finding. PoC or GTFO.
3. Fix it on a branch, with a regression test.
4. Replay the proof to check the fix actually works. If the exploit still works, it isn't fixed.
5. Re-scan, then prepare a pull request with the before and after proof.

It never pushes until I say so, and it only touches a local or test app. It's not allowed to "fix" a finding by switching off the alert. (I've met humans who consider that a valid strategy.)

The pull request is the part I like. It doesn't say "your CORS is bad." It says "here was the request, here was the response, here is the change, here is the same request after." A reviewer can read that over coffee.

I'm not claiming a victory lap. At [Ledge](https://ledge.co) we have a nightly ZAP run set up as a Cursor automation, so the scan-and-prove half now happens while everyone sleeps, and the fixes are the experiment we're starting now. I'll write up what it gets right and what it gets embarrassingly wrong.

## What actually changed

Nothing here is new science. ZAP is old. Secret scanners are old. What changed:

1. **Setup collapsed.** One line to install a tool, one afternoon to wire CI.
2. **The manual labour moved to an agent.** It clicks, I read the verdict.
3. **The noise got a filter with a conscience.** Security tools used to hand you a list and a guilt trip. Now they hand you the five things that are real.

Limits, because there are always limits: passive browsing only finds what it visits, and proving a finding is not a full penetration test. It's a smoke detector that checks the fire before it screams. Still better than a fire inspector who visits once a year.

## Steal this

If you've been putting this off like I was, here's the smallest useful version:

1. **Add a secret scanner to CI.** Today. It takes less time than reading this post, and I'm not even sorry about the length.
2. **Protect `main` and pin your Actions.** Make the safe path the only path.
3. **Run the ZAP MCP against Juice Shop first.** Then against something that's yours.

Security used to feel like a project. It now feels like a habit you can start before lunch.

*Next: I let the agent fix a whole app and report back. I'm told this is how it starts.*

*What's the security task you keep postponing? Tell me, and I'll tell you if an agent can take it.*
