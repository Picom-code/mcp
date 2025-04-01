from typing import Any, List, Dict
import httpx
import urllib.parse
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("web_search")

# Constants
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"

async def search_duckduckgo(query: str, num_results: int = 15) -> List[Dict[str, str]]:
    """Perform a DuckDuckGo search and parse the results."""
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    data = {
        "q": query,
        "kl": "us-en"
    }
    
    results = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DUCKDUCKGO_URL, headers=headers, data=data, timeout=30.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search result divs
            for result in soup.find_all('div', class_='result'):
                title_element = result.find('a', class_='result__a')
                snippet_element = result.find('a', class_='result__snippet')
                
                if title_element and snippet_element:
                    title = title_element.get_text().strip()
                    link = title_element.get('href')
                    
                    # DuckDuckGo uses redirect URLs
                    if link.startswith('/'):
                        try:
                            # Extract the actual URL from the redirect parameter
                            parsed_url = urllib.parse.urlparse(link)
                            query_params = urllib.parse.parse_qs(parsed_url.query)
                            if 'uddg' in query_params:
                                link = query_params['uddg'][0]
                            else:
                                link = "https://duckduckgo.com" + link
                        except:
                            link = "https://duckduckgo.com" + link
                            
                    snippet = snippet_element.get_text().strip()
                    
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })
                    
                    if len(results) >= num_results:
                        break
    except Exception as e:
        return [{"error": str(e)}]
    
    return results

@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web and return the top 15 results.

    Args:
        query: The search query string
    """
    results = await search_duckduckgo(query, 15)
    
    if results and "error" in results[0]:
        return f"Error: {results[0]['error']}"
    
    if not results:
        return "No search results found."
    
    formatted_results = []
    for i, result in enumerate(results, 1):
        formatted_result = f"""
Result {i}:
Title: {result.get('title', 'No title')}
URL: {result.get('link', 'No link')}
Snippet: {result.get('snippet', 'No description available')}
"""
        formatted_results.append(formatted_result)
    
    return "\n---\n".join(formatted_results)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 