// Compile for x86 (32-bit):
//   "C:\\Windows\\Microsoft.NET\\Framework\\v4.0.30319\\csc.exe" /platform:x86 /nologo /r:System.Data.dll Program.cs
//
// Examples:
//   Program.exe
//   Program.exe --base "C:\\Oracle\\Ora12_32\\client"
//   Program.exe --oracle-dll "C:\\Oracle\\Ora12_32\\client\\odp.net\\bin\\2.x\\Oracle.DataAccess.dll"
//   Program.exe --instant "C:\\Oracle\\Ora12_32\\client\\bin"
//   Program.exe --conn-name "MyConn"
//
using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data.Common;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

static class Program
{
    [DllImport("kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr LoadLibrary(string lpFileName);

    private static string _defaultBase = @"C:\Oracle\Ora12_32\client";
    private static string _defaultOdpRoot = @"C:\Oracle\Ora12_32\client\odp.net";

    private static int Main(string[] args)
    {
        string oracleDllArg = null;   // --oracle-dll <path>
        string instantArg   = null;   // --instant <path with oci.dll>
        string connName     = null;   // --conn-name <name>
        string baseRoot     = _defaultBase; // --base <dir>
        bool verbose        = false;

        for (int i = 0; i < args.Length; i++)
        {
            string a = args[i];
            if (a == "--oracle-dll" && i + 1 < args.Length) oracleDllArg = args[++i];
            else if (a == "--instant" && i + 1 < args.Length) instantArg = args[++i];
            else if (a == "--conn-name" && i + 1 < args.Length) connName = args[++i];
            else if (a == "--base" && i + 1 < args.Length) baseRoot = args[++i];
            else if (a == "--verbose") verbose = true;
        }

        Console.WriteLine("==============================================================");
        Console.WriteLine("Oracle.DataAccess x86 Diagnostic (auto-discovery)");
        Console.WriteLine("==============================================================");
        Console.WriteLine(string.Format("Process bitness: {0} | CLR: {1}",
            (IntPtr.Size == 4 ? "32-bit" : "64-bit"), Environment.Version));
        Console.WriteLine(string.Format(".NET Framework dir: {0}", RuntimeEnvironment.GetRuntimeDirectory()));
        Console.WriteLine(string.Format("Base search root: {0}", baseRoot));

        // 1) Find 32-bit oci.dll (unless user forced --instant)
        string ociFolder = null;
        if (!string.IsNullOrWhiteSpace(instantArg))
        {
            if (Directory.Exists(instantArg)) ociFolder = instantArg;
            Console.WriteLine(string.Format("[INFO] Using --instant folder for native client: {0}", instantArg));
        }
        else
        {
            Console.WriteLine("[INFO] Searching for 32-bit oci.dll under base root...");
            ociFolder = FindOciFolder32(baseRoot, verbose);
            if (ociFolder == null)
            {
                Console.WriteLine("[WARN] Could not locate a 32-bit oci.dll under base root.");
            }
            else
            {
                Console.WriteLine(string.Format("[OK]  Found 32-bit oci.dll in: {0}", ociFolder));
            }
        }

        // Prepend PATH if we found a folder
        if (!string.IsNullOrWhiteSpace(ociFolder))
        {
            var path = Environment.GetEnvironmentVariable("PATH") ?? "";
            Environment.SetEnvironmentVariable("PATH", ociFolder + ";" + path);
            if (verbose) Console.WriteLine(string.Format("[INFO] PATH updated (prepended): {0}", ociFolder));
        }

        // 2) Load oci.dll in this 32-bit process
        Console.WriteLine("\n-- Native oci.dll check -------------------------------------");
        try
        {
            var h = LoadLibrary("oci.dll");
            if (h != IntPtr.Zero)
            {
                Console.WriteLine("[OK]  oci.dll loaded successfully.");
            }
            else
            {
                int err = Marshal.GetLastWin32Error();
                Console.WriteLine(string.Format("[WARN] oci.dll failed to load. GetLastError={0} (193=mismatch; 126=not found).", err));
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("[ERR] Exception while loading oci.dll: {0}", ex.Message));
        }

        // 3) Find Oracle.DataAccess.dll if not specified
        string oracleDllPath = oracleDllArg;
        if (string.IsNullOrWhiteSpace(oracleDllPath))
        {
            Console.WriteLine("\n[INFO] No --oracle-dll provided; scanning for Oracle.DataAccess.dll under odp.net...");
            string odpRoot = Path.Combine(baseRoot, "odp.net");
            if (!Directory.Exists(odpRoot)) odpRoot = _defaultOdpRoot;
            var candidates = FindOracleDataAccessDlls(odpRoot, verbose);
            if (candidates.Count == 0)
            {
                Console.WriteLine(string.Format("[WARN] No Oracle.DataAccess.dll found under: {0}", odpRoot));
            }
            else
            {
                // Choose highest file version
                candidates.Sort((a, b) => CompareVersions(a.VersionString, b.VersionString));
                var chosen = candidates[candidates.Count - 1];
                oracleDllPath = chosen.Path;
                Console.WriteLine(string.Format("[OK]  Selected Oracle.DataAccess.dll: {0}  (FileVersion={1})", chosen.Path, chosen.VersionString ?? "<unknown>"));

                // Log EF6 / PublisherPolicy nearby if present
                ReportOdpNetExtras(chosen.Path, verbose);
            }
        }
        else
        {
            Console.WriteLine(string.Format("\n[INFO] Using provided Oracle.DataAccess.dll: {0}", oracleDllPath));
            ReportOdpNetExtras(oracleDllPath, verbose);
        }

        // 4) Try to load Oracle.DataAccess
        Console.WriteLine("\n-- Managed Oracle.DataAccess check --------------------------");
        Assembly asm = null;
        try
        {
            if (!string.IsNullOrWhiteSpace(oracleDllPath) && File.Exists(oracleDllPath))
            {
                asm = Assembly.LoadFrom(oracleDllPath);
                Console.WriteLine(string.Format("[OK]  Assembly loaded via LoadFrom: {0}", asm.FullName));
            }
            else
            {
                Console.WriteLine("[INFO] Loading by name (GAC/app.config/codeBase)...");
                asm = Assembly.Load("Oracle.DataAccess");
                Console.WriteLine(string.Format("[OK]  Assembly loaded: {0}", asm.FullName));
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("[ERR] Failed to load Oracle.DataAccess: {0}", ex));
            return 2;
        }

        // 5) OracleClientFactory.Instance
        Console.WriteLine("\n-- OracleClientFactory.Instance -----------------------------");
        try
        {
            var t = asm.GetType("Oracle.DataAccess.Client.OracleClientFactory", false);
            if (t == null)
            {
                Console.WriteLine("[ERR] Type Oracle.DataAccess.Client.OracleClientFactory not found.");
            }
            else
            {
                var prop = t.GetProperty("Instance", BindingFlags.Public | BindingFlags.Static);
                var instance = prop != null ? prop.GetValue(null, null) : null;
                if (instance != null)
                {
                    Console.WriteLine(string.Format("[OK]  OracleClientFactory.Instance acquired: {0}", instance.GetType().FullName));
                    Console.WriteLine(string.Format("      From assembly: {0}", instance.GetType().Assembly.FullName));
                }
                else
                {
                    Console.WriteLine("[ERR] OracleClientFactory.Instance returned null.");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("[ERR] Getting OracleClientFactory.Instance failed: {0}", ex));
        }

        // 6) DbProviderFactories
        Console.WriteLine("\n-- DbProviderFactories.GetFactory(\"Oracle.DataAccess.Client\") ---");
        try
        {
            var fac = DbProviderFactories.GetFactory("Oracle.DataAccess.Client");
            Console.WriteLine(string.Format("[OK]  DbProviderFactories returned: {0}", fac));
            Console.WriteLine(string.Format("      Factory type: {0}", fac.GetType().FullName));
            Console.WriteLine(string.Format("      Factory asm:  {0}", fac.GetType().Assembly.FullName));
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("[WARN] DbProviderFactories.GetFactory failed: {0}", ex.Message));
            Console.WriteLine("       (Add app-local provider entry under <system.data>/<DbProviderFactories>.)");
        }

        // 7) Optional connection test from config
        if (!string.IsNullOrWhiteSpace(connName))
        {
            Console.WriteLine(string.Format("\n-- Connection test using <connectionStrings>['{0}'] ----", connName));
            try
            {
                var elem = ConfigurationManager.ConnectionStrings[connName];
                if (elem == null)
                {
                    Console.WriteLine(string.Format("[ERR] No connection string named '{0}' found.", connName));
                }
                else
                {
                    Console.WriteLine(string.Format("[INFO] providerName: {0}", elem.ProviderName ?? "<null>"));
                    Console.WriteLine(string.Format("[INFO] connString  : {0}", string.IsNullOrWhiteSpace(elem.ConnectionString) ? "<empty>" : "<present>"));

                    var connType = asm.GetType("Oracle.DataAccess.Client.OracleConnection", false);
                    if (connType == null)
                    {
                        Console.WriteLine("[ERR] OracleConnection type not found.");
                    }
                    else
                    {
                        using (var conn = (IDisposable)Activator.CreateInstance(connType, new object[] { elem.ConnectionString }))
                        {
                            var open = connType.GetMethod("Open");
                            var close = connType.GetMethod("Close");
                            try
                            {
                                open.Invoke(conn, null);
                                Console.WriteLine("[OK]  Connection.Open() succeeded.");
                            }
                            catch (TargetInvocationException tie)
                            {
                                Console.WriteLine(string.Format("[ERR] Connection.Open() threw: {0}",
                                    tie.InnerException != null ? tie.InnerException.Message : tie.Message));
                            }
                            finally
                            {
                                try { close.Invoke(conn, null); } catch { }
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("[ERR] Connection test failed: {0}", ex));
            }
        }

        Console.WriteLine("\n==============================================================");
        Console.WriteLine("Done.");
        return 0;
    }

    // ---------- Discovery helpers ----------

    private static string FindOciFolder32(string baseRoot, bool verbose)
    {
        try
        {
            if (!Directory.Exists(baseRoot)) return null;
            foreach (var path in SafeEnumerateFiles(baseRoot, "oci.dll"))
            {
                if (verbose) Console.WriteLine(string.Format("[DBG] candidate oci.dll: {0}", path));
                if (IsPe32Native(path))
                {
                    return Path.GetDirectoryName(path);
                }
            }
        }
        catch { /* ignore */ }
        return null;
    }

    private class OdpDll
    {
        public string Path;
        public string VersionString;
    }

    private static List<OdpDll> FindOracleDataAccessDlls(string odpRoot, bool verbose)
    {
        var list = new List<OdpDll>();
        try
        {
            if (!Directory.Exists(odpRoot)) return list;
            foreach (var path in SafeEnumerateFiles(odpRoot, "Oracle.DataAccess.dll"))
            {
                string v = GetFileVersionSafe(path);
                if (verbose) Console.WriteLine(string.Format("[DBG] candidate ODP: {0}  (FileVersion={1})", path, v ?? "<unknown>"));
                list.Add(new OdpDll { Path = path, VersionString = v });
            }
        }
        catch { /* ignore */ }
        return list;
    }

    private static int CompareVersions(string a, string b)
    {
        Version va, vb;
        if (!Version.TryParse(a, out va)) va = new Version(0, 0, 0, 0);
        if (!Version.TryParse(b, out vb)) vb = new Version(0, 0, 0, 0);
        return va.CompareTo(vb);
    }

    private static void ReportOdpNetExtras(string oracleDllPath, bool verbose)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(oracleDllPath)) return;
            var dllDir = Path.GetDirectoryName(oracleDllPath);
            if (dllDir == null) return;

            // PublisherPolicy siblings
            var odpRoot = FindAncestor(dllDir, "odp.net");
            if (odpRoot != null)
            {
                // Look for PublisherPolicy\2.x and \4
                var pp2 = Path.Combine(odpRoot, "PublisherPolicy", "2.x");
                var pp4 = Path.Combine(odpRoot, "PublisherPolicy", "4");
                int count = 0;

                count += ReportPolicies(pp2, verbose);
                count += ReportPolicies(pp4, verbose);

                if (count == 0 && verbose)
                    Console.WriteLine("[DBG] No Oracle.DataAccess publisher policy files detected.");
            }

            // EF6 dlls (EntityFramework provider), sometimes beside \4\EF6
            var ef6Dir = Path.Combine(dllDir, "EF6");
            if (Directory.Exists(ef6Dir))
            {
                foreach (var f in SafeEnumerateFiles(ef6Dir, "*.dll"))
                {
                    Console.WriteLine(string.Format("[INFO] EF6 provider file: {0}", f));
                }
            }
        }
        catch { /* ignore */ }
    }

    private static int ReportPolicies(string dir, bool verbose)
    {
        int count = 0;
        try
        {
            if (Directory.Exists(dir))
            {
                foreach (var f in SafeEnumerateFiles(dir, "Policy*.Oracle.DataAccess.*"))
                {
                    string v = GetFileVersionSafe(f);
                    Console.WriteLine(string.Format("[INFO] PublisherPolicy: {0}  (FileVersion={1})", f, v ?? "<unknown>"));
                    count++;
                }
            }
        }
        catch { /* ignore */ }
        return count;
    }

    private static string FindAncestor(string startDir, string name)
    {
        try
        {
            var cur = new DirectoryInfo(startDir);
            while (cur != null)
            {
                if (string.Equals(cur.Name, name, StringComparison.OrdinalIgnoreCase))
                    return cur.FullName;
                cur = cur.Parent;
            }
        }
        catch { /* ignore */ }
        return null;
    }

    private static string GetFileVersionSafe(string path)
    {
        try
        {
            var vi = FileVersionInfo.GetVersionInfo(path);
            return vi != null ? vi.FileVersion : null;
        }
        catch { return null; }
    }

    private static IEnumerable<string> SafeEnumerateFiles(string root, string pattern)
    {
        var stack = new Stack<string>();
        if (!string.IsNullOrWhiteSpace(root) && Directory.Exists(root))
            stack.Push(root);

        while (stack.Count > 0)
        {
            string dir = stack.Pop();
            string[] subdirs = new string[0];
            try { subdirs = Directory.GetDirectories(dir); } catch { }
            for (int i = 0; i < subdirs.Length; i++) stack.Push(subdirs[i]);

            string[] files = new string[0];
            try { files = Directory.GetFiles(dir, pattern); } catch { }
            for (int i = 0; i < files.Length; i++) yield return files[i];
        }
    }

    // Heuristic: check PE OptionalHeader.Magic == 0x10B (PE32) versus 0x20B (PE32+)
    private static bool IsPe32Native(string filePath)
    {
        try
        {
            using (var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (var br = new BinaryReader(fs))
            {
                // MZ header
                if (br.ReadUInt16() != 0x5A4D) return false; // 'MZ'
                fs.Seek(0x3C, SeekOrigin.Begin);
                int e_lfanew = br.ReadInt32();
                if (e_lfanew <= 0) return false;
                fs.Seek(e_lfanew, SeekOrigin.Begin);
                if (br.ReadUInt32() != 0x00004550) return false; // 'PE\0\0'
                fs.Seek(20, SeekOrigin.Current); // skip IMAGE_FILE_HEADER (20 bytes)
                ushort magic = br.ReadUInt16();  // OptionalHeader.Magic
                // 0x10B = PE32 (32-bit), 0x20B = PE32+ (64-bit)
                return magic == 0x10B;
            }
        }
        catch { return false; }
    }
}
