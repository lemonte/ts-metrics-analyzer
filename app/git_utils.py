import tempfile, shutil, os
from git import Repo
import traceback
import os.path

def clone_and_get_commits(repo_url, branch=None, token=None):
    if not repo_url:
        raise ValueError("Repository URL is required")
        
    # Default to main branch if not specified
    if not branch:
        branch = "main"
        print(f"No branch specified, defaulting to 'main'")
        
    clone_url = repo_url
    if token:
        clone_url = repo_url.replace("https://", f"https://{token}@")
    temp_dir = tempfile.mkdtemp()
    
    # Create a dictionary to track missing files for better error handling
    missing_files = {}

    try:
        print(f"Cloning repository: {repo_url} (branch: {branch})")
        repo = Repo.clone_from(clone_url, temp_dir, branch=branch)
        
        # Try to get commits
        try:
            commits = list(repo.iter_commits(branch))
            print(f"Found {len(commits)} commits")
            
            if not commits:
                print("Warning: No commits found in the repository")
                shutil.rmtree(temp_dir)
                return []
                
            result = []
            for commit in commits:
                # Check if files exist before adding to result
                commit_data = {
                    "repo": repo,
                    "temp_dir": temp_dir,
                    "commit": commit,
                    "missing_files": missing_files
                }
                result.append(commit_data)
            return result
            
        except Exception as e:
            print(f"Error getting commits: {str(e)}")
            print(traceback.format_exc())
            shutil.rmtree(temp_dir)
            raise Exception(f"Failed to get commits: {str(e)}")
            
    except Exception as e:
        print(f"Error cloning repository: {str(e)}")
        print(traceback.format_exc())
        shutil.rmtree(temp_dir)
        raise Exception(f"Failed to clone repository: {str(e)}")
