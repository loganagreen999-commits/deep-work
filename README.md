# Deep Work

A focus timer that is honest about what it can and cannot do.

You name the assignment, say how long you think the work needs, set a session
length, and start the clock. The phone shows one screen: the task and a
countdown. Afterwards it tells you the thing nobody tracks — how long that
"twenty minute" assignment actually took.

## The blocking problem, stated plainly

**No web app can block apps on an iPhone.** Neither can a native app, unless
Apple grants it the `com.apple.developer.family-controls` entitlement, which
needs a Mac, a paid developer account and Apple's approval — and even then a
user can revoke it from Settings in one tap.

So this app does not pretend to block your phone. It uses the one thing on iOS
that genuinely cannot be escaped:

> **Guided Access** — Settings › Accessibility › Guided Access. Turn it on, set
> a passcode. Then triple-click the side button inside any app and iOS locks the
> phone to that app until the passcode is entered.

Start a session, triple-click, and the phone *is* the countdown until the time
is up. That is the whole design: this app is the thing you get locked into.

Guided Access also has its own time limit (Options › Time Limit) if you would
rather it end the lock for you.

## The laptop half

`focus.py` blocks distracting sites on the laptop for the length of a session,
because there the blocking can be real.

    ./focus.py start "Controls lab 2" 45 --est 20 --course "EEL 4657C"
    ./focus.py stop                # end early, unblock
    ./focus.py status
    ./focus.py stats
    ./focus.py serve               # serve the app on the LAN + accept the phone's sessions

Blocking rewrites the Windows hosts file, which needs Administrator, so one
elevated helper is launched per session. It restores the file when the clock
runs out, or sooner if `focus stop` drops the stop flag — **one UAC prompt per
session, not two**. Edit `blocklist.txt` to taste; `www.` and `m.` variants are
added for you.

If the laptop is killed mid-session the helper still restores the hosts file on
its own deadline, so you cannot be left permanently blocked.

## Starting both halves with one tap

An https page may not call a plain-http address on your own network — browsers
block it as mixed content, and `localhost` is the only exemption. So the app
cannot start the laptop's block by itself, and the sync field only works when
the app was opened from the laptop. It says so now rather than failing quietly.

**Shortcuts is not a browser and is not bound by that rule.** Run `focus serve`
and it prints the exact recipe, with your laptop's address filled in:

    1  Get Contents of URL   http://<laptop>:8777/api/live
         Method POST, Request Body JSON:
           action   text    start
           minutes  number  45
           task     text    Ask Each Time
    2  Open URLs             https://loganagreen999-commits.github.io/deep-work/

Name it Focus and put it on your home screen. One tap asks what you are working
on, arms the site block on the laptop, and opens the timer ready to start. Then
triple-click for Guided Access as usual.

`POST /api/live` with `{"action":"stop"}` ends it early and unblocks; `GET
/api/live` reports what is running and how long is left.

## Sharing one log

Both halves write the same session shape. Run `focus serve` on the laptop, paste
the printed address into the phone's Stats tab, and the phone uploads any
sessions the laptop has not seen whenever it can reach it. Deduplicated by id,
so uploading twice is harmless. Everything works fully offline without it — the
sync is a convenience, never a dependency.

## What it measures

- **Streak** of completed sessions. Ending early breaks it — unless you ended
  early because you *finished*, which is a win and is treated as one.
- **Why you stopped**, from a one-tap list. The point is to find out whether it
  is really the phone, or being stuck, or being tired.
- **Estimate against actual**, per assignment and as a single multiplier. If you
  say twenty minutes and it takes an hour, that ratio is the number worth knowing.
- **How many times you left the app** mid-session, from the page visibility API.
  Honest accountability for the sessions you run without Guided Access — and
  impossible to trigger during one, which is rather the point.

## Storage

Everything is in the phone's `localStorage` (`fx.sessions`, `fx.tasks`, `fx.cfg`,
`fx.live`) and, on the laptop, `state/sessions.json`. A session in progress
survives a reload, a crash or the battery dying: reopen and it either resumes or
is credited in full if the clock already ran out.

Fonts are self-hosted and the service worker caches the shell, so the app opens
with no network at all.

## Breaks

A break is offered after every session, but only with a length attached. It runs
on the same locked screen, so staying in Guided Access through the break is the
whole idea — the break cannot quietly become an hour of scrolling. When it ends
it rings, and the screen that replaces it does not go away on its own: it says
how far past the end you are and offers exactly two answers, back to work or
hold to stop for the day. If the phone was in your pocket when the break ran
out, the overrun is measured from when it *should* have ended, so Stats can tell
you the true length of your five minute breaks.

## The Plan tab: being where you said you would be

iOS gives a web app **no background location** — only a reading taken while the
app is open in front of you. So nothing here polls, and nothing is tracked
between checks. A block is checked at exactly two moments, and an iPhone
automation supplies both.

Add a block (name, kind, days, start and end, and a place captured by standing
there and tapping **Use my location now**), then open it and tap **Shortcut
links for this block**. You get two URLs. In the Shortcuts app:

    Automation › + › Arrive › pick the place › Next
      › New Blank Automation › Open URL › paste the arrive link
      › turn on Run Immediately

    ...and again with Leave, using the depart link.

From then on, walking into the library opens the app, it takes one fix, and:

- **You are there, and it is a study block** → a screen you cannot dismiss. Start
  a session, or hold the button down to record a skip. That is the accountability.
- **You are not there** → logged as a miss, with how far away you actually were.
- **You leave** → logged, and any running session is closed.

Each block then carries its own record: made 5 of 9, average 34 minutes late.

It catches skipping and lateness. It does not catch sitting in the building
doing nothing, and it only catches leaving early if you set up the leave
automation. That is the honest boundary of what the phone will allow.

## youtube-blinders/

An unpacked Chrome extension that leaves YouTube with a search bar and a player.
Hidden: the home feed (replaced with a full stop), the recommendation sidebar,
end screens and cards, Shorts, comments, the left rail, notifications. Each is a
separate toggle in the popup, and turning it off restores YouTube instantly with
no reload.

Install: `chrome://extensions` › Developer mode › **Load unpacked** ›
pick `youtube-blinders/`.

### Installing the extension the easy way

    ~/focus/install-extension.sh

It copies the folder to your Windows Desktop and opens Chrome's extensions page.
Then: **Developer mode** on (top right) › **Load unpacked** › pick the
`youtube-blinders` folder on the Desktop › done.
