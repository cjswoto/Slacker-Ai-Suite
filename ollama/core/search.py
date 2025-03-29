import re
import html
import datetime
from urllib.parse import quote_plus

try:
    from duckduckgo_search import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


def perform_web_search(query, search_engine="DuckDuckGo", max_results=3, search_timeout=10):
    search_debug_info = f"Search query: \"{query}\"\n"
    search_debug_info += f"Search time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
    search_debug_info += f"Search engine: {search_engine}\n"
    search_debug_info += f"Max results: {max_results}\n"
    search_debug_info += f"Timeout: {search_timeout} seconds\n\n"

    search_results = []

    try:
        if search_engine == "DuckDuckGo API" and DDGS_AVAILABLE:
            search_debug_info += "Using DuckDuckGo Search API\n"
            try:
                with DDGS() as ddgs:
                    ddgs_results = list(ddgs.text(query, max_results=max_results))
                    search_debug_info += f"Found {len(ddgs_results)} results\n\n"
                    for i, result in enumerate(ddgs_results):
                        title = result.get("title", "No title")
                        body = result.get("body", "No content")
                        href = result.get("href", "No URL")
                        search_results.append(
                            f"Result {i + 1}:\nTitle: {title}\nSnippet: {body}\nURL: {href}\n"
                        )
                        search_debug_info += f"Result {i + 1} - {title}\n"
            except Exception as e:
                error_msg = f"DuckDuckGo API error: {str(e)}"
                search_debug_info += f"Error: {error_msg}\nFalling back to HTML scraping method\n"
                search_engine = "DuckDuckGo"

        if search_engine in ["DuckDuckGo", "Google"]:
            if search_engine == "DuckDuckGo":
                search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
                search_debug_info += f"Using DuckDuckGo HTML scraping\nURL: {search_url}\n"
            else:
                search_url = f"https://www.google.com/search?q={quote_plus(query)}"
                search_debug_info += f"Using Google HTML scraping\nURL: {search_url}\n"

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                    " Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            import requests
            response = requests.get(search_url, headers=headers, timeout=search_timeout)
            search_debug_info += f"Response status code: {response.status_code}\n"
            if response.status_code != 200:
                return {"results": f"Error: Search engine returned status code {response.status_code}",
                        "debug": search_debug_info}

            content = response.text

            if search_engine == "DuckDuckGo":
                result_divs = re.findall(
                    r'<div class="result__body">(.*?)</div>\s*</div>', content, re.DOTALL
                )
                search_debug_info += f"Found {len(result_divs)} result divs in HTML\n\n"
                for i, div in enumerate(result_divs[:max_results]):
                    title_match = re.search(
                        r'<a class="result__a" href=".*?">(.*?)</a>', div, re.DOTALL
                    )
                    title = (
                        html.unescape(re.sub(r"<.*?>", "", title_match.group(1)))
                        if title_match
                        else "No title"
                    )
                    snippet_match = re.search(
                        r'<a class="result__snippet".*?>(.*?)</a>', div, re.DOTALL
                    )
                    snippet = (
                        html.unescape(re.sub(r"<.*?>", "", snippet_match.group(1)))
                        if snippet_match
                        else "No snippet"
                    )
                    url_match = re.search(
                        r'<a class="result__a" href="(.*?)"', div, re.DOTALL
                    )
                    url = url_match.group(1) if url_match else "No URL"
                    search_results.append(
                        f"Result {i + 1}:\nTitle: {title}\nSnippet: {snippet}\nURL: {url}\n"
                    )
                    search_debug_info += f"Result {i + 1} - {title}\n"
            elif search_engine == "Google":
                result_divs = re.findall(
                    r'<div class="g">(.*?)</div>\s*</div>\s*</div>', content, re.DOTALL
                )
                search_debug_info += f"Found {len(result_divs)} result divs in HTML\n\n"
                for i, div in enumerate(result_divs[:max_results]):
                    title_match = re.search(
                        r'<h3 class=".*?">(.*?)</h3>', div, re.DOTALL
                    )
                    title = (
                        html.unescape(re.sub(r"<.*?>", "", title_match.group(1)))
                        if title_match
                        else "No title"
                    )
                    snippet_match = re.search(
                        r'<span class=".*?">(.*?)</span>', div, re.DOTALL
                    )
                    snippet = (
                        html.unescape(re.sub(r"<.*?>", "", snippet_match.group(1)))
                        if snippet_match
                        else "No snippet"
                    )
                    url_match = re.search(r'<a href="(https?://.*?)"', div, re.DOTALL)
                    url = url_match.group(1) if url_match else "No URL"
                    search_results.append(
                        f"Result {i + 1}:\nTitle: {title}\nSnippet: {snippet}\nURL: {url}\n"
                    )
                    search_debug_info += f"Result {i + 1} - {title}\n"

        if not search_results:
            search_debug_info += "No search results found.\n"
            return {"results": "No search results found.", "debug": search_debug_info}

        search_debug_info += f"\nSearch completed successfully with {len(search_results)} results."
        formatted_results = f"Web search results for: {query}\n\n" + "\n".join(search_results)
        return {"results": formatted_results, "debug": search_debug_info}
    except Exception as e:
        error_msg = f"Error performing web search: {str(e)}"
        search_debug_info += f"\n{error_msg}"
        return {"results": error_msg, "debug": search_debug_info}
