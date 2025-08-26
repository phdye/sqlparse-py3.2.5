// Compile for x86 (32-bit):
//   "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe" /platform:x86 /unsafe /nologo /r:System.Data.dll Program.cs
//
// Example runs:
//   Program.exe --oracle-dll "C:\Oracle\Ora12_32\client\odp.net\bin\2.x\Oracle.DataAccess.dll" --instant "C:\Oracle\Ora12_32\client\bin"
//   Program.exe --conn-name "MyConn" --instant "C:\Oracle\instantclient_19_26"
//   Program.exe   (relies on your app.config codeBase/bindingRedirect and PATH)

using System;
using System.Configuration;
using System.Data.Common;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

static class Program
{
    // P/Invoke LoadLibrary to test native oci.dll availability in a 32-bit host
    [DllImport("kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr LoadLibrary(string lpFileName);

    private static int Main(string[] args)
    {
        string oracleDll = null;        // --oracle-dll <path to Oracle.DataAccess.dll>
        string instant = null;          // --instant <path to folder containing oci.dll>
        string connName = null;         // --conn-name <name in <connectionStrings>>

        // very light arg parse
        for (int i = 0; i < args.Length; i++)
        {
            var a = args[i];
            if (a == "--oracle-dll" && i + 1 < args.Length) oracleDll = args[++i];
            else if (a == "--instant" && i + 1 < args.Length) instant = args[++i];
            else if (a == "--conn-name" && i + 1 < args.Length) connName = args[++i];
        }

        Console.WriteLine("==============================================================");
        Console.WriteLine("Oracle.DataAccess x86 Diagnostic");
        Console.WriteLine("==============================================================");
        Console.WriteLine($"Process bitness: {(IntPtr.Size == 4 ? "32-bit" : "64-bit")}  |  CLR: {Environment.Version}");
        Console.WriteLine($".NET Framework dir: {RuntimeEnvironment.GetRuntimeDirectory()}");

        // 1) PATH tweak (optional)
        if (!string.IsNullOrWhiteSpace(instant))
        {
            Console.WriteLine($"[INFO] Prepending to PATH: {instant}");
            var path = Environment.GetEnvironmentVariable("PATH") ?? "";
            Environment.SetEnvironmentVariable("PATH", instant + ";" + path);
        }

        // 2) Try loading oci.dll directly
        Console.WriteLine("\n-- Native oci.dll check -------------------------------------");
        try
        {
            var h = LoadLibrary("oci.dll");
            if (h != IntPtr.Zero)
            {
                Console.WriteLine("[OK]  oci.dll loaded successfully in this 32-bit process.");
            }
            else
            {
                int err = Marshal.GetLastWin32Error();
                Console.WriteLine($"[WARN] oci.dll failed to load. GetLastError={err} (193 likely = bitness mismatch; 126 = not found).");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ERR] Exception while loading oci.dll: {ex.Message}");
        }

        // 3) Load Oracle.DataAccess assembly
        Console.WriteLine("\n-- Managed Oracle.DataAccess check --------------------------");
        Assembly asm = null;
        try
        {
            if (!string.IsNullOrWhiteSpace(oracleDll))
            {
                Console.WriteLine($"[INFO] Loading Oracle.DataAccess from: {oracleDll}");
                asm = Assembly.LoadFrom(oracleDll);
            }
            else
            {
                Console.WriteLine("[INFO] Loading Oracle.DataAccess by name (GAC/app.config/codeBase).");
                asm = Assembly.Load("Oracle.DataAccess");
            }
            Console.WriteLine($"[OK]  Assembly loaded: {asm.FullName}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ERR] Failed to load Oracle.DataAccess: {ex}");
            return 2;
        }

        // 4) OracleClientFactory.Instance
        Console.WriteLine("\n-- OracleClientFactory.Instance -----------------------------");
        try
        {
            var t = asm.GetType("Oracle.DataAccess.Client.OracleClientFactory", throwOnError: false);
            if (t == null)
            {
                Console.WriteLine("[ERR] Type Oracle.DataAccess.Client.OracleClientFactory not found.");
            }
            else
            {
                var prop = t.GetProperty("Instance", BindingFlags.Public | BindingFlags.Static);
                var instance = prop?.GetValue(null, null);
                if (instance != null)
                {
                    Console.WriteLine($"[OK]  OracleClientFactory.Instance acquired: {instance.GetType().FullName}");
                    Console.WriteLine($"      From assembly: {instance.GetType().Assembly.FullName}");
                }
                else
                {
                    Console.WriteLine("[ERR] OracleClientFactory.Instance returned null.");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ERR] Getting OracleClientFactory.Instance failed: {ex}");
        }

        // 5) DbProviderFactories lookup (requires app-local registration if no machine.config entries)
        Console.WriteLine("\n-- DbProviderFactories.GetFactory(\"Oracle.DataAccess.Client\") ---");
        try
        {
            var fac = DbProviderFactories.GetFactory("Oracle.DataAccess.Client");
            Console.WriteLine($"[OK]  DbProviderFactories returned: {fac}");
            Console.WriteLine($"      Factory type: {fac.GetType().FullName}");
            Console.WriteLine($"      Factory asm:  {fac.GetType().Assembly.FullName}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[WARN] DbProviderFactories.GetFactory failed: {ex.Message}");
            Console.WriteLine("       (Add app-local provider entry under <system.data>/<DbProviderFactories>.)");
        }

        // 6) Optional: open a connection using a named connection string
        if (!string.IsNullOrWhiteSpace(connName))
        {
            Console.WriteLine($"\n-- Connection test using <connectionStrings>['{connName}'] ----");
            try
            {
                var elem = ConfigurationManager.ConnectionStrings[connName];
                if (elem == null)
                {
                    Console.WriteLine($"[ERR] No connection string named '{connName}' found.");
                }
                else
                {
                    Console.WriteLine($"[INFO] providerName: {elem.ProviderName ?? "<null>"}");
                    Console.WriteLine($"[INFO] connString  : {(string.IsNullOrWhiteSpace(elem.ConnectionString) ? "<empty>" : "<present>")}");

                    // Late-bind OracleConnection so we don't need a hard reference
                    var connType = asm.GetType("Oracle.DataAccess.Client.OracleConnection", throwOnError: false);
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
                                Console.WriteLine($"[ERR] Connection.Open() threw: {tie.InnerException?.Message ?? tie.Message}");
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
                Console.WriteLine($"[ERR] Connection test failed: {ex}");
            }
        }

        Console.WriteLine("\n==============================================================");
        Console.WriteLine("Done.");
        return 0;
    }
}
