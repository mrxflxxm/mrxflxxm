#!/usr/bin/env python3
import os
import math
import requests
from datetime import datetime, timedelta

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
USERNAME = 'mrxflxxm'
OUTPUT = 'coding-card.svg'

HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json',
}

QUERY = '''
{
  user(login: "mrxflxxm") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
'''


def get_stats():
    try:
        resp = requests.post(
            'https://api.github.com/graphql',
            json={'query': QUERY},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        cal = resp.json()['data']['user']['contributionsCollection']['contributionCalendar']
    except Exception as e:
        print(f'GitHub API error: {e}')
        return {'total': 0, 'streak': 0, 'week': 0, 'best_day': 'Mon'}

    days = [d for week in cal['weeks'] for d in week['contributionDays']]
    total = cal['totalContributions']

    today = datetime.utcnow().date()

    # current streak
    streak = 0
    for day in sorted(days, key=lambda d: d['date'], reverse=True):
        d = datetime.strptime(day['date'], '%Y-%m-%d').date()
        if d > today:
            continue
        if day['contributionCount'] > 0:
            streak += 1
        else:
            break

    # commits this week
    week = sum(
        d['contributionCount']
        for d in days
        if datetime.strptime(d['date'], '%Y-%m-%d').date() >= today - timedelta(days=6)
    )

    # most active weekday
    day_totals = [0] * 7
    for d in days:
        day_totals[d['weekday']] += d['contributionCount']
    best_day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day_totals.index(max(day_totals))]

    return {'total': total, 'streak': streak, 'week': week, 'best_day': best_day}


def radar_polygon(cx, cy, r, values):
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        angle = math.pi * 2 * i / n - math.pi / 2
        pts.append(f'{cx + r * v * math.cos(angle):.1f},{cy + r * v * math.sin(angle):.1f}')
    return ' '.join(pts)


def label_anchor(lx, cx):
    if lx < cx - 8:
        return 'end'
    if lx > cx + 8:
        return 'start'
    return 'middle'


def generate_svg(stats):
    W, H = 820, 400

    skills = [
        ('PHP/Laravel', 0.90),
        ('C# / .NET',   0.80),
        ('SQL',         0.92),
        ('Redis',       0.70),
        ('Docker',      0.65),
        ('Payments',    0.85),
    ]
    n = len(skills)
    cx, cy, r = 195, 218, 118

    now = datetime.utcnow().strftime('%Y-%m-%d  %H:%M UTC')

    # ── SVG open + defs ──────────────────────────────────────────────────────
    svg = f'''\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <filter id="glow" x="-15%" y="-15%" width="130%" height="130%">
      <feGaussianBlur stdDeviation="2.8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      @keyframes pulse  {{ 0%,100%{{opacity:.55}} 50%{{opacity:1}} }}
      @keyframes fadein {{ from{{opacity:0}} to{{opacity:1}} }}
      @keyframes draw   {{ from{{stroke-dashoffset:1800}} to{{stroke-dashoffset:0}} }}
      .dot  {{ animation: pulse 2.2s ease-in-out infinite; }}
      .d1   {{ animation-delay:.55s }}
      .d2   {{ animation-delay:1.1s }}
      .fi   {{ animation: fadein .6s ease both }}
      .rv   {{ stroke-dasharray:1800; stroke-dashoffset:1800;
               animation: draw 1.6s .3s cubic-bezier(.4,0,.2,1) forwards }}
    </style>
  </defs>

  <!-- background -->
  <rect width="{W}" height="{H}" rx="12" fill="#0D1117"/>
  <rect width="{W}" height="{H}" rx="12" fill="none" stroke="#6C63FF" stroke-width="1.3" filter="url(#glow)"/>

  <!-- title bar -->
  <rect width="{W}" height="38" rx="12" fill="#161b22"/>
  <rect y="28"  width="{W}" height="10"  fill="#161b22"/>
  <rect y="38"  width="{W}" height="1"   fill="#30363d"/>
  <circle cx="20" cy="19" r="5.5" fill="#FF5F57"/>
  <circle cx="38" cy="19" r="5.5" fill="#FFBD2E"/>
  <circle cx="56" cy="19" r="5.5" fill="#28C840"/>
  <text x="{W//2}" y="24" text-anchor="middle"
        font-family="Courier New,Courier,monospace" font-size="11" fill="#8b949e"
  >coding-dna.svg — {now}</text>

  <!-- panel divider -->
  <line x1="395" y1="48" x2="395" y2="{H - 30}" stroke="#30363d" stroke-width="1"/>

  <!-- ── LEFT: radar ─────────────────────────────────────────── -->
  <text x="{cx}" y="64" text-anchor="middle"
        font-family="Courier New,Courier,monospace" font-size="10.5" fill="#8b949e"
  >▸ skill radar</text>
'''

    # grid rings
    for level in (0.33, 0.66, 1.0):
        pts = radar_polygon(cx, cy, r, [level] * n)
        op = 0.12 + level * 0.08
        svg += f'  <polygon points="{pts}" fill="none" stroke="#6C63FF" stroke-width="0.7" opacity="{op:.2f}"/>\n'

    # axis lines
    for i in range(n):
        angle = math.pi * 2 * i / n - math.pi / 2
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        svg += f'  <line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#312e81" stroke-width="0.7"/>\n'

    # value polygon (animated)
    vpts = radar_polygon(cx, cy, r, [v for _, v in skills])
    svg += f'  <polygon points="{vpts}" fill="#6C63FF" fill-opacity="0.18" stroke="#A855F7" stroke-width="1.6" class="rv" filter="url(#glow)"/>\n'

    # dot at each vertex
    for i, (_, v) in enumerate(skills):
        angle = math.pi * 2 * i / n - math.pi / 2
        dx = cx + r * v * math.cos(angle)
        dy = cy + r * v * math.sin(angle)
        svg += f'  <circle cx="{dx:.1f}" cy="{dy:.1f}" r="3.2" fill="#A855F7" class="dot fi" filter="url(#glow)"/>\n'

    # axis labels
    for i, (name, _) in enumerate(skills):
        angle = math.pi * 2 * i / n - math.pi / 2
        lx = cx + (r + 22) * math.cos(angle)
        ly = cy + (r + 22) * math.sin(angle)
        anchor = label_anchor(lx, cx)
        svg += (f'  <text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle"'
                f' font-family="Courier New,Courier,monospace" font-size="10" fill="#C4B5FD">{name}</text>\n')

    # ── RIGHT: stats ─────────────────────────────────────────────────────────
    sx = 418
    bw, bh, gap = 152, 70, 10

    def stat_box(bx, by, value, label, color):
        return (
            f'  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="7" fill="#161b22" stroke="#30363d" stroke-width="1"/>\n'
            f'  <text x="{bx + bw//2}" y="{by + 38}" text-anchor="middle"'
            f' font-family="Courier New,Courier,monospace" font-size="26" fill="{color}" filter="url(#glow)">{value}</text>\n'
            f'  <text x="{bx + bw//2}" y="{by + 58}" text-anchor="middle"'
            f' font-family="Courier New,Courier,monospace" font-size="10" fill="#8b949e">{label}</text>\n'
        )

    svg += f'  <text x="{sx}" y="64" font-family="Courier New,Courier,monospace" font-size="10.5" fill="#8b949e">▸ github stats</text>\n'
    svg += stat_box(sx,          76, stats['streak'],   'current streak',      '#A855F7')
    svg += stat_box(sx + bw + gap, 76, stats['week'],   'commits this week',   '#6C63FF')
    svg += stat_box(sx,          76 + bh + gap, stats['total'],  'total contributions', '#7EE787')
    svg += stat_box(sx + bw + gap, 76 + bh + gap, stats['best_day'], 'most active day', '#F2CC60')

    # ── Currently Building ───────────────────────────────────────────────────
    bby = 76 + (bh + gap) * 2 + gap
    cbh = H - 30 - bby - 8
    svg += f'''\
  <rect x="{sx}" y="{bby}" width="{bw*2 + gap}" height="{cbh}" rx="7" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="{sx + 12}" y="{bby + 20}" font-family="Courier New,Courier,monospace" font-size="10.5" fill="#8b949e">⚡ currently building</text>

  <circle cx="{sx + 18}" cy="{bby + 42}" r="4" fill="#A855F7" class="dot"/>
  <text x="{sx + 32}" y="{bby + 46}" font-family="Courier New,Courier,monospace" font-size="11" fill="#79C0FF">payment-gateway-3ds</text>
  <text x="{sx + 32}" y="{bby + 59}" font-family="Courier New,Courier,monospace" font-size="9.5" fill="#8b949e">Laravel · Stripe · ArCa · 3DS v2</text>

  <circle cx="{sx + 18}" cy="{bby + 82}" r="4" fill="#6C63FF" class="dot d1"/>
  <text x="{sx + 32}" y="{bby + 86}" font-family="Courier New,Courier,monospace" font-size="11" fill="#79C0FF">analytics-dashboard</text>
  <text x="{sx + 32}" y="{bby + 99}" font-family="Courier New,Courier,monospace" font-size="9.5" fill="#8b949e">Blazor WASM · ApexCharts · Excel</text>

  <circle cx="{sx + 18}" cy="{bby + 122}" r="4" fill="#58A6FF" class="dot d2"/>
  <text x="{sx + 32}" y="{bby + 126}" font-family="Courier New,Courier,monospace" font-size="11" fill="#79C0FF">auth-service</text>
  <text x="{sx + 32}" y="{bby + 139}" font-family="Courier New,Courier,monospace" font-size="9.5" fill="#8b949e">ASP.NET Core · JWT · Redis</text>
'''

    # ── bottom bar ───────────────────────────────────────────────────────────
    svg += f'''\
  <rect y="{H - 30}" width="{W}" height="30" rx="12" fill="#1e1b4b"/>
  <rect y="{H - 30}" width="{W}" height="2"  fill="#312e81"/>
  <text x="14" y="{H - 11}" font-family="Courier New,Courier,monospace" font-size="10" fill="#A855F7">[coding-dna]</text>
  <circle cx="106" cy="{H - 16}" r="3.5" fill="#7EE787" class="dot"/>
  <text x="116" y="{H - 11}" font-family="Courier New,Courier,monospace" font-size="10" fill="#C4B5FD">active</text>
  <text x="{W - 14}" y="{H - 11}" text-anchor="end"
        font-family="Courier New,Courier,monospace" font-size="10" fill="#6C63FF"
  >mrxflxxm · Asia/Yerevan</text>
</svg>'''

    return svg


def main():
    print('Fetching GitHub stats...')
    stats = get_stats()
    print(f'  streak={stats["streak"]}  week={stats["week"]}  total={stats["total"]}  best={stats["best_day"]}')
    svg = generate_svg(stats)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'Generated {OUTPUT}')


if __name__ == '__main__':
    main()
