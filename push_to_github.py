"""
AegisRL - GitHub Push Automation Script
Uses Dulwich (pure Python Git implementation) to push the repository
without requiring external Git CLI installations.
"""

import sys
import os
import argparse
import dulwich.porcelain
import dulwich.repo

def main():
    parser = argparse.ArgumentParser(description="Push AegisRL repository to GitHub")
    parser.add_argument("--repo-url", required=True, help="GitHub repository URL (e.g. https://github.com/username/reponame.git)")
    parser.add_argument("--token", default=None, help="GitHub Personal Access Token (optional if embedded in URL)")
    parser.add_argument("--branch", default="main", help="Branch name to push (default: main)")
    
    args = parser.parse_args()
    
    repo_path = os.path.dirname(os.path.abspath(__file__))
    repo = dulwich.repo.Repo(repo_path)
    
    remote_url = args.repo_url.strip()
    if args.token:
        # Embed token into https URL if not already present
        if remote_url.startswith("https://") and "@" not in remote_url:
            remote_url = remote_url.replace("https://", f"https://{args.token}@")
            
    print(f"[*] Target Remote: {args.repo_url}")
    print(f"[*] Target Branch: {args.branch}")
    print(f"[*] Project Path: {repo_path}")
    print("[*] Initiating push...")
    
    try:
        refspec = f"refs/heads/{args.branch}:refs/heads/{args.branch}".encode("utf-8")
        dulwich.porcelain.push(repo, remote_url, refspecs=[refspec])
        print("\n[SUCCESS] Successfully pushed repository to GitHub!")
        print(f"Check your repository at: {args.repo_url.replace('.git', '')}")
    except Exception as e:
        print(f"\n[ERROR] Failed to push: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
