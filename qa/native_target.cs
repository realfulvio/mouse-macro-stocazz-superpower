// Dedicated acceptance targets. No input injection, child processes or networking.
using System;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;

class NativeTarget : Form {
    [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr context);
    int a, b, doubles, down, up, wheel, drags;
    Label counters;
    Panel dragArea, block, wheelArea;
    bool held;
    int startX, initialX;
    readonly string output = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "native-counts.local.json");
    NativeTarget() {
        Text = "Banco nativo Mouse Macro — bersagli locali";
        StartPosition = FormStartPosition.Manual; Location = new Point(40,40);
        ClientSize = new Size(550,620); AutoScaleMode = AutoScaleMode.None;
        Font = new Font("Segoe UI",14); BackColor = Color.FromArgb(242,235,249);
        var title = new Label { Text="Prova locale: nessun servizio esterno", Location=new Point(20,15), Size=new Size(510,40) };
        Controls.Add(title);
        var left = new Button { Text="Bersaglio A", Location=new Point(20,70), Size=new Size(230,70) };
        var right = new Button { Text="Bersaglio B", Location=new Point(280,70), Size=new Size(230,70) };
        left.Click += (s,e)=> { a++; Save(); }; right.Click += (s,e)=> { b++; Save(); };
        Controls.Add(left); Controls.Add(right);
        var doubleArea = new Label { Text="Doppio clic qui", TextAlign=ContentAlignment.MiddleCenter,
            Location=new Point(20,165), Size=new Size(490,70), BackColor=Color.LightGreen };
        doubleArea.DoubleClick += (s,e)=> { doubles++; Save(); }; Controls.Add(doubleArea);
        dragArea = new Panel { Location=new Point(20,260), Size=new Size(490,80), BackColor=Color.LightGray };
        block = new Panel { Location=new Point(5,10), Size=new Size(60,60), BackColor=Color.MediumPurple };
        block.MouseDown += (s,e)=> { if(e.Button != MouseButtons.Left) return;
            held=true; down++; startX=block.PointToScreen(e.Location).X; initialX=block.Left; block.Capture=true; Save(); };
        block.MouseMove += (s,e)=> { if(held) block.Left=Math.Max(5,Math.Min(425,initialX+block.PointToScreen(e.Location).X-startX)); };
        block.MouseUp += (s,e)=> { if(!held) return; held=false; up++; block.Capture=false;
            if(block.Left>=300) drags++; block.Left=5; Save(); };
        dragArea.Controls.Add(block); Controls.Add(dragArea);
        wheelArea = new Panel { Location=new Point(20,365), Size=new Size(490,80), BackColor=Color.White, TabStop=true };
        wheelArea.Controls.Add(new Label { Text="Rotella qui", Location=new Point(10,10), Size=new Size(300,40) });
        wheelArea.MouseEnter += (s,e)=> wheelArea.Focus();
        wheelArea.MouseWheel += (s,e)=> { wheel += e.Delta/120; Save(); }; Controls.Add(wheelArea);
        counters = new Label { Location=new Point(20,465), Size=new Size(510,70) }; Controls.Add(counters);
        var reset = new Button { Text="Azzera contatori", Location=new Point(20,545), Size=new Size(245,55) };
        reset.Click += (s,e)=> { a=b=doubles=down=up=wheel=drags=0; held=false; block.Left=5; Save(); }; Controls.Add(reset);
        var mouseState = new Timer { Interval=100 };
        mouseState.Tick += (s,e)=> { if(!held) Save(); }; mouseState.Start();
        FormClosed += (s,e)=> mouseState.Dispose(); Save();
    }
    void Save() {
        string text = "{\"a\":"+a+",\"b\":"+b+",\"double\":"+doubles+",\"down\":"+down+
            ",\"up\":"+up+",\"wheel\":"+wheel+",\"drag\":"+drags+
            ",\"held\":"+(held?"true":"false")+",\"mouseButtons\":"+(int)Control.MouseButtons+"}";
        counters.Text = "A: "+a+"   B: "+b+"   Doppio: "+doubles+"\nDrag: "+drags+"   Rotella: "+wheel+"   Pressioni/rilasci: "+down+"/"+up;
        File.WriteAllText(output,text);
    }
    [STAThread] static void Main() {
        SetProcessDpiAwarenessContext(new IntPtr(-4));
        Application.EnableVisualStyles(); Application.Run(new NativeTarget());
    }
}
