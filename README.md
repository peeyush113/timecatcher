# timecatcher

A goal-focused Pomodoro timer for the terminal. Open source, local-first — no cloud, no accounts.

```
╔══════════════════════════════════════════════════════════════╗
║  timecatcher       Mon 19 May              Streak: 7 days    ║
╠══════════════════╦═══════════════════════╦═══════════════════╣
║  ACTIVE SESSION  ║   TODAY'S GOALS       ║   FOCUS SCORE     ║
║                  ║                       ║                   ║
║   Write Thesis   ║  ● Write Thesis  80%  ║  ▁▃▅▇▆▅▇█  7.8   ║
║   Ch.2 outline   ║  ████████░░           ║   last 8 sessions ║
║                  ║                       ║                   ║
║   ╔══════════╗   ║  ○ Review PRs   30%   ║  WEEKLY GOAL      ║
║   ║  18:42   ║   ║  ███░░░░░░░           ║  12h / 20h target ║
║   ╚══════════╝   ║                       ║  ████████░░░░░    ║
║   Pomodoro 3/4   ║                       ║                   ║
║  [P]ause [S]top  ║                       ║                   ║
╚══════════════════╩═══════════════════════╩═══════════════════╝
```

## Features

- **Pomodoro-first** — 25/5/15 cycles with intent setting before each session
- **Goal-focused** — every session is tied to a goal; track progress toward targets
- **Rich dashboard** — live timer, goal progress bars, focus sparkline, session timeline
- **Reflection prompts** — capture what you accomplished and rate focus after each session
- **Analytics** — daily charts, contribution heatmap, streaks, completion rates
- **Local-first** — all data in `~/.timetracker/data.db` (SQLite), no accounts needed
- **Sync-friendly** — place `~/.timetracker/` in Dropbox/Syncthing to sync across machines

## Install

```bash
pip install timecatcher
```

Or from source:

```bash
git clone https://github.com/peeyush113/timecatcher
cd timecatcher
pip install -e .
```

## Run

```bash
tt
```

## Keys

| Key | Action |
|-----|--------|
| `n` | Start new Pomodoro session |
| `p` | Pause / Resume timer |
| `s` | Abandon current session |
| `d` | Dashboard |
| `g` | Goals |
| `a` | Analytics |
| `h` | History |
| `q` | Quit |

## Data

All data is stored in `~/.timetracker/data.db` (SQLite). To sync between machines, symlink or place this directory inside Dropbox, iCloud Drive, or Syncthing — no account or server required.

## License

MIT
