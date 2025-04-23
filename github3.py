from typing import Any, Dict, List
import requests
import base64
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("github_api")

# Constants
GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "github-mcp-tool/1.0"
# Add GitHub authentication token
GITHUB_TOKEN = ""

def get_github_contents(repo_owner: str, repo_name: str, path: str = "", ref: str = "main") -> dict:
    """Get contents of a file or directory from GitHub API."""
    url = f"{GITHUB_API_BASE}/repos/{repo_owner}/{repo_name}/contents/{path}"
    params = {"ref": ref}
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"GitHub API error: {response.status_code} - {response.text}"}
    
    return response.json()

@mcp.tool()
def github_get_file(repo: str, file_path: str, branch: str = "main") -> str:
    """Get the contents of a specific file from a GitHub repository.
    
    Args:
        repo: Repository in the format 'owner/repo'
        file_path: Path to the file within the repository
        branch: The branch or commit reference (default: main)
    """
    # Parse the repo parameter
    parts = repo.split('/')
    if len(parts) != 2:
        return f"Error: Repository format should be 'owner/repo', got '{repo}'"
    
    owner, repo_name = parts
    
    # Get file contents from GitHub API
    contents = get_github_contents(owner, repo_name, file_path, branch)
    
    if "error" in contents:
        return f"Error: {contents['error']}"
        
    if isinstance(contents, dict) and "type" in contents:
        if contents["type"] != "file":
            return f"Error: Path '{file_path}' is not a file"
            
        if "content" in contents and contents["encoding"] == "base64":
            decoded_content = base64.b64decode(contents["content"]).decode("utf-8")
            return decoded_content
        else:
            return f"Error: Could not decode file content"
    else:
        return f"Error: Unexpected API response format"

@mcp.tool()
def github_list_directory(repo: str, path: str = "", branch: str = "main") -> str:
    """List files and directories at the specified path in a GitHub repository.
    
    Args:
        repo: Repository in the format 'owner/repo'
        path: Path within the repository (default: repository root)
        branch: The branch or commit reference (default: main)
    """
    # Parse the repo parameter
    parts = repo.split('/')
    if len(parts) != 2:
        return f"Error: Repository format should be 'owner/repo', got '{repo}'"
    
    owner, repo_name = parts
    
    # Get directory contents from GitHub API
    contents = get_github_contents(owner, repo_name, path, branch)
    
    if "error" in contents:
        return f"Error: {contents['error']}"
        
    if not isinstance(contents, list):
        return f"Error: Path '{path}' is not a directory or the API returned unexpected data"
        
    formatted_results = []
    for item in contents:
        item_type = item["type"]  # "file" or "dir"
        item_name = item["name"]
        item_path = item["path"]
        item_size = item.get("size", "N/A") if item["type"] == "file" else "N/A"
        
        formatted_item = f"""
Type: {item_type}
Name: {item_name}
Path: {item_path}
Size: {item_size} bytes
"""
        formatted_results.append(formatted_item)
        
    return "\n---\n".join(formatted_results)

@mcp.tool()
def github_search_code(repo: str, query: str, branch: str = "main") -> str:
    """Search for files matching a query within a GitHub repository.
    
    Args:
        repo: Repository in the format 'owner/repo'
        query: Search term to look for in filenames
        branch: The branch or commit reference (default: main)
    """
    # Parse the repo parameter
    parts = repo.split('/')
    if len(parts) != 2:
        return f"Error: Repository format should be 'owner/repo', got '{repo}'"
    
    owner, repo_name = parts
    
    url = f"{GITHUB_API_BASE}/search/code"
    params = {
        "q": f"{query} in:file repo:{owner}/{repo_name} ref:{branch}",
    }
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return f"Error: GitHub API error: {response.status_code} - {response.text}"
    
    result = response.json()
    items = result.get("items", [])
    
    if not items:
        return "No matching files found."
    
    formatted_results = []
    for i, item in enumerate(items, 1):
        formatted_item = f"""
Result {i}:
Name: {item.get('name', 'Unknown')}
Path: {item.get('path', 'Unknown')}
URL: {item.get('html_url', 'Unknown')}
"""
        formatted_results.append(formatted_item)
        
    return "\n---\n".join(formatted_results)

@mcp.tool()
def check_github_connection() -> str:
    """Verify the connection to GitHub API is working properly."""
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Authorization": f"token {GITHUB_TOKEN}"
        }
        response = requests.get(f"{GITHUB_API_BASE}/rate_limit", headers=headers)
        if response.status_code == 200:
            rate_limit_info = response.json()
            core_remaining = rate_limit_info.get("resources", {}).get("core", {}).get("remaining", 0)
            return f"GitHub API connection successful. Remaining rate limit: {core_remaining} requests."
        else:
            return f"Error connecting to GitHub API: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# This is the critical part that was missing in the previous implementation
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 