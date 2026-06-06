import os
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "ashinbabu"

# GraphQL Query to fetch user stats
# - Uses stargazerCount across owned repos (not starredRepositories which counts repos YOU starred)
# - Uses contributionsCollection.repositoriesWithContributedCommits for "Contributed to"
QUERY = """
query {
  user(login: "%s") {
    name
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalRepositoriesWithContributedCommits
    }
    pullRequests(states: [OPEN, CLOSED, MERGED]) {
      totalCount
    }
    issues(states: [OPEN, CLOSED]) {
      totalCount
    }
  }
}
""" % USERNAME


def fetch_stats():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY},
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(
            f"Query failed with status {response.status_code}. Response: {response.text}"
        )

    data = response.json()
    if "errors" in data:
        print(data)
        raise Exception("GraphQL query failed: " + str(data["errors"]))

    user = data["data"]["user"]

    # Fix: sum stargazerCount across all owned public repos (not repos the user starred)
    total_stars = sum(
        repo["stargazerCount"]
        for repo in user["repositories"]["nodes"]
    )

    contributions = user["contributionsCollection"]
    total_commits = (
        contributions["totalCommitContributions"]
        + contributions["restrictedContributionsCount"]
    )
    total_prs = user["pullRequests"]["totalCount"]
    total_issues = user["issues"]["totalCount"]

    # Fix: use actual distinct repos contributed to, not just commit count
    repos_contributed_to = contributions["totalRepositoriesWithContributedCommits"]

    return {
        "stars": total_stars,
        "commits": total_commits,
        "prs": total_prs,
        "issues": total_issues,
        "repos": user["repositories"]["totalCount"],
        "contribs": repos_contributed_to,
    }


def generate_svg(stats):
    # Dracula color palette
    BG_COLOR = "#282a36"
    TEXT_COLOR = "#f8f8f2"
    ACCENT_COLOR = "#bd93f9"   # Purple
    TITLE_COLOR = "#ff79c6"    # Pink
    BORDER_COLOR = "#44475a"
    DIM_COLOR = "#6272a4"      # Comment grey
    GREEN_COLOR = "#50fa7b"    # Green

    current_year = datetime.now().year

    def bar_width(value, max_val, max_px=200):
        if max_val == 0:
            return 0
        return min(int((value / max_val) * max_px), max_px)

    max_val = max(stats["commits"], stats["stars"], stats["contribs"], 1)

    rows = [
        ("⭐ Stars Earned",       stats["stars"],   ACCENT_COLOR),
        (f"💻 Commits ({current_year})", stats["commits"], GREEN_COLOR),
        ("🔀 Pull Requests",       stats["prs"],     "#ffb86c"),
        ("🐛 Issues",              stats["issues"],  "#ff5555"),
        ("📁 Repos",               stats["repos"],   "#8be9fd"),
        ("🤝 Contributed To",      stats["contribs"], "#50fa7b"),
    ]

    row_svgs = ""
    for i, (label, value, color) in enumerate(rows):
        y = 75 + i * 28
        bw = bar_width(value, max_val)
        row_svgs += f"""
      <!-- Row {i+1}: {label} -->
      <text x="25" y="{y}" class="stat label">{label}</text>
      <text x="310" y="{y}" class="stat value">{value}</text>
      <rect x="25" y="{y + 5}" width="{bw}" height="4" rx="2" fill="{color}" opacity="0.7"/>
      <rect x="25" y="{y + 5}" width="200" height="4" rx="2" fill="{BORDER_COLOR}" opacity="0.3"/>
"""

    svg_content = f"""<svg width="495" height="260" viewBox="0 0 495 260" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header   {{ font: 700 17px 'Segoe UI', Ubuntu, Sans-Serif; fill: {TITLE_COLOR}; }}
    .subhead  {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: {DIM_COLOR}; }}
    .stat     {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {TEXT_COLOR}; }}
    .label    {{ fill: {TEXT_COLOR}; }}
    .value    {{ font-weight: 700; fill: {ACCENT_COLOR}; text-anchor: middle; }}
  </style>

  <!-- Background -->
  <rect x="0.5" y="0.5" rx="8" height="99%" stroke="{BORDER_COLOR}" width="99%"
        fill="{BG_COLOR}" stroke-opacity="1" stroke-width="1.5"/>

  <!-- Accent top bar -->
  <rect x="0.5" y="0.5" rx="8" height="6" width="99%" fill="{TITLE_COLOR}" opacity="0.8"/>

  <!-- Title -->
  <text x="25" y="38" class="header">📊 {USERNAME}'s GitHub Stats</text>
  <text x="25" y="56" class="subhead">Auto-updated daily · Dracula theme</text>

  <!-- Divider -->
  <line x1="25" y1="65" x2="470" y2="65" stroke="{BORDER_COLOR}" stroke-width="1"/>

  {row_svgs}
</svg>"""

    os.makedirs("generated", exist_ok=True)
    with open("generated/stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)


if __name__ == "__main__":
    try:
        stats = fetch_stats()
        generate_svg(stats)
        print("✅ Generated generated/stats.svg successfully.")
        print(f"   Stars:        {stats['stars']}")
        print(f"   Commits:      {stats['commits']}")
        print(f"   PRs:          {stats['prs']}")
        print(f"   Issues:       {stats['issues']}")
        print(f"   Repos:        {stats['repos']}")
        print(f"   Contributed:  {stats['contribs']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
