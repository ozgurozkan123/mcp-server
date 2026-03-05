"""
Burp Suite MCP Server - Standalone Deployment

This is a standalone MCP server that provides:
1. Utility tools (URL encoding/decoding, Base64, random string generation)
2. HTTP request tools for making requests to targets
3. Proxy connectivity to a running Burp Suite MCP server (when available)

The original Burp Suite MCP server is a Java extension that runs inside Burp Suite.
This Python server provides similar utility functions that can run independently.
"""

import os
import base64
import random
import string
import urllib.parse
from typing import Optional
import httpx
from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("burp-suite-mcp")


@mcp.tool()
def url_encode(content: str) -> str:
    """
    URL encodes the input string.
    
    Args:
        content: The string to URL encode
    
    Returns:
        URL encoded string
    """
    return urllib.parse.quote(content, safe='')


@mcp.tool()
def url_decode(content: str) -> str:
    """
    URL decodes the input string.
    
    Args:
        content: The URL encoded string to decode
    
    Returns:
        Decoded string
    """
    return urllib.parse.unquote(content)


@mcp.tool()
def base64_encode(content: str) -> str:
    """
    Base64 encodes the input string.
    
    Args:
        content: The string to Base64 encode
    
    Returns:
        Base64 encoded string
    """
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')


@mcp.tool()
def base64_decode(content: str) -> str:
    """
    Base64 decodes the input string.
    
    Args:
        content: The Base64 encoded string to decode
    
    Returns:
        Decoded string
    """
    try:
        return base64.b64decode(content).decode('utf-8')
    except Exception as e:
        return f"Error decoding Base64: {str(e)}"


@mcp.tool()
def generate_random_string(length: int, character_set: str = "alphanumeric") -> str:
    """
    Generates a random string of specified length and character set.
    
    Args:
        length: The length of the random string to generate
        character_set: The type of characters to use. Options:
                      - "alphanumeric" (default): letters and numbers
                      - "alpha": only letters
                      - "numeric": only numbers
                      - "hex": hexadecimal characters
                      - "special": includes special characters
                      - Or provide a custom string of characters to use
    
    Returns:
        Random string of the specified length
    """
    if character_set == "alphanumeric":
        chars = string.ascii_letters + string.digits
    elif character_set == "alpha":
        chars = string.ascii_letters
    elif character_set == "numeric":
        chars = string.digits
    elif character_set == "hex":
        chars = string.hexdigits
    elif character_set == "special":
        chars = string.ascii_letters + string.digits + string.punctuation
    else:
        # Use the provided string as the character set
        chars = character_set
    
    return ''.join(random.choice(chars) for _ in range(length))


@mcp.tool()
async def send_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[str] = None,
    body: Optional[str] = None,
    timeout: int = 30
) -> str:
    """
    Sends an HTTP request to the specified URL and returns the response.
    
    Args:
        url: The full URL to send the request to (e.g., https://example.com/path)
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Optional headers as a JSON string, e.g., '{"Content-Type": "application/json"}'
        body: Optional request body
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Response including status code, headers, and body
    """
    import json
    
    parsed_headers = {}
    if headers:
        try:
            parsed_headers = json.loads(headers)
        except json.JSONDecodeError:
            return f"Error: Invalid headers JSON format. Got: {headers}"
    
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=parsed_headers,
                content=body if body else None
            )
            
            response_headers = dict(response.headers)
            
            result = f"""HTTP Response:
Status: {response.status_code} {response.reason_phrase}
Headers: {json.dumps(response_headers, indent=2)}

Body:
{response.text[:10000]}{'... (truncated)' if len(response.text) > 10000 else ''}"""
            
            return result
            
    except httpx.TimeoutException:
        return f"Error: Request timed out after {timeout} seconds"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def html_encode(content: str) -> str:
    """
    HTML encodes special characters in the input string.
    
    Args:
        content: The string to HTML encode
    
    Returns:
        HTML encoded string
    """
    import html
    return html.escape(content)


@mcp.tool()
def html_decode(content: str) -> str:
    """
    HTML decodes the input string.
    
    Args:
        content: The HTML encoded string to decode
    
    Returns:
        Decoded string
    """
    import html
    return html.unescape(content)


@mcp.tool()
def hash_string(content: str, algorithm: str = "sha256") -> str:
    """
    Computes a hash of the input string.
    
    Args:
        content: The string to hash
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
    
    Returns:
        Hexadecimal hash string
    """
    import hashlib
    
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    if algorithm.lower() not in algorithms:
        return f"Error: Unsupported algorithm. Use one of: {', '.join(algorithms.keys())}"
    
    hash_func = algorithms[algorithm.lower()]
    return hash_func(content.encode('utf-8')).hexdigest()


@mcp.tool()
def jwt_decode(token: str) -> str:
    """
    Decodes a JWT token and returns its header and payload (without verification).
    
    Args:
        token: The JWT token to decode
    
    Returns:
        JSON string containing the decoded header and payload
    """
    import json
    
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return "Error: Invalid JWT format. Expected 3 parts separated by dots."
        
        # Add padding if needed
        def decode_part(part):
            padding = 4 - len(part) % 4
            if padding != 4:
                part += '=' * padding
            return base64.urlsafe_b64decode(part).decode('utf-8')
        
        header = json.loads(decode_part(parts[0]))
        payload = json.loads(decode_part(parts[1]))
        
        return json.dumps({
            "header": header,
            "payload": payload,
            "signature": parts[2][:20] + "..." if len(parts[2]) > 20 else parts[2]
        }, indent=2)
        
    except Exception as e:
        return f"Error decoding JWT: {str(e)}"


@mcp.tool()
def analyze_url(url: str) -> str:
    """
    Analyzes a URL and extracts its components.
    
    Args:
        url: The URL to analyze
    
    Returns:
        JSON string with URL components (scheme, host, port, path, query params, etc.)
    """
    import json
    
    try:
        parsed = urllib.parse.urlparse(url)
        query_params = dict(urllib.parse.parse_qsl(parsed.query))
        
        result = {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "path": parsed.path,
            "query_string": parsed.query,
            "query_params": query_params,
            "fragment": parsed.fragment,
            "netloc": parsed.netloc
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error analyzing URL: {str(e)}"


@mcp.tool()
def get_burp_connection_info() -> str:
    """
    Returns information about connecting to a Burp Suite MCP server.
    
    This standalone server provides utility functions. To connect to a running
    Burp Suite instance with full functionality (proxy history, repeater, intruder, etc.),
    you need to:
    
    1. Install the Burp Suite MCP extension in Burp Suite
    2. Configure the MCP server in the extension settings
    3. Connect your MCP client to the Burp SSE MCP server
    
    Returns:
        Instructions for connecting to Burp Suite MCP server
    """
    return """
Burp Suite MCP Server Connection Information:

This standalone MCP server provides utility tools that work independently:
- URL encoding/decoding
- Base64 encoding/decoding
- Random string generation
- HTTP request sending
- HTML encoding/decoding
- Hash computation
- JWT decoding
- URL analysis

For full Burp Suite integration (proxy history, repeater, intruder, scanner, etc.),
you need the Burp Suite extension:

1. Install the MCP extension in Burp Suite (from BApp Store or build from source)
2. Configure the extension in Burp's MCP tab
3. The extension exposes an SSE MCP server (default: http://127.0.0.1:9876)
4. Connect your MCP client to that URL

Available tools in the Burp Suite extension:
- send_http1_request: Send HTTP/1.1 requests through Burp
- send_http2_request: Send HTTP/2 requests through Burp
- create_repeater_tab: Create a Repeater tab with a request
- send_to_intruder: Send a request to Intruder
- get_proxy_http_history: View proxy HTTP history
- get_scanner_issues: View scanner findings (Professional only)
- generate_collaborator_payload: Generate OOB payloads (Professional only)
- And more...

For more information: https://github.com/PortSwigger/mcp-server
"""


# Run the server
if __name__ == "__main__":
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    
    # Use HTTP transport for better compatibility with remote deployment
    # HTTP transport creates endpoint at /mcp
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )
