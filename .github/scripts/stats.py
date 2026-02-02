import os
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "ashinbabu"

# GraphQL Query to fetch user stats
QUERY = """
query {
  user(login: "%s") {
    name
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
      totalCount
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    pullRequests(first: 1) {
      totalCount
    }
    issues(first: 1) {
      totalCount
    }
    starredRepositories {
      totalCount
    }
  }
}
""" % USERNAME

def fetch_stats():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.post("https://api.github.com/graphql", json={"query": QUERY}, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {QUERY}")
        
    data = response.json()
    if "errors" in data:
      print(data)
      raise Exception("GraphQL query failed")
      
    user = data["data"]["user"]
    
    # Calculate stats
    total_stars = user["starredRepositories"]["totalCount"]
    total_commits = user["contributionsCollection"]["totalCommitContributions"] + user["contributionsCollection"]["restrictedContributionsCount"]
    total_prs = user["pullRequests"]["totalCount"]
    total_issues = user["issues"]["totalCount"]
    total_contribs = total_commits # Simplified for now, often includes PRs/Issues
    
    return {
        "stars": total_stars,
        "commits": total_commits,
        "prs": total_prs,
        "issues": total_issues,
        "contribs": total_contribs
    }

def generate_svg(stats):
    # Dracula Colors
    BG_COLOR = "#282a36"
    TEXT_COLOR = "#f8f8f2"
    ICON_COLOR = "#bd93f9" # Purple
    TITLE_COLOR = "#ff79c6" # Pink
    BORDER_COLOR = "#44475a"
    
    svg_content = f"""
    <svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
      <style>
        .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {TITLE_COLOR}; }}
        .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {TEXT_COLOR}; }}
        .stagger {{ animation: fadeInAnimation 0.8s ease-in-out forwards; }}
        @keyframes fadeInAnimation {{ from {{ opacity: 0; transform: translateX(-20px); }} to {{ opacity: 1; transform: translateX(0); }} }}
      </style>
      
      <rect x="0.5" y="0.5" rx="4.5" height="99%" stroke="{BORDER_COLOR}" width="99%" fill="{BG_COLOR}" stroke-opacity="1" />
      
      <g transform="translate(25, 35)">
        <text x="0" y="0" class="header">{USERNAME}'s GitHub Stats</text>
      </g>
      
      <g transform="translate(0, 55)">
        <g class="stagger" style="animation-delay: 450ms" transform="translate(25, 30)">
          <text class="stat" x="25" y="12.5">Total Stars Earned:</text>
          <text class="stat" x="200" y="12.5" font-weight="700">{stats['stars']}</text>
        </g>
        
        <g class="stagger" style="animation-delay: 600ms" transform="translate(25, 55)">
          <text class="stat" x="25" y="12.5">Total Commits (2024):</text>
          <text class="stat" x="200" y="12.5" font-weight="700">{stats['commits']}</text>
        </g>
        
        <g class="stagger" style="animation-delay: 750ms" transform="translate(25, 80)">
          <text class="stat" x="25" y="12.5">Total PRs:</text>
          <text class="stat" x="200" y="12.5" font-weight="700">{stats['prs']}</text>
        </g>
        
        <g class="stagger" style="animation-delay: 900ms" transform="translate(25, 105)">
          <text class="stat" x="25" y="12.5">Total Issues:</text>
          <text class="stat" x="200" y="12.5" font-weight="700">{stats['issues']}</text>
        </g>
      </g>
    </svg>
    """
    
    os.makedirs("generated", exist_ok=True)
    with open("generated/stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

if __name__ == "__main__":
    try:
        stats = fetch_stats()
        generate_svg(stats)
        print("Generated generated/stats.svg successfully.")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
