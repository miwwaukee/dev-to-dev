#!/usr/bin/env python3
"""
DevHelper MCP Server - Main entry point.

Commands:
    serve - Start MCP server on port 8000
    smoke - Run quick self-test
"""

import sys
import json
import asyncio
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

from src.tools.tech_debt import find_tech_debt
from src.tools.deps_check import check_dependencies

# === MCP Server Tools Registry ===
TOOLS = {
    "find_tech_debt": {
        "description": "Scan codebase for TODO/FIXME/HACK comments and prioritize them",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to directory to scan"
                },
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File extensions to scan",
                    "default": [".py", ".js", ".ts", ".java", ".go"]
                },
                "min_priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Minimum priority level to return",
                    "default": "low"
                }
            },
            "required": ["path"]
        }
    },
    "check_dependencies": {
        "description": "Analyze dependency manifest for vulnerabilities and license compliance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "manifest_path": {
                    "type": "string",
                    "description": "Path to requirements.txt or package.json"
                },
                "license_policy": {
                    "type": "string",
                    "enum": ["permissive", "copyleft", "strict"],
                    "description": "License policy to enforce",
                    "default": "permissive"
                },
                "check_vulnerabilities": {
                    "type": "boolean",
                    "description": "Check for known vulnerabilities",
                    "default": True
                }
            },
            "required": ["manifest_path"]
        }
    }
}

# === FastAPI Application ===
app = FastAPI(title="DevHelper MCP Server", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint - returns quickly without heavy operations."""
    return {"status": "ok", "service": "devhelper-mcp", "version": "1.0.0"}


@app.get("/mcp")
async def mcp_get():
    """MCP endpoint - return server info."""
    return {
        "name": "DevHelper MCP Server",
        "version": "1.0.0",
        "tools": list(TOOLS.keys()),
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp"
        }
    }


@app.post("/mcp")
async def mcp_post(request: Request):
    """MCP endpoint - handle tool calls."""
    try:
        body = await request.json()
        
        # Handle MCP protocol messages
        if body.get("method") == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "DevHelper",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif body.get("method") == "tools/list":
            tools_list = []
            for name, info in TOOLS.items():
                tools_list.append({
                    "name": name,
                    "description": info["description"],
                    "inputSchema": info["inputSchema"]
                })
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"tools": tools_list}
            }
        
        elif body.get("method") == "tools/call":
            tool_name = body.get("params", {}).get("name")
            tool_args = body.get("params", {}).get("arguments", {})
            
            if tool_name == "find_tech_debt":
                result = find_tech_debt(
                    path=tool_args.get("path", "."),
                    extensions=tool_args.get("extensions", [".py", ".js", ".ts"]),
                    min_priority=tool_args.get("min_priority", "low")
                )
            elif tool_name == "check_dependencies":
                result = check_dependencies(
                    manifest_path=tool_args.get("manifest_path", "./requirements.txt"),
                    license_policy=tool_args.get("license_policy", "permissive"),
                    check_vulnerabilities=tool_args.get("check_vulnerabilities", True)
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {body.get('method')}"
                }
            }
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in dir() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


@app.get("/")
async def root():
    """Root endpoint - server info."""
    return {
        "service": "DevHelper MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp (GET/POST)"
        },
        "tools": list(TOOLS.keys())
    }


# === CLI Entry Point ===
def run_smoke_test():
    """Run quick self-test to verify tools work."""
    print("🔍 Running smoke test...")
    
    try:
        # Test 1: Tech debt finder
        print("  Testing find_tech_debt...")
        result1 = find_tech_debt(path="./demo_project", min_priority="low")
        if "items" not in result1:
            print("  ❌ find_tech_debt: invalid response format")
            return False
        print(f"  ✅ find_tech_debt: found {len(result1.get('items', []))} items")
        
        # Test 2: Dependency checker
        print("  Testing check_dependencies...")
        result2 = check_dependencies(manifest_path="./demo_project/requirements.txt")
        if "packages" not in result2:
            print("  ❌ check_dependencies: invalid response format")
            return False
        print(f"  ✅ check_dependencies: analyzed {len(result2.get('packages', []))} packages")
        
        print("✅ Smoke test passed!")
        return True
    
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        cmd = "serve"
    else:
        cmd = sys.argv[1]
    
    if cmd == "smoke":
        success = run_smoke_test()
        sys.exit(0 if success else 1)
    
    elif cmd == "serve":
        print("🚀 Starting DevHelper MCP Server on port 8000...")
        print("   Health: http://localhost:8000/health")
        print("   MCP:    http://localhost:8000/mcp")
        uvicorn.run("src.server:app", host="0.0.0.0", port=8000, log_level="info")
    
    else:
        print(f"❌ Unknown command: {cmd}")
        print("   Usage: python -m src.server [serve|smoke]")
        sys.exit(1)


if __name__ == "__main__":
    main()
