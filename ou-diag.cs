// Compile for x86 (32-bit):
//   "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe" /platform:x86 /nologo /r:System.Data.dll Program.cs
//
// Example run using full ODAC 32-bit client:
//   Program.exe --oracle-dll "C:\Oracle\Ora12_32\client\odp.net\bin\2.x\Oracle.DataAccess.dll" --instant "C:\Oracle\Ora12_32\client\bin"

using System;
using System.Configuration;
using System.Data.Common;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

static class Program
{
    [DllImport("kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr LoadLibrary(string lpFileName);

    private static int Main(string[] args)
    {
        string oracleDll = null;
        string instant = null;
        string connName = null;

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
        Console.WriteLine(String.Format("Process bitness: {0}  |  CLR: {1}", 
            (IntPtr.Size == 4 ? "32-bit" : "64-bit"), Environment.Version));
        Console.WriteLine(String.Format(".NET Framework dir: {0}", RuntimeEnvironment.GetRuntimeDirectory()));

        // PATH tweak
        if (!string.IsNullOrWhiteSpace(instant))
        {
            Console.WriteLine(String.Format("[INFO] Prepending to PATH: {0}", instant));
            var path = Environment.GetEnvironmentVariable("PATH") ?? "";
            Environment.SetEnvironmentVariable("PATH", instant + ";" + path);
        }

        // Try oci.dll
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
                Console.WriteLine(String.Format("[WARN] oci.dll failed to load. GetLastError={0} (193=mismatch; 126=not found).", err));
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine(String.Format("[ERR] Exception while loading oci.dll: {0}", ex.Message));
        }

        // Load Oracle.DataAccess
        Console.WriteLine("\n-- Managed Oracle.DataAccess check --------------------------");
        Assembly asm = null;
        try
        {
            if (!string.IsNullOrWhiteSpace(oracleDll))
            {
                Console.WriteLine(String.Format("[INFO] Loading Oracle.DataAccess from: {0}", oracleDll));
                asm = Assembly.LoadFrom(oracleDll);
            }
            else
            {
                Console.WriteLine("[INFO] Loading Oracle.DataAccess by name (GAC/app.config/codeBase).");
                asm = Assembly.Load("Oracle.DataAccess");
            }
            Console.WriteLine(String.Format("[OK]  Assembly loaded: {0}", asm.FullName));
        }
        catch (Exception ex)
        {
            Console.WriteLine(String.Format("[ERR] Failed to load Oracle.DataAccess: {0}", ex));
            return 2;
        }

        // OracleClientFactory.Instance
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
                    Console.WriteLine(String.Format("[OK]  OracleClientFactory.Instance acquired: {0}", instance.GetType().FullName));
                    Console.WriteLine(String.Format("      From assembly: {0}", instance.GetType().Assembly.FullName));
                }
                else
                {
                    Console.WriteLine("[ERR] OracleClientFactory.Instance returned null.");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine(String.Format("[ERR] Getting OracleClientFactory.Instance failed: {0}", ex));
        }

        // DbProviderFactories
        Console.WriteLine("\n-- DbProviderFactories.GetFactory(\"Oracle.DataAccess.Client\") ---");
        try
        {
            var fac = DbProviderFactories.GetFactory("Oracle.DataAccess.Client");
            Console.WriteLine(String.Format("[OK]  DbProviderFactories returned: {0}", fac));
            Console.WriteLine(String.Format("      Factory type: {0}", fac.GetType().FullName));
            Console.WriteLine(String.Format("      Factory asm:  {0}", fac.GetType().Assembly.FullName));
        }
        catch (Exception ex)
        {
            Console.WriteLine(String.Format("[WARN] DbProviderFactories.GetFactory failed: {0}", ex.Message));
            Console.WriteLine("       (Add app-local provider entry under <system.data>/<DbProviderFactories>.)");
        }

        // Optional: connection test
        if (!string.IsNullOrWhiteSpace(connName))
        {
            Console.WriteLine(String.Format("\n-- Connection test using <connectionStrings>['{0}'] ----", connName));
            try
            {
                var elem = ConfigurationManager.ConnectionStrings[connName];
                if (elem == null)
                {
                    Console.WriteLine(String.Format("[ERR] No connection string named '{0}' found.", connName));
                }
                else
                {
                    Console.WriteLine(String.Format("[INFO] providerName: {0}", elem.ProviderName ?? "<null>"));
                    Console.WriteLine(String.Format("[INFO] connString  : {0}", 
                        string.IsNullOrWhiteSpace(elem.ConnectionString) ? "<empty>" : "<present>"));

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
                                Console.WriteLine(String.Format("[ERR] Connection.Open() threw: {0}", tie.InnerException != null ? tie.InnerException.Message : tie.Message));
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
                Console.WriteLine(String.Format("[ERR] Connection test failed: {0}", ex));
            }
        }

        Console.WriteLine("\n==============================================================");
        Console.WriteLine("Done.");
        return 0;
    }
}
