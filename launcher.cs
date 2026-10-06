// Explicit portable startup: original PSF interpreter name, no sitecustomize.
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
using System.Reflection;
[assembly: AssemblyTitle("Mouse Macro Stocazz Superpower")]
[assembly: AssemblyCompany("hcok")]
[assembly: AssemblyVersion("0.19.1.0")]
[assembly: AssemblyFileVersion("0.19.1.0")]
class Launcher {
    [STAThread] static int Main() {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string runtime = Path.Combine(root, "runtime", "pythonw.exe");
        string app = Path.Combine(root, "app", "windows_main.py");
        if (!File.Exists(runtime) || !File.Exists(app)) {
            MessageBox.Show("Estrai tutto lo ZIP e mantieni insieme tutti i file.", "Mouse Macro 0.19.1", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        try {
            ProcessStartInfo start = new ProcessStartInfo(runtime, "-B \"" + app + "\"");
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            Process process = Process.Start(start);
            process.WaitForExit();
            return process.ExitCode;
        } catch (Exception error) {
            MessageBox.Show("Avvio non riuscito: " + error.Message, "Mouse Macro 0.19.1", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
