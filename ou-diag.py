# ou-diag.py
# Diagnostic script for Oracle ODP.NET (Oracle.DataAccess) binding/loader issues
#
# Usage examples:
#   python ou-diag.py --exe "C:\Path\To\App.exe"
#   python ou-diag.py --config "C:\Path\To\App.exe.config" --oracle-dll "C:\Oracle\...\Oracle.DataAccess.dll"
#   python ou-diag.py --instant-client-dir "C:\Oracle\instantclient_19_17"
#
# Notes:
# - Works WITHOUT admin rights.
# - Uses optional 'pythonnet' to attempt real .NET loads if available. Otherwise, performs static checks.
# - Attempts to load oci.dll via ctypes to verify native client presence/bitness.
#
import argparse
import ctypes
import os
import platform
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

RESULTS = []
WARNINGS = []
ERRORS = []
DETAILS = []

def add(section, message):
    DETAILS.append(f"[{section}] {message}")

def warn(message):
    WARNINGS.append(message)

def error(message):
    ERRORS.append(message)

def ok(message):
    RESULTS.append(message)

def parse_args():
    p = argparse.ArgumentParser(description="Oracle Utilities ODP.NET diagnostic (Oracle.DataAccess)")
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--config", help="Path to app.exe.config (or web.config)")
    g.add_argument("--exe", help="Path to application EXE to derive <exe>.config")
    p.add_argument("--oracle-dll", help="Explicit path to Oracle.DataAccess.dll (managed ODP.NET)")
    p.add_argument("--instant-client-dir", help="Folder containing native DLLs (oci.dll, etc.). Will be prepended to PATH at runtime for this process.")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    return p.parse_args()

def find_config(args):
    if args.config:
        return Path(args.config)
    if args.exe:
        exe = Path(args.exe)
        return exe.with_suffix(exe.suffix + ".config")
    return None

def read_config_xml(cfg_path: Path):
    if not cfg_path or not cfg_path.exists():
        error(f"Config file not found: {cfg_path}")
        return None, {}
    try:
        text = cfg_path.read_text(encoding="utf-8")
    except Exception:
        text = cfg_path.read_text(errors="ignore")
    try:
        tree = ET.fromstring(text)
    except Exception as e:
        error(f"Failed to parse XML config: {e}")
        return None, {}
    ns = {"asm": "urn:schemas-microsoft-com:asm.v1"}
    result = {
        "bindingRedirect_new": None,
        "bindingRedirect_old": None,
        "codeBase_href": None,
        "codeBase_version": None,
        "factory_type": None,
        "factory_version": None,
        "provider_present": False,
    }
    # assemblyBinding/dependentAssembly for Oracle.DataAccess
    for dep in tree.findall(".//runtime/asm:assemblyBinding/asm:dependentAssembly", ns):
        asm_id = dep.find("asm:assemblyIdentity", ns)
        if asm_id is not None and asm_id.get("name") == "Oracle.DataAccess":
            br = dep.find("asm:bindingRedirect", ns)
            if br is not None:
                result["bindingRedirect_old"] = br.get("oldVersion")
                result["bindingRedirect_new"] = br.get("newVersion")
            cb = dep.find("asm:codeBase", ns)
            if cb is not None:
                result["codeBase_href"] = cb.get("href")
                result["codeBase_version"] = cb.get("version")
    # DbProviderFactories entry
    fac = tree.find(".//system.data/DbProviderFactories/add")
    if fac is not None:
        if fac.get("invariant") == "Oracle.DataAccess.Client":
            result["provider_present"] = True
            result["factory_type"] = fac.get("type")
            # Extract version from type string: "..., Oracle.DataAccess, Version=2.122.1.0, Culture=..."
            m = re.search(r"Version=([\d\.]+)", result["factory_type"] or "")
            if m:
                result["factory_version"] = m.group(1)
    return tree, result

def uri_to_path(uri: str):
    if not uri:
        return None
    # Expecting file:///C:/...
    if uri.lower().startswith("file:///"):
        return Path(uri[8:])
    if uri.lower().startswith("file://"):
        # less common case
        return Path(uri[7:])
    # allow raw windows path if user provided
    return Path(uri)

def get_file_version_win(path: Path):
    """
    Try to read Windows file version info via ctypes.
    Returns 'major.minor.build.revision' or None.
    """
    try:
        # GetFileVersionInfoSizeW
        size = ctypes.windll.version.GetFileVersionInfoSizeW(str(path), None)
        if not size:
            return None
        import struct
        res = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(str(path), 0, size, res):
            return None
        u_len = ctypes.c_uint()
        u_ptr = ctypes.c_void_p()
        if not ctypes.windll.version.VerQueryValueW(res, "\\", ctypes.byref(u_ptr), ctypes.byref(u_len)):
            return None
        # VS_FIXEDFILEINFO structure
        # Read as two DWORDs for version MS and LS
        buf = (ctypes.c_byte * u_len.value).from_address(u_ptr.value)
        data = bytes(buf[:u_len.value])
        # fixed offsets: https://learn.microsoft.com/windows/win32/api/verrsrc/ns-verrsrc-vs_fixedfileinfo
        dwFileVersionMS = int.from_bytes(data[40:44], "little")
        dwFileVersionLS = int.from_bytes(data[44:48], "little")
        major = (dwFileVersionMS >> 16) & 0xFFFF
        minor = dwFileVersionMS & 0xFFFF
        build = (dwFileVersionLS >> 16) & 0xFFFF
        rev = dwFileVersionLS & 0xFFFF
        return f"{major}.{minor}.{build}.{rev}"
    except Exception:
        return None

def try_load_oci(instant_dir=None):
    """
    Try to load oci.dll to verify native Oracle client availability.
    Return (ok, message)
    """
    try:
        if instant_dir and os.path.isdir(instant_dir):
            os.environ["PATH"] = instant_dir + os.pathsep + os.environ.get("PATH", "")
            add("PATH", f"Prepended instant client dir to PATH: {instant_dir}")
        ctypes.WinDLL("oci.dll")
        return True, "oci.dll loaded successfully (native Oracle Client present on PATH)"
    except OSError as e:
        # ERROR_BAD_EXE_FORMAT (193) often indicates bitness mismatch
        if hasattr(e, "winerror") and e.winerror == 193:
            return False, "oci.dll found but cannot be loaded (ERROR 193) — likely 32/64-bit mismatch"
        return False, f"oci.dll not found or failed to load: {e}"
    except Exception as e:
        return False, f"Unexpected error when loading oci.dll: {e}"

def dotted_to_tuple(v):
    try:
        return tuple(int(x) for x in (v or "").split("."))
    except Exception:
        return tuple()

def check_bitness_hints(oracle_dll_path: Path):
    hints = []
    pybits = 64 if sys.maxsize > 2**32 else 32
    hints.append(f"Python process bitness: {pybits}-bit ({platform.architecture()[0]})")
    if oracle_dll_path:
        pstr = str(oracle_dll_path).lower()
        if "\\bin\\2.x" in pstr or "client32" in pstr or "ora12_32" in pstr or "wow" in pstr:
            hints.append("Oracle managed DLL path suggests 32-bit client")
        if "\\bin\\4" in pstr or "x64" in pstr or "client64" in pstr:
            hints.append("Oracle managed DLL path suggests 64-bit client")
    return hints

def try_pythonnet_load(oracle_dll_path: Path):
    """
    If pythonnet is available, attempt to:
      - Load Oracle.DataAccess (from GAC or provided path)
      - Obtain OracleClientFactory.Instance
      - Use DbProviderFactories if config registers it
    """
    try:
        import clr  # type: ignore
        from System import AppDomain
        from System import EventHandler
        from System.Reflection import Assembly, ResolveEventArgs
        from System.Data.Common import DbProviderFactories
    except Exception as e:
        warn("pythonnet not available; skipping .NET runtime load tests. (pip install pythonnet)")
        return {
            "pythonnet": False,
            "assembly_loaded": False,
            "factory_instance": False,
            "dbprovider_factory": False,
            "assembly_fullname": None,
            "factory_fullname": None,
            "factory_asm_fullname": None,
            "errors": [str(e)],
        }

    data = {
        "pythonnet": True,
        "assembly_loaded": False,
        "factory_instance": False,
        "dbprovider_factory": False,
        "assembly_fullname": None,
        "factory_fullname": None,
        "factory_asm_fullname": None,
        "errors": [],
    }

    def _resolve(sender, args):
        try:
            if args.Name and args.Name.startswith("Oracle.DataAccess"):
                if oracle_dll_path and oracle_dll_path.exists():
                    return Assembly.LoadFrom(str(oracle_dll_path))
        except Exception as ee:
            data["errors"].append(f"Resolver failed: {ee}")
        return None

    try:
        AppDomain.CurrentDomain.AssemblyResolve += EventHandler[ResolveEventArgs](_resolve)
        # Load System.Data so DbProviderFactories is present
        Assembly.Load("System.Data")
    except Exception as e:
        data["errors"].append(f"Preload System.Data failed: {e}")

    # Attempt Assembly.Load by name (falls back to GAC), else explicit path
    asm = None
    try:
        asm = Assembly.Load("Oracle.DataAccess")
    except Exception as e1:
        try:
            if oracle_dll_path and oracle_dll_path.exists():
                asm = Assembly.LoadFrom(str(oracle_dll_path))
        except Exception as e2:
            data["errors"].append(f"Assembly load failed: {e1}; then LoadFrom failed: {e2}")

    if asm is not None:
        data["assembly_loaded"] = True
        data["assembly_fullname"] = str(asm.FullName)

    # Try OracleClientFactory.Instance
    try:
        if asm is not None:
            t = asm.GetType("Oracle.DataAccess.Client.OracleClientFactory", False)
            if t is not None:
                inst_prop = t.GetProperty("Instance")
                if inst_prop is not None:
                    inst = inst_prop.GetValue(None, None)
                    if inst is not None:
                        data["factory_instance"] = True
                        data["factory_fullname"] = str(inst.GetType().FullName)
                        data["factory_asm_fullname"] = str(inst.GetType().Assembly.FullName)
    except Exception as e:
        data["errors"].append(f"OracleClientFactory.Instance failed: {e}")

    # Try DbProviderFactories.GetFactory
    try:
        fac = DbProviderFactories.GetFactory("Oracle.DataAccess.Client")
        if fac is not None:
            data["dbprovider_factory"] = True
            # enrich details
            data["factory_fullname"] = data["factory_fullname"] or str(fac.GetType().FullName)
            data["factory_asm_fullname"] = data["factory_asm_fullname"] or str(fac.GetType().Assembly.FullName)
    except Exception as e:
        data["errors"].append(f"DbProviderFactories.GetFactory failed: {e}")

    return data

def main():
    args = parse_args()

    ok(f"OS: {platform.system()} {platform.release()} | Python: {platform.python_version()} | Arch: {platform.architecture()[0]}")
    if args.verbose:
        add("ENV", f"PATH(0..120): {os.environ.get('PATH','')[:120]}...")

    # Step 1: identify config
    cfg = find_config(args)
    if cfg:
        ok(f"Config path: {cfg}")
    else:
        warn("No --config or --exe provided. Some checks (connectionStrings, redirects) will be skipped.")

    # Step 2: parse config (if present)
    config_info = {}
    if cfg and cfg.exists():
        _, config_info = read_config_xml(cfg)
        if config_info.get("bindingRedirect_new"):
            ok(f"bindingRedirect present: old='{config_info['bindingRedirect_old']}' -> new='{config_info['bindingRedirect_new']}'")
        else:
            warn("No bindingRedirect for Oracle.DataAccess found in config")

        if config_info.get("codeBase_href"):
            codebase_path = uri_to_path(config_info["codeBase_href"])
            ok(f"codeBase href: {config_info['codeBase_href']} -> {codebase_path}")
            if not codebase_path.exists():
                error(f"codeBase target path does not exist: {codebase_path}")
        else:
            warn("No codeBase href found for Oracle.DataAccess in config")

        if config_info.get("provider_present"):
            ok("DbProviderFactories entry for 'Oracle.DataAccess.Client' present")
            if config_info.get("factory_version"):
                ok(f"Provider 'type' references Version={config_info['factory_version']}")
        else:
            warn("No DbProviderFactories entry for 'Oracle.DataAccess.Client' in config (app-local)")
    else:
        if cfg and not cfg.exists():
            error(f"Config file does not exist: {cfg}")

    # Step 3: determine Oracle.DataAccess.dll path
    oracle_dll_path = None
    if args.oracle_dll:
        oracle_dll_path = Path(args.oracle_dll)
        ok(f"Oracle DLL provided: {oracle_dll_path}")
    else:
        if config_info.get("codeBase_href"):
            oracle_dll_path = uri_to_path(config_info["codeBase_href"])
            ok(f"Oracle DLL inferred from codeBase: {oracle_dll_path}")
        else:
            # try next to EXE
            if args.exe:
                candidate = Path(args.exe).with_name("Oracle.DataAccess.dll")
                if candidate.exists():
                    oracle_dll_path = candidate
                    ok(f"Oracle DLL found next to EXE: {oracle_dll_path}")

    if oracle_dll_path and not oracle_dll_path.exists():
        error(f"Oracle.DataAccess.dll path not found: {oracle_dll_path}")

