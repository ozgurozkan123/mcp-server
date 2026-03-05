"""
Burp Suite MCP Server - Standalone Deployment with Burp Suite Professional

This is a standalone MCP server that provides:
1. Utility tools (URL encoding/decoding, Base64, random string generation)
2. HTTP request tools for making requests to targets
3. Burp Suite Professional integration (installed in container)
4. Proxy connectivity to a running Burp Suite MCP server (when available)

The Burp Suite Professional JAR is installed in this container at /opt/burpsuite/burpsuite_pro.jar
"""

import os
import base64
import random
import string
import urllib.parse
import subprocess
import json
from typing import Optional
import httpx
from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("burp-suite-mcp")

# Burp Suite paths
BURP_JAR = os.getenv("BURP_JAR", "/opt/burpsuite/burpsuite_pro.jar")
JAVA_HOME = os.getenv("JAVA_HOME", "/usr/lib/jvm/temurin-21-jre-amd64")


@mcp.tool()
def check_burp_installation() -> str:
    """
    Checks if Burp Suite Professional is installed and returns version info.
    
    Returns:
        Installation status and version information
    """
    result = {
        "burp_jar_exists": os.path.exists(BURP_JAR),
        "burp_jar_path": BURP_JAR,
        "java_home": JAVA_HOME,
        "java_exists": os.path.exists(f"{JAVA_HOME}/bin/java"),
        "license_configured": os.path.exists("/root/.BurpSuite/prefs.xml")
    }
    
    # Check Java version
    try:
        java_version = subprocess.run(
            [f"{JAVA_HOME}/bin/java", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        result["java_version"] = java_version.stderr.strip()
    except Exception as e:
        result["java_version"] = f"Error: {str(e)}"
    
    # Check Burp JAR file size
    if os.path.exists(BURP_JAR):
        result["burp_jar_size_mb"] = round(os.path.getsize(BURP_JAR) / (1024 * 1024), 2)
    
    return json.dumps(result, indent=2)


@mcp.tool()
def get_burp_command(
    headless: bool = True,
    project_file: Optional[str] = None,
    config_file: Optional[str] = None,
    user_config_file: Optional[str] = None
) -> str:
    """
    Generates the command to run Burp Suite Professional.
    
    Args:
        headless: Run in headless mode (no GUI). Default: True
        project_file: Path to a Burp project file to open
        config_file: Path to a project-level config file
        user_config_file: Path to a user-level config file
    
    Returns:
        The command that can be used to run Burp Suite
    """
    java_bin = f"{JAVA_HOME}/bin/java"
    
    cmd_parts = [
        java_bin,
        "-Xmx2g",  # Max heap size
    ]
    
    if headless:
        cmd_parts.append("-Djava.awt.headless=true")
    
    cmd_parts.extend(["-jar", BURP_JAR])
    
    if project_file:
        cmd_parts.extend(["--project-file", project_file])
    
    if config_file:
        cmd_parts.extend(["--config-file", config_file])
    
    if user_config_file:
        cmd_parts.extend(["--user-config-file", user_config_file])
    
    return " ".join(cmd_parts)


@mcp.tool()
def run_burp_headless(timeout_seconds: int = 30) -> str:
    """
    Starts Burp Suite Professional in headless mode for a brief check.
    Note: Long-running Burp instances should be managed separately.
    
    Args:
        timeout_seconds: How long to run Burp before terminating (max 60 seconds)
    
    Returns:
        Burp Suite startup output
    """
    timeout_seconds = min(timeout_seconds, 60)  # Cap at 60 seconds
    
    try:
        java_bin = f"{JAVA_HOME}/bin/java"
        cmd = [
            java_bin,
            "-Xmx1g",
            "-Djava.awt.headless=true",
            "-jar", BURP_JAR,
            "--diagnostics"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        return f"""Burp Suite Diagnostics:
Exit Code: {result.returncode}

STDOUT:
{result.stdout[:5000] if result.stdout else '(empty)'}

STDERR:
{result.stderr[:5000] if result.stderr else '(empty)'}
"""
    except subprocess.TimeoutExpired:
        return f"Burp Suite ran for {timeout_seconds} seconds (timeout - this is expected for startup check)"
    except Exception as e:
        return f"Error running Burp Suite: {str(e)}"


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
    
    This server has Burp Suite Professional installed at /opt/burpsuite/burpsuite_pro.jar
    
    Returns:
        Instructions and installation status for Burp Suite MCP server
    """
    # Check installation status
    burp_exists = os.path.exists(BURP_JAR)
    license_exists = os.path.exists("/root/.BurpSuite/prefs.xml")
    
    return f"""
Burp Suite MCP Server - Installation Status:

Burp Suite Professional Installed: {'Yes' if burp_exists else 'No'}
Burp JAR Location: {BURP_JAR}
License Configured: {'Yes' if license_exists else 'No'}
Java Home: {JAVA_HOME}

This MCP server provides the following tools:

UTILITY TOOLS (work independently):
- url_encode/url_decode: URL encoding/decoding
- base64_encode/base64_decode: Base64 encoding/decoding
- html_encode/html_decode: HTML entity encoding/decoding
- generate_random_string: Generate random strings
- hash_string: Compute MD5, SHA1, SHA256, SHA512 hashes
- jwt_decode: Decode JWT tokens
- analyze_url: Parse and analyze URLs
- send_http_request: Send HTTP requests

BURP SUITE TOOLS:
- check_burp_installation: Verify Burp Suite installation
- get_burp_command: Generate command to run Burp Suite
- run_burp_headless: Run Burp diagnostics in headless mode

TO RUN BURP SUITE INTERACTIVELY:
Use the get_burp_command tool to generate the command, then run it in a terminal
with X11 forwarding or a display server.

For full Burp Suite extension integration (proxy history, repeater, intruder, scanner, etc.),
install the MCP extension from: https://github.com/PortSwigger/mcp-server
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
