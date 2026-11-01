// Explicit portable startup: original PSF interpreter name, no sitecustomize.
// Double-clicked from the extracted ZIP it first offers a per-user install
// (no administrator rights): the package goes under
// %LOCALAPPDATA%\MouseMacroStocazzSuperpower\Portable, next to the versions the
// in-app updater downloads, and a fixed copy of this launcher, which always
// starts the newest installed version, gets the Start menu and Desktop shortcuts.
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Microsoft.Win32;
[assembly: AssemblyTitle("Mouse Macro Stocazz Superpower")]
[assembly: AssemblyCompany("hcok")]
[assembly: AssemblyVersion("1.2.1.0")]
[assembly: AssemblyFileVersion("1.2.1.0")]
class Launcher {
    const string Version = "1.2.1";
    const string Name = "Mouse Macro Stocazz Superpower";
    const string Prefix = "MouseMacroStocazzSuperpower-Windows-v";
    const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\MouseMacroStocazzSuperpower";
    static readonly string Title = "Mouse Macro " + Version;
    static readonly string Home = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MouseMacroStocazzSuperpower");
    static readonly string Packages = Path.Combine(Home, "Portable");
    static readonly string Installed = Path.Combine(Home, Name + ".exe");

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool DeleteFileW(string path);

    [STAThread] static int Main(string[] args) {
        try {
            if (Array.IndexOf(args, "--uninstall") >= 0) return Uninstall();
            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
            bool package = IsPackage(root);
            if (package && !Inside(root, Home)) {
                string newest = Newest();
                if (newest != null && FolderVersion(newest) >= new Version(Version)) {
                    Integrate(FolderVersion(newest).ToString());  // shortcuts deleted by hand come back
                    return Start(newest);
                }
                DialogResult answer = MessageBox.Show(
                    "Installare " + Name + " " + Version + " sul computer?\n\n" +
                    "Sì: lo copia nella tua cartella utente (senza permessi da amministratore) e crea i collegamenti " +
                    "nel menu Start e sul desktop. Gli aggiornamenti si installano poi dal programma.\n" +
                    "No: lo avvia da questa cartella senza installare niente.",
                    Title, MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question);
                if (answer == DialogResult.Cancel) return 0;
                if (answer == DialogResult.No) return Start(root);
                return Start(Install(root));
            }
            string target = Newest() ?? (package ? root : null);
            if (target == null) {
                MessageBox.Show("Non trovo il programma installato in " + Packages + ".\nScarica di nuovo lo ZIP e apri il file .exe.",
                                Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
            if (Registry.CurrentUser.OpenSubKey(UninstallKey) != null) Register(FolderVersion(target).ToString());
            return Start(target);
        } catch (Exception error) {
            MessageBox.Show("Avvio non riuscito: " + error.Message, Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    static bool IsPackage(string folder) {
        return File.Exists(Path.Combine(folder, @"runtime\pythonw.exe")) && File.Exists(Path.Combine(folder, @"app\windows_main.py"));
    }

    static bool Inside(string folder, string parent) {
        return (Path.GetFullPath(folder).TrimEnd('\\') + "\\").StartsWith(Path.GetFullPath(parent).TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase);
    }

    static Version FolderVersion(string folder) {
        try { return new Version(Path.GetFileName(folder.TrimEnd('\\')).Substring(Prefix.Length)); }
        catch (Exception) { return new Version(0, 0); }
    }

    // Newest complete package under Portable\, including the ones the updater added.
    static string Newest() {
        if (!Directory.Exists(Packages)) return null;
        string best = null;
        foreach (string folder in Directory.GetDirectories(Packages, Prefix + "*")) {
            if (IsPackage(folder) && (best == null || FolderVersion(folder) > FolderVersion(best))) best = folder;
        }
        return best;
    }

    static int Start(string folder) {
        if (!IsPackage(folder)) {
            MessageBox.Show("Estrai tutto lo ZIP e mantieni insieme tutti i file.", Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        ProcessStartInfo start = new ProcessStartInfo(Path.Combine(folder, @"runtime\pythonw.exe"),
                                                      "-B \"" + Path.Combine(folder, @"app\windows_main.py") + "\"");
        start.WorkingDirectory = folder;
        start.UseShellExecute = false;
        start.CreateNoWindow = true;
        Process.Start(start);  // no wait: the installed launcher must stay replaceable while the panel is open
        return 0;
    }

    static string Install(string source) {
        string target = Path.Combine(Packages, Prefix + Version);
        string staging = target + ".installing";
        if (Directory.Exists(staging)) Directory.Delete(staging, true);
        Copy(source, staging);
        if (Directory.Exists(target)) Directory.Delete(target, true);
        Directory.Move(staging, target);
        Integrate(Version);
        return target;
    }

    static void Copy(string source, string target) {
        Directory.CreateDirectory(target);
        foreach (string file in Directory.GetFiles(source)) {
            string copy = Path.Combine(target, Path.GetFileName(file));
            File.Copy(file, copy, true);
            // Installed copies, like any installer's files, do not keep the ZIP's download mark.
            DeleteFileW(copy + ":Zone.Identifier");
        }
        foreach (string folder in Directory.GetDirectories(source)) Copy(folder, Path.Combine(target, Path.GetFileName(folder)));
    }

    // Fixed launcher + shortcuts + "Installed apps" entry; refreshed at every install.
    static void Integrate(string version) {
        Directory.CreateDirectory(Home);
        string self = Assembly.GetExecutingAssembly().Location;
        if (!string.Equals(Path.GetFullPath(self), Path.GetFullPath(Installed), StringComparison.OrdinalIgnoreCase)) {
            File.Copy(self, Installed, true);
            DeleteFileW(Installed + ":Zone.Identifier");
        }
        foreach (string link in Links()) Shortcut(link);
        Register(version);
    }

    static string[] Links() {
        return new string[] {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), Name + ".lnk"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), Name + ".lnk")
        };
    }

    static void Shortcut(string path) {
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        object shell = Activator.CreateInstance(shellType);
        try {
            object link = shellType.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { path });
            Type linkType = link.GetType();
            linkType.InvokeMember("TargetPath", BindingFlags.SetProperty, null, link, new object[] { Installed });
            linkType.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, link, new object[] { Home });
            linkType.InvokeMember("IconLocation", BindingFlags.SetProperty, null, link, new object[] { Installed + ",0" });
            linkType.InvokeMember("Description", BindingFlags.SetProperty, null, link, new object[] { "Registra e riproduce i gesti del mouse" });
            linkType.InvokeMember("Save", BindingFlags.InvokeMethod, null, link, null);
            Marshal.ReleaseComObject(link);
        } finally {
            Marshal.ReleaseComObject(shell);
        }
    }

    static void Register(string version) {
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(UninstallKey)) {
            key.SetValue("DisplayName", Name);
            key.SetValue("DisplayVersion", version);
            key.SetValue("Publisher", "hcok");
            key.SetValue("DisplayIcon", Installed + ",0");
            key.SetValue("InstallLocation", Home);
            key.SetValue("UninstallString", "\"" + Installed + "\" --uninstall");
            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
            key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
        }
    }

    // Removes program, shortcuts and entry; settings and saved macros stay in place.
    static int Uninstall() {
        if (MessageBox.Show("Disinstallare " + Name + "?\n\nChiudi prima il pannello se è aperto. " +
                            "Le impostazioni e le macro salvate restano.", "Mouse Macro",
                            MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return 0;
        foreach (string link in Links()) if (File.Exists(link)) File.Delete(link);
        Registry.CurrentUser.DeleteSubKeyTree(UninstallKey, false);
        try {
            if (Directory.Exists(Packages)) Directory.Delete(Packages, true);
        } catch (Exception error) {
            MessageBox.Show("Alcuni file sono ancora in uso (il pannello è aperto?): " + error.Message + "\n" + Packages,
                            "Mouse Macro", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        MessageBox.Show(Name + " è stato disinstallato.", "Mouse Macro", MessageBoxButtons.OK, MessageBoxIcon.Information);
        // A running exe cannot delete itself: cmd removes it once this process has exited
        // (started last, after the message box, and retried for a few seconds).
        ProcessStartInfo later = new ProcessStartInfo("cmd.exe", "/c for /l %i in (1,1,10) do (ping -n 2 127.0.0.1 >nul & del /f /q \"" +
                                                      Installed + "\" 2>nul & if not exist \"" + Installed + "\" exit /b 0)");
        later.CreateNoWindow = true;
        later.UseShellExecute = false;
        Process.Start(later);
        return 0;
    }
}
