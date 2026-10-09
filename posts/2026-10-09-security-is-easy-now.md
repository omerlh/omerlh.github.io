# I Had an AI Pen-Test a Shop While I Watched. Security Got Easy When I Wasn't Looking.

*Subtitle: Secret scanning, dependency checks and a web security scan: an afternoon each, or less.*

---

For years, "do security properly" meant a long list of things I would get to next quarter.

Set up scanning. Learn a proxy tool. Click through the whole app by hand, slowly, while a second window fills with alerts nobody reads. I knew what good looked like. I also knew I wasn't going to do it on a Tuesday evening.

Then I noticed something: the tedious part, the *clicking around*, is exactly what an AI agent is good at. And the rest has been getting cheaper for a while, quietly.

## I've been here before

In 2018 I wrote [Want to Write Good Code? Start Using Security Tests](../../archive/write-good-code-with-security-tests/), arguing that you should wire security checks into your pipeline. Two months later I pointed the tools at the same deliberately broken shop in [Hacking Juice Shop, the DevSecOps Way](../../archive/hacking-juice-shop-the-devsecops-way/). In 2019 I was still [hand-wiring ZAP as a proxy](../../archive/debugging-ios-apps-with-zaproxy/) just to see my own traffic. And I spent a lot of words on [whether we even need threat modeling](../../archive/do-we-really-need-threat-modeling/) and on [doing it as code](../../archive/threat-modeling-as-code/).

Eight years ago that took a weekend of YAML, Docker flags and patience. Today it boils down to one line to install and one paragraph to ask.

## Layer one: don't leak things

This website is a static folder of Markdown on GitHub Pages. Nothing to hack, you'd think. But a repo can still leak, so it has three guards:

- **[Gitleaks](https://github.com/gitleaks/gitleaks)** runs in CI and fails the build if a secret sneaks into a commit.
- **[Snyk](https://snyk.io)** is connected through its GitHub integration and checks dependencies and code.
- **`main` is protected.** Everything goes through a pull request, and every GitHub Action is pinned to a commit SHA, so a compromised tag can't swap code under me.

Setup time for all of it: an afternoon, most of it reading docs. Running cost: zero attention, until something is actually wrong.

## Layer two: the part I always skipped

Scanning code is the easy half. The half I never did was testing a *running* app, because it needs a human to use it like a user would: register, log in, search, fill a basket. That's what makes the scanner see real traffic.

So I built a small thing. [**zap-mcp**](https://github.com/omerlh/zap-mcp) is an [MCP](https://modelcontextprotocol.io) server with three tools:

| Tool | What it does |
|---|---|
| `zap_start` | Starts [ZAP](https://www.zaproxy.org) in Docker as a proxy |
| `zap_get_alerts` | Returns what ZAP found, grouped and sorted by risk |
| `zap_stop` | Cleans up |

The agent drives a real browser *through* ZAP. ZAP quietly watches every request and response. There's no attacking: it's passive scanning only, so it's safe by default. Then the agent reads the alerts and tells me what matters.

Installing it is one line:

```bash
claude mcp add zap -- npx -y github:omerlh/zap-mcp
```

## The test drive

I pointed it at [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/), a shop that is vulnerable on purpose, so nobody gets hurt. The instruction was roughly: *register a user, log in, search, add things to the basket, open the profile, then triage what ZAP found.*

The browsing produced **63 alerts**. That is exactly the number at which a human closes the tab.

The server groups alerts by type, so those 63 became **7 findings**:

- Permissive CORS (`Access-Control-Allow-Origin: *`) across 27 URLs
- No Content Security Policy
- A session ID travelling in the URL
- A private IP address leaking from an admin endpoint
- A few missing headers and timestamp disclosures

The second half of the problem is the report, so the server also ships a triage skill. It classifies each finding as real, noise or needs-verification, rates it with the [OWASP Risk Rating Methodology](https://owasp.org/www-community/OWASP_Risk_Rating_Methodology) (likelihood times impact), and writes a short report with evidence and a concrete fix for each item. Same Juice Shop run, but now the output is something I could hand to a developer.

Seven things is a to-do list. Sixty-three is a wall. The grouping did more for me than any clever scanning trick: it turned the output into something an agent, or a person, can actually triage.

## What actually changed

Nothing here is new science. ZAP is old. Secret scanners are old. What changed is the cost of the boring bit:

1. **Setup collapsed.** One line to install a tool, one afternoon to wire CI.
2. **The manual labour moved to an agent.** It clicks, I read the summary.
3. **Output got shaped for triage,** which matters more than coverage, because a report nobody reads protects nothing.

There are limits, and they matter. Passive scanning finds hygiene problems, not deep logic bugs. It is a smoke detector, not a penetration test, and it only belongs on apps you're allowed to test. But a smoke detector in every house beats a fire inspector who visits once a year.

## Your turn

If you've been putting this off like I was, here's the smallest useful version:

1. Add a secret scanner to CI. Today.
2. Protect your main branch and pin your Actions.
3. Run the ZAP MCP against something that's yours, or against Juice Shop first.

Security used to feel like a project. It now feels like a habit you can start before lunch.
