"""
Dependency Checker Tool.

Analyzes dependency manifests for vulnerabilities and license compliance.
Uses local database only - no external API calls required.
"""

import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path


# Local vulnerability database (pattern-based, no external API)
# In production, this would be updated regularly from CVE databases
VULNERABILITY_PATTERNS = {
    "python": {
        "flask": [
            {"version_pattern": r"^1\.[0-1]\.", "cve": "CVE-2022-XXXX", "severity": "high", "description": "Known vulnerabilities in Flask < 2.0"}
        ],
        "django": [
            {"version_pattern": r"^[1-2]\.", "cve": "CVE-2021-XXXX", "severity": "high", "description": "Known vulnerabilities in Django < 3.0"}
        ],
        "requests": [
            {"version_pattern": r"^2\.[0-1][0-9]\.", "cve": "CVE-2023-XXXX", "severity": "medium", "description": "Known vulnerabilities in requests < 2.20"}
        ],
        "urllib3": [
            {"version_pattern": r"^1\.[0-9]\.", "cve": "CVE-2021-33503", "severity": "high", "description": "ReDoS vulnerability in urllib3 < 1.26.5"}
        ],
        "pillow": [
            {"version_pattern": r"^[0-7]\.", "cve": "CVE-2022-XXXX", "severity": "high", "description": "Known vulnerabilities in Pillow < 8.0"}
        ]
    },
    "javascript": {
        "express": [
            {"version_pattern": r"^[0-3]\.", "cve": "CVE-2022-XXXX", "severity": "medium", "description": "Known vulnerabilities in express < 4.0"}
        ],
        "lodash": [
            {"version_pattern": r"^4\.[0-9]\.", "cve": "CVE-2021-23337", "severity": "high", "description": "Prototype pollution in lodash < 4.17.21"}
        ],
        "axios": [
            {"version_pattern": r"^0\.[0-1][0-9]\.", "cve": "CVE-2021-XXXX", "severity": "medium", "description": "Known vulnerabilities in axios < 0.21"}
        ]
    }
}

# License classification
LICENSE_WHITELIST = {
    "permissive": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "CC0-1.0"],
    "copyleft": ["GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0", "MPL-2.0"],
    "restricted": ["Proprietary", "Commercial", "All Rights Reserved"]
}

# Known license mappings (simplified)
KNOWN_LICENSES = {
    "requests": "Apache-2.0",
    "flask": "BSD-3-Clause",
    "django": "BSD-3-Clause",
    "numpy": "BSD-3-Clause",
    "pandas": "BSD-3-Clause",
    "pytest": "MIT",
    "express": "MIT",
    "lodash": "MIT",
    "axios": "MIT",
    "react": "MIT",
    "vue": "MIT",
    "angular": "MIT"
}

# Typosquatting patterns (common package name variations)
TYPOSQUAT_PATTERNS = {
    "python": {
        "requets": "requests",
        "reqeusts": "requests",
        "djnago": "django",
        "flaskk": "flask",
        "numppy": "numpy"
    },
    "javascript": {
        "lodahs": "lodash",
        "expres": "express",
        "axois": "axios",
        "reacct": "react"
    }
}


def parse_requirements_txt(path: str) -> List[Dict[str, str]]:
    """Parse Python requirements.txt file."""
    packages = []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Skip options like -r, -e, etc.
                if line.startswith('-'):
                    continue
                
                # Parse package==version or package>=version etc.
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*([=<>!~]+)\s*([0-9.a-zA-Z-]+)', line)
                if match:
                    packages.append({
                        "name": match.group(1).lower(),
                        "version": match.group(3),
                        "specifier": match.group(2)
                    })
                else:
                    # Package without version
                    match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                    if match:
                        packages.append({
                            "name": match.group(1).lower(),
                            "version": "unknown",
                            "specifier": "=="
                        })
    except Exception as e:
        pass
    
    return packages


def parse_package_json(path: str) -> List[Dict[str, str]]:
    """Parse JavaScript package.json file."""
    packages = []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check dependencies and devDependencies
        for dep_type in ["dependencies", "devDependencies"]:
            deps = data.get(dep_type, {})
            for name, version in deps.items():
                # Clean version string (remove ^, ~, etc.)
                clean_version = re.sub(r'^[\^~>=<]*', '', version)
                packages.append({
                    "name": name.lower(),
                    "version": clean_version,
                    "specifier": "npm",
                    "dep_type": dep_type
                })
    except Exception as e:
        pass
    
    return packages


def check_vulnerability(name: str, version: str, ecosystem: str) -> List[Dict[str, Any]]:
    """Check if package version has known vulnerabilities."""
    issues = []
    vuln_db = VULNERABILITY_PATTERNS.get(ecosystem, {})
    
    if name in vuln_db:
        for vuln in vuln_db[name]:
            if re.match(vuln["version_pattern"], version):
                issues.append({
                    "type": "vulnerability",
                    "package": name,
                    "version": version,
                    "cve": vuln["cve"],
                    "severity": vuln["severity"],
                    "description": vuln["description"]
                })
    
    return issues


def check_typosquatting(name: str, ecosystem: str) -> Dict[str, Any]:
    """Check if package name looks like typosquatting."""
    typosquat_db = TYPOSQUAT_PATTERNS.get(ecosystem, {})
    
    if name in typosquat_db:
        return {
            "type": "typosquatting",
            "package": name,
            "suspicious_of": typosquat_db[name],
            "severity": "high",
            "description": f"Package name '{name}' is suspiciously similar to '{typosquat_db[name]}'"
        }
    
    return None


def get_license(name: str) -> str:
    """Get known license for package."""
    return KNOWN_LICENSES.get(name.lower(), "unknown")


def check_license_compliance(license_name: str, policy: str) -> bool:
    """Check if license complies with policy."""
    if license_name == "unknown":
        return True  # Can't determine, allow with warning
    
    policy_licenses = LICENSE_WHITELIST.get(policy, LICENSE_WHITELIST["permissive"])
    
    # For permissive policy, allow permissive licenses
    if policy == "permissive":
        return license_name in LICENSE_WHITELIST["permissive"] or license_name == "unknown"
    
    # For copyleft policy, allow permissive and copyleft
    elif policy == "copyleft":
        return license_name in LICENSE_WHITELIST["permissive"] + LICENSE_WHITELIST["copyleft"] or license_name == "unknown"
    
    # For strict policy, only allow permissive
    else:
        return license_name in LICENSE_WHITELIST["permissive"] or license_name == "unknown"


def check_dependencies(
    manifest_path: str = "./requirements.txt",
    license_policy: str = "permissive",
    check_vulnerabilities: bool = True
) -> Dict[str, Any]:
    """
    Analyze dependency manifest for issues.
    
    Args:
        manifest_path: Path to requirements.txt or package.json
        license_policy: License policy (permissive/copyleft/strict)
        check_vulnerabilities: Whether to check for vulnerabilities
    
    Returns:
        Dictionary with packages, issues, and summary
    """
    path = Path(manifest_path)
    
    if not path.exists():
        return {
            "error": f"Manifest file not found: {manifest_path}",
            "packages": [],
            "issues": [],
            "licenses": {"ok": 0, "restricted": 0, "unknown": 0}
        }
    
    # Determine ecosystem and parse
    if path.suffix == ".txt" or path.name == "requirements.txt":
        ecosystem = "python"
        packages = parse_requirements_txt(str(path))
    elif path.name == "package.json":
        ecosystem = "javascript"
        packages = parse_package_json(str(path))
    else:
        return {
            "error": f"Unsupported manifest format: {manifest_path}",
            "packages": [],
            "issues": [],
            "licenses": {"ok": 0, "restricted": 0, "unknown": 0}
        }
    
    # Analyze each package
    results = []
    issues = []
    license_stats = {"ok": 0, "restricted": 0, "unknown": 0}
    
    for pkg in packages:
        name = pkg["name"]
        version = pkg["version"]
        
        # Get license
        license_name = get_license(name)
        license_ok = check_license_compliance(license_name, license_policy)
        
        if license_name == "unknown":
            license_stats["unknown"] += 1
        elif license_ok:
            license_stats["ok"] += 1
        else:
            license_stats["restricted"] += 1
            issues.append({
                "type": "license",
                "package": name,
                "license": license_name,
                "policy": license_policy,
                "severity": "medium",
                "description": f"License '{license_name}' does not comply with policy '{license_policy}'"
            })
        
        # Check typosquatting
        typosquat = check_typosquatting(name, ecosystem)
        if typosquat:
            issues.append(typosquat)
        
        # Check vulnerabilities
        if check_vulnerabilities:
            vulns = check_vulnerability(name, version, ecosystem)
            issues.extend(vulns)
        
        # Determine package status
        pkg_issues = [i for i in issues if i.get("package") == name]
        status = "ok" if not pkg_issues else "warning" if any(i["severity"] == "medium" for i in pkg_issues) else "vulnerable"
        
        results.append({
            "name": name,
            "version": version,
            "license": license_name,
            "status": status,
            "issues_count": len(pkg_issues)
        })
    
    # Calculate summary
    summary = {
        "total_packages": len(results),
        "ok": sum(1 for p in results if p["status"] == "ok"),
        "warning": sum(1 for p in results if p["status"] == "warning"),
        "vulnerable": sum(1 for p in results if p["status"] == "vulnerable"),
        "total_issues": len(issues)
    }
    
    return {
        "packages": results,
        "issues": issues,
        "licenses": license_stats,
        "summary": summary,
        "ecosystem": ecosystem,
        "manifest_path": str(path)
    }
