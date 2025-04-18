from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import traceback
import uuid
import datetime
from .git_utils import clone_and_get_commits
from .lizard_metrics import process_commit

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return jsonify({
        "message": "TS Metrics Analyzer API",
        "endpoints": {
            "/analyze": "POST - Analyze a Git repository"
        },
        "usage": {
            "repo": "GitHub repository URL",
            "branch": "Branch name to analyze",
            "token": "GitHub token (optional)"
        }
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        # Extract repository URL - this is the only required field
        repo_url = data.get("repo")
        if not repo_url:
            return jsonify({"error": "Repository URL is required"}), 400
            
        # Extract optional parameters with defaults
        branch = data.get("branch")
        token = data.get("token")

        print(f"Analyzing repository: {repo_url}, branch: {branch or 'not specified (will use main)'}, token: {'provided' if token else 'not provided'}")
        
        try:
            results = clone_and_get_commits(repo_url, branch, token)
            
            if not results:
                return jsonify({
                    "message": "Repository cloned successfully but no commits were found to analyze",
                    "data": []
                })

            # Generate repository ID and other metadata
            repo_id = str(uuid.uuid4())
            branch_id = str(uuid.uuid4())
            org_id = str(uuid.uuid4())
            
            # Extract repository name and organization from URL
            repo_parts = repo_url.rstrip('/').split('/')
            project_name = repo_parts[-1] if repo_parts else "unknown-project"
            organization = repo_parts[-2] if len(repo_parts) > 1 else "unknown-org"
            
            # Collect unique authors
            authors = {}
            
            # Process commits
            formatted_commits = []
            for commit in results:
                commit_data = process_commit(commit)
                if not commit_data:
                    continue
                    
                for file_data in commit_data:
                    author_name = file_data.get("Autor", "Unknown")
                    
                    # Skip files that don't exist or aren't supported
                    file_path = file_data.get("Arquivo", "")
                    if file_data.get("error") == "file_not_found":
                        print(f"Skipping file: {file_path} (file not found)")
                        continue
                    if file_data.get("error") == "unsupported_file_type":
                        print(f"Skipping file: {file_path} (not a supported file type)")
                        continue
                    
                    # Add author if not already in the list
                    if author_name not in authors:
                        author_id = str(uuid.uuid4())
                        authors[author_name] = {
                            "id": author_id,
                            "name": author_name,
                            "link": f"https://github.com/{author_name}"
                        }
                    
                    # Format commit data according to the specified pattern
                    formatted_commit = {
                        "commitId": str(uuid.uuid4()),
                        "authorId": authors[author_name]["id"],
                        "branchId": branch_id,
                        "repositoryId": repo_id,
                        "autor": author_name,
                        "link": f"https://github.com/{organization}/{project_name}/commit/{file_data.get('SHA', '')}",
                        "sha": file_data.get("SHA", ""),
                        "createAt": file_data.get("Data", datetime.datetime.now().isoformat()),
                        "message": file_data.get("Mensagem", ""),
                        "filePath": file_data.get("Arquivo", ""),
                        "changeCode": file_data.get("Código Alterado", ""),
                        "risk": file_data.get("Risco (Nível)", 0),
                        "riskComment": file_data.get("Comentário Risco", ""),
                        "quality": file_data.get("Qualidade (Nível)", 0),
                        "qualityComment": file_data.get("Comentário Qualidade", ""),
                        "metrics": file_data.get("metricas", {})
                    }
                    
                    formatted_commits.append(formatted_commit)

            if not formatted_commits:
                return jsonify({
                    "message": "Repository analyzed but no metrics data was generated. This may be because no supported file types were found or files were missing.",
                    "data": []
                })
            
            # Create the final response object
            response = {
                "id": repo_id,
                "name": project_name,
                "organizationId": org_id,
                "branchId": branch_id,
                "link": f"https://github.com/{organization}/{project_name}/",
                "authors": list(authors.values()),
                "commits": formatted_commits
            }
                
            return jsonify(response)
            
        except Exception as e:
            error_message = str(e)
            print(f"Error processing repository: {error_message}")
            print(traceback.format_exc())
            if "does not exist" in error_message.lower() or "not found" in error_message.lower():
                return jsonify({"error": f"Repository or branch not found. Please check the URL and branch name. Details: {error_message}"}), 404
            elif "xcworkspace" in error_message.lower() or "ios/runner" in error_message.lower():
                return jsonify({"error": f"Flutter/Dart project detected. Some files may be skipped during analysis. Details: {error_message}"}), 202
            else:
                return jsonify({"error": f"Error analyzing repository: {error_message}"}), 500
                
    except Exception as e:
        print(f"Error in analyze endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
        
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500
