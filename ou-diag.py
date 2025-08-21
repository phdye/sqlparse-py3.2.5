#!/usr/bin/env python3
"""
Oracle Utilities ODP.NET diagnostic for Oracle.DataAccess (ou-diag.py)

This script checks everything needed to run Oracle.DataAccess without admin rights:
- app/web config: bindingRedirect, codeBase, DbProviderFactories entry
- managed DLL availability and version
- native Instant Client presence (oci.dll) and bitness hints
- optional runtime tests via pythonnet: assembly load, OracleClientFactory.Instance,
  DbProviderFactories.GetFactory("Oracle.DataAccess.Client")

Usage examples:
  python ou-diag.py --exe "C:\\Path\\To\\App.exe"
  python ou-diag.py --config "C:\\Path\\To\\App.exe.config" --oracle-dll "C:\\Oracle\\...\\Oracle.DataAccess.dll"
  python ou-diag.py --instant-client-dir "C:\\Oracle\\instantclient_19_17"

Example full command:
  python ou-diag.py --config "C:\\Apps\\OU\\Bin\\MyApp.exe.config" \
                    --oracle-dll "C:\\Oracle\\Ora12_32\\client\\odp.net\\bin\\2.x\\Oracle.DataAccess.dll" \
                    --instant-client-dir "C:\\Oracle\\instantclient_19_23" \
                    --verbose

Exit codes:
  0 = No blocking issues detected
  1 = Errors encountered
  2 = Likely root causes identified
 99 = Fatal exception in the diagnostic itself
"""

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
    p.add_argument("--instant-client-dir", help="Folder with native DLLs (oci.dll, etc.). Will be prepended to PATH for this process.")
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
    if fac is not None and fac.get("invariant") == "Oracle.DataAccess.Client":
        result["provider_present"] = True
        result["factory_type"] = fac.get("type")
        # Extract version from type string: ", Oracle.DataAccess, Version=2.122.1.0, ..."
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
    """Return Windows file version like 'major.minor.build.revision', or None."""
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(str(path), None)
        if not size:
            return None
        res = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(str(path), 0, size, res):
            return None
        u_len = ctypes.c_uint()
        u_ptr = ctypes.c_void_p()
        if not ctypes.windll.version.VerQueryValueW(res, "\\", ctypes.byref(u_ptr), ctypes.byref(u_len)):
            return None
        buf = (ctypes.c_byte * u_len.value).from_address(u_ptr.value)
        data = bytes(buf[:u_len.value])
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
    """Try to load oci.dll to verify native Oracle client availability. Return (ok, message)."""
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
    """Attempt real .NET loads using pythonnet (if installed)."""
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

    # Attempt Assembly.Load by name (GAC), else explicit path
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

    # OracleClientFactory.Instance
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

    # DbProviderFactories
    try:
        fac = DbProviderFactories.GetFactory("Oracle.DataAccess.Client")
        if fac is not None:
            data["dbprovider_factory"] = True
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
            if args.exe:
                candidate = Path(args.exe).with_name("Oracle.DataAccess.dll")
                if candidate.exists():
                    oracle_dll_path = candidate
                    ok(f"Oracle DLL found next to EXE: {oracle_dll_path}")

    if oracle_dll_path and not oracle_dll_path.exists():
        error(f"Oracle.DataAccess.dll path not found: {oracle_dll_path}")
        oracle_dll_path = None

    # Step 4: version checks on Oracle.DataAccess.dll file
    if oracle_dll_path and oracle_dll_path.exists():
        fv = get_file_version_win(oracle_dll_path)
        if fv:
            ok(f"Oracle.DataAccess.dll file version: {fv}")
            br_new = config_info.get("bindingRedirect_new")
            fac_ver = config_info.get("factory_version")
            if br_new and dotted_to_tuple(fv) != dotted_to_tuple(br_new):
                warn(f"File version ({fv}) differs from bindingRedirect newVersion ({br_new})")
            if fac_ver and dotted_to_tuple(fv) != dotted_to_tuple(fac_ver):
                warn(f"File version ({fv}) differs from DbProviderFactories type Version ({fac_ver})")
        else:
            warn("Could not read file version of Oracle.DataAccess.dll (non-Windows or missing version info)")

    # Step 5: bitness hints
    for hint in check_bitness_hints(oracle_dll_path):
        add("Bitness", hint)

    # Step 6: try loading oci.dll (native)
    oci_ok, oci_msg = try_load_oci(args.instant_client_dir)
    (ok if oci_ok else warn)(oci_msg)

    # Step 7: pythonnet-based runtime tests
    pn = try_pythonnet_load(oracle_dll_path)
    if pn.get("pythonnet"):
        if pn.get("assembly_loaded"):
            ok(f".NET: Oracle.DataAccess loaded: {pn.get('assembly_fullname')}")
        else:
            warn(".NET: Oracle.DataAccess NOT loaded (GAC/path/resolver).")

        if pn.get("factory_instance"):
            ok(".NET: OracleClientFactory.Instance retrieved")
        else:
            warn(".NET: OracleClientFactory.Instance not available (assembly loaded: %s)" % pn.get("assembly_loaded"))

        if pn.get("dbprovider_factory"):
            ok(".NET: DbProviderFactories.GetFactory('Oracle.DataAccess.Client') succeeded")
        else:
            warn(".NET: DbProviderFactories.GetFactory failed (missing app-local provider entry or machine.config registration)")

        for e in pn.get("errors", []):
            add("pythonnet", f"{e}")
    else:
        add("pythonnet", "Not installed; skipping runtime checks. Install with: pip install pythonnet")

    # Step 8: derive likely root causes
    root_causes = []

    if not oracle_dll_path:
        root_causes.append("Managed ODP.NET (Oracle.DataAccess.dll) not discoverable: specify --oracle-dll or add codeBase in config, or copy next to EXE.")

    if config_info.get("codeBase_href"):
        cbp = uri_to_path(config_info["codeBase_href"])
        if not cbp.exists():
            root_causes.append("codeBase href points to a non-existent file. Fix href or install ODAC at that path.")

    if not config_info.get("provider_present") and pn.get("pythonnet") and not pn.get("dbprovider_factory"):
        root_causes.append("DbProviderFactories entry missing. Add <system.data>/<DbProviderFactories> for Oracle.DataAccess.Client in app config.")

    if oracle_dll_path and oracle_dll_path.exists():
        dll_ver = get_file_version_win(oracle_dll_path) or ""
        if config_info.get("bindingRedirect_new") and dll_ver and dotted_to_tuple(dll_ver) != dotted_to_tuple(config_info["bindingRedirect_new"]):
            root_causes.append("bindingRedirect newVersion does not match the actual Oracle.DataAccess.dll file version.")
        if config_info.get("factory_version") and dll_ver and dotted_to_tuple(dll_ver) != dotted_to_tuple(config_info["factory_version"]):
            root_causes.append("DbProviderFactories 'type' Version does not match the actual Oracle.DataAccess.dll file version.")

    if not oci_ok:
        root_causes.append("Native Oracle Client (oci.dll) not found or failed to load. Ensure Instant Client/bin is on PATH and bitness matches the app.")

    if pn.get("pythonnet") and not pn.get("assembly_loaded"):
        root_causes.append("Runtime could not load Oracle.DataAccess (not in GAC and no valid codeBase or local copy).")

    if pn.get("pythonnet") and pn.get("assembly_loaded") and not pn.get("factory_instance"):
        root_causes.append("OracleClientFactory.Instance not available. Version mismatch or corrupted assembly.")

    # Step 9: print report
    print("="*70)
    print("Oracle Utilities ODP.NET Diagnostic (ou-diag.py)")
    print("="*70)
    for r in RESULTS:
        print("[OK]   " + r)
    for w in WARNINGS:
        print("[WARN] " + w)
    if args.verbose:
        for d in DETAILS:
            print("[INFO] " + d)
    for e in ERRORS:
        print("[ERR]  " + e)

    print("-"*70)
    if root_causes:
        print("LIKELY ROOT CAUSES:")
        for rc in root_causes:
            print("  - " + rc)
        exit_code = 2
    elif ERRORS:
        print("ERRORS encountered; see above.")
        exit_code = 1
    else:
        print("No blocking issues detected. If you're still seeing NullReferenceException, check the connectionStrings name, providerName, and app code paths.")
        exit_code = 0

    print("-"*70)
    print("Tips:")
    print(" - Use --config or --exe so the script can inspect bindingRedirect/codeBase/provider entries.")
    print(" - Use --oracle-dll to point to the exact Oracle.DataAccess.dll you want to test.")
    print(" - Use --instant-client-dir to temporarily prepend native client folder to PATH.")
    print(" - Install 'pythonnet' to enable runtime loader tests: pip install pythonnet")
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("[FATAL] " + str(ex))
        if "--verbose" in sys.argv:
            traceback.print_exc()
        sys.exit(99)
