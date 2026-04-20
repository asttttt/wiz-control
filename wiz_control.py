import customtkinter as ctk
import tkinter as tk
import colorsys, socket, json, threading, os
import pathlib, json as _json, sys
from PIL import Image, ImageDraw

def _app_data_dir() -> pathlib.Path:
    if sys.platform == "win32":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home()))
    else:
        base = pathlib.Path.home() / ".config"
    d = base / "WizControl"
    d.mkdir(parents=True, exist_ok=True)
    return d

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

DARK    = "#1f1f1e"
CARD    = "#2c2c2a"
ENTRY   = "#121212"
BORDER  = "#3a3a38"
FG      = "#ececea"
FG_DIM  = "#777771"
ACCENT  = "#787873"
ACCENT2 = "#22C55E"
BULB_PORT = 38899

app = ctk.CTk()
app.title("WiZ Control")
app.geometry("420x540")
app.resizable(False, False)
app.configure(fg_color=DARK)

status_var    = tk.StringVar(value="Ready")
cct_var       = tk.IntVar(value=4000)
color_bri_var = tk.IntVar(value=100)
cct_bri_var   = tk.IntVar(value=100)
flux_bri_var  = tk.IntVar(value=100)
hue_deg       = [0.0]
_dbc = [None]
_dbw = [None]

bulbs            = []
_feature_targets = {}
_status_pair     = [None]
_bulb_rows_wrap  = [None]

# ── Tooltip ────────────────────────────────────────────────────────────
class _Tooltip:
    def __init__(self, widget, text):
        self._tip = None
        self._text = text
        widget.bind("<Enter>",  self._show, add="+")
        widget.bind("<Leave>",  self._hide, add="+")
        widget.bind("<Motion>", self._move, add="+")

    def _show(self, e):
        if self._tip: return
        self._tip = tk.Toplevel()
        self._tip.overrideredirect(True)
        self._tip.attributes("-topmost", True)
        self._tip.configure(bg=BORDER)
        outer = tk.Frame(self._tip, bg=ENTRY, padx=1, pady=1)
        outer.pack()
        tk.Label(outer, text=self._text, bg=ENTRY, fg=FG,
                 font=("Segoe UI", 8), justify="left",
                 padx=10, pady=7).pack()
        self._move(e)

    def _move(self, e):
        if self._tip:
            self._tip.geometry(f"+{e.x_root+14}+{e.y_root+14}")

    def _hide(self, _e):
        if self._tip:
            self._tip.destroy()
            self._tip = None

def _tip(widget, text): _Tooltip(widget, text)

# ── Bulb helpers ───────────────────────────────────────────────────────
def _bulb_name(i):   return f"B{i+1}"
def _bulb_accent(i): return ACCENT2 if i % 2 == 0 else ACCENT
def _bulb_ip(b):     return b["ip_var"].get().strip()

def _default_bulb_ip():
    for b in bulbs:
        ip = _bulb_ip(b)
        if ip: return ip
    return ""

def _set_bulb_indicator(index, state=None):
    if index >= len(bulbs): return
    b = bulbs[index]
    b["on"][0] = bool(state) if state in (True, False) else False
    dot = b.get("status_dot"); lbl = b.get("status_lbl"); btn = b.get("power_btn")
    if state is True:
        dc,txt,tc="#2ecc71","ON","#2ecc71";   bc,bh,bt,bl="#1e5c38","#256b42","#a0e8b8","Pwr  ON"
    elif state is False:
        dc,txt,tc="#e74c3c","OFF","#e74c3c";  bc,bh,bt,bl="#5c1e1e","#6e2424","#e8a0a0","Pwr  OFF"
    else:
        dc,txt,tc=FG_DIM,"–",FG_DIM;         bc,bh,bt,bl="#5c1e1e","#6e2424","#e8a0a0","Pwr  OFF"
    if dot: dot.configure(fg_color=dc)
    if lbl: lbl.configure(text=txt, text_color=tc)
    if btn: btn.configure(text=bl, fg_color=bc, hover_color=bh, text_color=bt)

# ── Target picker ──────────────────────────────────────────────────────
def _set_all_targets(k, v):
    for var in _feature_targets.get(k,{}).get("vars",[]): var.set(v)
    _update_target_summary(k)

def _selected_bulbs(k):
    tv = _feature_targets.get(k,{}).get("vars",[])
    return [(i,b,_bulb_ip(b)) for i,b in enumerate(bulbs)
            if i<len(tv) and tv[i].get() and _bulb_ip(b)]

def _target_summary(k):
    v=_feature_targets.get(k,{}).get("vars",[])
    s=[_bulb_name(i) for i,x in enumerate(v) if x.get()]
    if not v: return "No bulbs"
    if len(s)==len(v): return "All bulbs"
    if not s: return "Select bulbs"
    return ", ".join(s) if len(s)<=2 else f"{len(s)} bulbs"

def _update_target_summary(k):
    g=_feature_targets.get(k)
    if g: g["summary_var"].set(_target_summary(k))

def _close_target_menu(k):
    g=_feature_targets.get(k)
    if not g or not g.get("popup"): return
    try: g["popup"].destroy()
    except: pass
    g["popup"]=None

def _rebuild_target_menu(k):
    g=_feature_targets.get(k)
    if not g or not g.get("popup"): return
    popup=g["popup"]
    for c in popup.winfo_children(): c.destroy()
    top=ctk.CTkFrame(popup, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
    top.pack(fill="both", expand=True, padx=1, pady=1)
    act=ctk.CTkFrame(top, fg_color="transparent")
    act.pack(fill="x", padx=8, pady=(8,6))
    ctk.CTkButton(act,text="All",width=44,height=24,corner_radius=6,
                  fg_color=ENTRY,hover_color=BORDER,text_color=FG,
                  border_width=1,border_color=BORDER,font=("Segoe UI",9,"bold"),
                  command=lambda:_set_all_targets(k,True)).pack(side="left")
    ctk.CTkButton(act,text="Clear",width=52,height=24,corner_radius=6,
                  fg_color=ENTRY,hover_color=BORDER,text_color=FG_DIM,
                  border_width=1,border_color=BORDER,font=("Segoe UI",9),
                  command=lambda:_set_all_targets(k,False)).pack(side="left",padx=(4,0))
    for idx,var in enumerate(g["vars"]):
        r=ctk.CTkFrame(top,fg_color="transparent")
        r.pack(fill="x",padx=8,pady=2)
        ctk.CTkCheckBox(r,text=_bulb_name(idx),variable=var,
                        onvalue=True,offvalue=False,corner_radius=5,
                        fg_color=ACCENT,hover_color=BORDER,text_color=FG,
                        font=("Segoe UI",9),
                        command=lambda:_update_target_summary(k)).pack(anchor="w")
    popup.update_idletasks()

def _toggle_target_menu(k, anchor):
    g=_feature_targets.get(k)
    if not g: return
    if g.get("popup") and g["popup"].winfo_exists():
        _close_target_menu(k); return
    popup=ctk.CTkToplevel(app)
    popup.overrideredirect(True)
    popup.attributes("-topmost",True)
    popup.configure(fg_color=CARD)
    g["popup"]=popup
    _rebuild_target_menu(k)
    x=anchor.winfo_rootx(); y=anchor.winfo_rooty()+anchor.winfo_height()+4
    popup.geometry(f"170x{min(240,58+max(1,len(g['vars']))*32)}+{x}+{y}")
    popup.bind("<FocusOut>", lambda _e:_close_target_menu(k))
    popup.focus_force()

def _append_target_option(k, index):
    g=_feature_targets.get(k)
    if not g: return
    g["vars"].append(tk.BooleanVar(value=True))
    _update_target_summary(k); _rebuild_target_menu(k)

def _remove_last_target_option(k):
    g=_feature_targets.get(k)
    if not g or not g["vars"]: return
    g["vars"].pop(); _update_target_summary(k); _rebuild_target_menu(k)

# ── Bulb rows ──────────────────────────────────────────────────────────
def _on_bulb_ip_change(index,*_):
    _set_bulb_indicator(index,None); _save_slots_to_disk()

def _add_bulb(ip="", save=True):
    index=len(bulbs)
    b={"ip_var":tk.StringVar(value=ip),"on":[False],
       "status_dot":None,"status_lbl":None,"power_btn":None,
       "status_frame":None,"row_frame":None}
    b["ip_var"].trace_add("write", lambda *_a,i=index:_on_bulb_ip_change(i))
    bulbs.append(b)
    if _status_pair[0] is not None:
        stat=ctk.CTkFrame(_status_pair[0],fg_color="transparent")
        stat.pack(side="left",padx=(0,8))
        b["status_frame"]=stat
        ctk.CTkLabel(stat,text=_bulb_name(index),text_color=_bulb_accent(index),
                     font=("Segoe UI",8,"bold")).pack(side="left",padx=(0,3))
        b["status_dot"]=ctk.CTkLabel(stat,text="",width=7,height=7,
                                      corner_radius=0,fg_color=FG_DIM)
        b["status_dot"].pack(side="left",padx=(0,2))
        b["status_lbl"]=ctk.CTkLabel(stat,text="–",text_color=FG_DIM,
                                      font=("Segoe UI",8,"bold"),width=24)
        b["status_lbl"].pack(side="left")
    if _bulb_rows_wrap[0] is not None:
        row=ctk.CTkFrame(_bulb_rows_wrap[0],fg_color="transparent")
        row.pack(fill="x",pady=(0,2))
        b["row_frame"]=row
        ctk.CTkLabel(row,text=_bulb_name(index),text_color=_bulb_accent(index),
                     font=("Segoe UI",10,"bold"),width=26).pack(side="left")
        ctk.CTkEntry(row,textvariable=b["ip_var"],placeholder_text="IP",
                     fg_color=ENTRY,border_color=BORDER,border_width=1,text_color=FG,
                     font=("Consolas",9),corner_radius=8,
                     height=26).pack(side="left",fill="x",expand=True,padx=(5,5))
        pb=ctk.CTkButton(row,text="Pwr OFF",width=72,height=26,corner_radius=7,
                         fg_color="#5c1e1e",hover_color="#6e2424",
                         text_color="#e8a0a0",font=("Segoe UI",8,"bold"),
                         command=lambda i=index:_toggle_power(i))
        pb.pack(side="right"); b["power_btn"]=pb
    _set_bulb_indicator(index,None)
    for fk in list(_feature_targets): _append_target_option(fk,index)
    if save: _save_slots_to_disk()
    return b

def _add_bulb_from_ui():
    if len(bulbs) >= 5:
        status_var.set("Max 5 bulbs"); return
    _add_bulb(); status_var.set("Bulb added")

def _remove_last_bulb():
    if not bulbs: status_var.set("No bulbs to remove"); return
    b=bulbs.pop()
    if b.get("row_frame"):    b["row_frame"].destroy()
    if b.get("status_frame"): b["status_frame"].destroy()
    for fk in list(_feature_targets): _remove_last_target_option(fk)
    _save_slots_to_disk(); status_var.set("Bulb removed")

# ── UDP ────────────────────────────────────────────────────────────────
def _valid_ip(ip):
    """Return True only for bare IPv4 addresses (no host names, no shell chars)."""
    import re
    ip = ip.strip()
    if not ip: return False
    if not re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip): return False
    try:
        socket.inet_aton(ip)   # validates each octet is 0-255
        return True
    except OSError:
        return False

def _udp_raw(ip, payload, timeout=0):
    try:
        ip = ip.strip()
        if not _valid_ip(ip): return False
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        if timeout: s.settimeout(timeout)
        s.sendto(json.dumps(payload).encode(),(ip,BULB_PORT))
        if timeout:
            try: s.recvfrom(1024)
            except: pass
        s.close(); return True
    except: return False

def send_udp(payload, ip=None, update_status=True):
    ip=(ip or _default_bulb_ip()).strip()
    if not _valid_ip(ip):
        if update_status: status_var.set("Set a valid bulb IP first")
        return False
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.settimeout(1); s.sendto(json.dumps(payload).encode(),(ip,BULB_PORT))
        try:
            s.recvfrom(1024)
            if update_status: status_var.set("Sent OK")
        except:
            if update_status: status_var.set("Sent")
        s.close(); return True
    except Exception as e:
        if update_status: status_var.set(f"Error: {e}")
        return False

def send_udp_fast(payload, ip=None):
    ip=(ip or _default_bulb_ip()).strip()
    if not _valid_ip(ip): return False
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.sendto(json.dumps(payload).encode(),(ip,BULB_PORT))
        s.close(); return True
    except: return False

def _send_feature_payloads(k, builder, feedback=True):
    sel=_selected_bulbs(k)
    if not sel: status_var.set("Select a bulb with an IP"); return False
    for pos,(idx,_b,ip) in enumerate(sel):
        if feedback and pos==0: send_udp(builder(idx),ip=ip,update_status=True)
        else: send_udp_fast(builder(idx),ip=ip)
    return True

def send_color():
    r,g,b=colorsys.hsv_to_rgb(hue_deg[0]/360.0,1.0,1.0)
    ri,gi,bi=int(r*255),int(g*255),int(b*255)
    dim=int(round(color_bri_var.get()))
    _send_feature_payloads("color",
        lambda i:{"id":1,"method":"setPilot","params":{"r":ri,"g":gi,"b":bi,"dimming":dim}})

def send_white():
    temp=int(round(cct_var.get()/100))*100
    dim=int(round(cct_bri_var.get()))
    _send_feature_payloads("cct",
        lambda i:{"id":1,"method":"setPilot","params":{"temp":temp,"dimming":dim}})

def debounce_color(_):
    if _dbc[0]: app.after_cancel(_dbc[0])
    _dbc[0]=app.after(150,send_color)

def debounce_white(_):
    if _dbw[0]: app.after_cancel(_dbw[0])
    _dbw[0]=app.after(150,send_white)

def _set_bulb_power(index,state):
    if index>=len(bulbs): return
    ip=_bulb_ip(bulbs[index])
    if not ip: status_var.set(f"Set {_bulb_name(index)} IP first"); return
    send_udp_fast({"id":1,"method":"setState","params":{"state":state}},ip=ip)
    _set_bulb_indicator(index,state)
    status_var.set(f"{_bulb_name(index)} {'ON' if state else 'OFF'}")

def _toggle_power(index):
    if index<len(bulbs): _set_bulb_power(index, not bulbs[index]["on"][0])

def _set_all_bulb_power(state):
    sent=0; pl={"id":1,"method":"setState","params":{"state":state}}
    for i,b in enumerate(bulbs):
        ip=_bulb_ip(b)
        if not ip: continue
        _udp_raw(ip,pl,timeout=0); _set_bulb_indicator(i,state); sent+=1
    status_var.set(("All ON" if state else "All OFF") if sent else "Set at least one IP")

def _all_on():  _set_all_bulb_power(True)
def _all_off(): _set_all_bulb_power(False)

def _fetch_one_status(index):
    if index>=len(bulbs): return
    ip=_bulb_ip(bulbs[index])
    if not ip:
        app.after(0, lambda i=index:_set_bulb_indicator(i,None)); return
    state=None
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.settimeout(2)
        s.sendto(json.dumps({"method":"getPilot","params":{}}).encode(),(ip,BULB_PORT))
        data,_=s.recvfrom(1024); s.close()
        state=json.loads(data.decode()).get("result",{}).get("state")
    except: pass
    app.after(0, lambda st=state,i=index:_set_bulb_indicator(i,st))

def get_status():
    status_var.set("Fetching...")
    def _f():
        for i in range(len(bulbs)): _fetch_one_status(i)
        app.after(0, lambda: status_var.set("Ready"))
    threading.Thread(target=_f,daemon=True).start()

def hue_to_hex(deg):
    r,g,b=colorsys.hsv_to_rgb(deg/360.0,1.0,1.0)
    return "#{:02x}{:02x}{:02x}".format(int(r*255),int(g*255),int(b*255))

def kelvin_to_hex(k):
    t=(k-2200)/(6500-2200)
    return "#{:02x}{:02x}{:02x}".format(
        int((1.0+t*(0.7-1.0))*255),
        int((0.6+t*(0.85-0.6))*255),
        int((0.15+t*(1.0-0.15))*255))

# ── Persistence ────────────────────────────────────────────────────────
# IMPORTANT: Bulb IPs are NEVER embedded in the built exe.
# They are stored in %APPDATA%\WizControl\wiz_slots.json at runtime only.
# PyInstaller bundles source code, not user data — your IPs stay private.
_SLOTS_FILE=_app_data_dir()/"wiz_slots.json"

def _load_slots_from_disk():
    try:
        data=_json.loads(_SLOTS_FILE.read_text())
        c=(data.get("color") or [None]*5)[:5]; c+=[None]*(5-len(c))
        w=(data.get("cct")   or [None]*5)[:5]; w+=[None]*(5-len(w))
        ips=[str(x) for x in (data.get("bulbs") or [""])] or [""]
        return c,w,ips
    except: return [None]*5,[None]*5,[""]

def _save_slots_to_disk():
    try:
        _SLOTS_FILE.write_text(_json.dumps({
            "color":color_slots,"cct":cct_slots,
            "bulbs":[_bulb_ip(b) for b in bulbs]},indent=2))
    except: pass

_cdisk,_wdisk,_ipdisk=_load_slots_from_disk()

def _do_reset():
    global color_slots,cct_slots
    try: _SLOTS_FILE.unlink(missing_ok=True)
    except: pass
    for i in range(len(color_slots)): color_slots[i]=None; _render_color_slot(i)
    for i in range(len(cct_slots)):   cct_slots[i]=None;   _render_cct_slot(i)
    while len(bulbs)>1: _remove_last_bulb()
    if bulbs: bulbs[0]["ip_var"].set("")
    status_var.set("Reset complete")

# ══════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════════════
def _card(parent, title=None, pady=(0,6)):
    f=ctk.CTkFrame(parent,fg_color=CARD,corner_radius=12,
                   border_width=1,border_color=BORDER)
    f.pack(fill="x",padx=12,pady=pady)
    body=ctk.CTkFrame(f,fg_color="transparent")
    body.pack(fill="both",expand=True,padx=10,pady=(8,8))
    if title:
        ctk.CTkLabel(body,text=title,text_color=FG_DIM,
                     font=("Segoe UI",8,"bold")).pack(anchor="w",pady=(0,6))
    return body

def _slider_row(parent, label, var, from_, to, steps, cmd=None, a2=False):
    row=ctk.CTkFrame(parent,fg_color="transparent")
    row.pack(fill="x",pady=(0,4))
    ctk.CTkLabel(row,text=label,text_color=FG_DIM,
                 font=("Segoe UI",9),width=76,anchor="w").pack(side="left")
    bc=ACCENT2 if a2 else ACCENT
    ctk.CTkSlider(row,from_=from_,to=to,number_of_steps=steps,
                  variable=var,command=cmd,
                  button_color=bc,button_hover_color=ACCENT,
                  progress_color=bc,fg_color=ENTRY,height=13
                  ).pack(side="left",fill="x",expand=True,padx=(6,6))
    vl=ctk.CTkLabel(row,text="",text_color=FG,font=("Consolas",9),
                    width=40,fg_color=ENTRY,corner_radius=6)
    vl.pack(side="left")
    def _u(*_): vl.configure(text=f"{int(var.get())}%")
    var.trace_add("write",_u); _u()
    return row

def _action_btn(parent, text, cmd):
    b=ctk.CTkButton(parent,text=text,height=32,corner_radius=8,
                    fg_color=ACCENT,hover_color=BORDER,
                    text_color=FG,font=("Segoe UI",10,"bold"),command=cmd)
    b.pack(fill="x",padx=12,pady=(2,4))
    return b

def _bri_target_card(parent, feature_key, bri_var, bri_cmd):
    body=_card(parent,pady=(0,6))
    trow=ctk.CTkFrame(body,fg_color="transparent")
    trow.pack(fill="x",pady=(0,6))
    ctk.CTkLabel(trow,text="Send to",text_color=FG_DIM,
                 font=("Segoe UI",9),width=60,anchor="w").pack(side="left")
    sv=tk.StringVar(value="Select bulbs")
    btn=ctk.CTkButton(trow,textvariable=sv,height=28,corner_radius=8,
                      fg_color=ENTRY,hover_color=CARD,text_color=FG,
                      border_width=1,border_color=BORDER,anchor="w",
                      font=("Segoe UI",9),
                      command=lambda k=feature_key:_toggle_target_menu(k,btn))
    btn.pack(side="left",fill="x",expand=True)
    _feature_targets[feature_key]={"vars":[],"summary_var":sv,"button":btn,"popup":None}
    for i in range(len(bulbs)): _append_target_option(feature_key,i)
    _update_target_summary(feature_key)
    _slider_row(body,"Brightness",bri_var,1,100,99,cmd=bri_cmd)

# ══════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════
hdr=ctk.CTkFrame(app,fg_color=CARD,corner_radius=14,border_width=1,border_color=BORDER)
hdr.pack(fill="x",padx=12,pady=(8,4))

title_row=ctk.CTkFrame(hdr,fg_color="transparent")
title_row.pack(fill="x",padx=12,pady=(6,3))

# Left: title
ctk.CTkLabel(title_row,text="WiZ Control",text_color=FG,
             font=("Segoe UI",11,"bold")).pack(side="left")

# Right: status chips + always-visible +/- buttons
hr=ctk.CTkFrame(title_row,fg_color="transparent")
hr.pack(side="right")

# + and - always visible, packed first so they never get pushed
ctk.CTkButton(hr,text="+",width=26,height=26,corner_radius=7,
              fg_color=ACCENT,hover_color=BORDER,text_color=FG,
              font=("Segoe UI",12,"bold"),
              command=_add_bulb_from_ui).pack(side="right",padx=(3,0))
ctk.CTkButton(hr,text="-",width=26,height=26,corner_radius=7,
              fg_color="#7F1D1D",hover_color="#991B1B",text_color="white",
              font=("Segoe UI",12,"bold"),
              command=_remove_last_bulb).pack(side="right",padx=(3,0))

_status_pair[0]=ctk.CTkFrame(hr,fg_color="transparent")
_status_pair[0].pack(side="left",padx=(0,6))

_bulb_rows_wrap[0]=ctk.CTkFrame(hdr,fg_color="transparent")
_bulb_rows_wrap[0].pack(fill="x",padx=12,pady=(0,2))
for _ip in _ipdisk: _add_bulb(_ip,save=False)

# Controls row
ctrl_row=ctk.CTkFrame(hdr,fg_color="transparent")
ctrl_row.pack(fill="x",padx=12,pady=(0,6))

ctk.CTkButton(ctrl_row,text="All ON",width=68,height=26,corner_radius=7,
              fg_color="#1e5c38",hover_color="#256b42",text_color="#a0e8b8",
              font=("Segoe UI",8,"bold"),command=_all_on).pack(side="left",padx=(0,3))
ctk.CTkButton(ctrl_row,text="All OFF",width=68,height=26,corner_radius=7,
              fg_color="#5c1e1e",hover_color="#6e2424",text_color="#e8a0a0",
              font=("Segoe UI",8,"bold"),command=_all_off).pack(side="left",padx=(0,6))

# Status button — purple (swapped)
ctk.CTkButton(ctrl_row,text="Status",width=56,height=26,corner_radius=7,
              fg_color="#4A1942",hover_color="#6B2560",text_color="#E879F9",
              font=("Segoe UI",8,"bold"),
              command=get_status).pack(side="left")

# Reset button — muted (swapped)
ctk.CTkButton(ctrl_row,text="Reset",width=52,height=26,corner_radius=7,
              fg_color=ENTRY,hover_color=BORDER,text_color=FG_DIM,
              border_width=1,border_color=BORDER,
              font=("Segoe UI",8),
              command=_do_reset).pack(side="left",padx=(4,0))

ctk.CTkLabel(ctrl_row,textvariable=status_var,text_color=FG_DIM,
             font=("Segoe UI",8),anchor="e").pack(side="right")

# ══════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════
_TAB_LABELS=["Color","CCT","f.lux"]
_active_tab=[0]

def _switch_tab(idx):
    _active_tab[0]=idx; tab_bar.set(_TAB_LABELS[idx])
    for i,f in enumerate(_frames):
        if i==idx: f.pack(fill="both",expand=True)
        else:      f.pack_forget()

tab_bar=ctk.CTkSegmentedButton(app,values=_TAB_LABELS,
                               command=lambda v:_switch_tab(_TAB_LABELS.index(v)),
                               fg_color=CARD,selected_color=ACCENT,
                               selected_hover_color=BORDER,
                               unselected_color=ENTRY,unselected_hover_color=BORDER,
                               text_color=FG,corner_radius=10,
                               font=("Segoe UI",10,"bold"),height=32)
tab_bar.pack(fill="x",padx=12,pady=(0,4))

_wrap=ctk.CTkFrame(app,fg_color=CARD,corner_radius=14,border_width=1,border_color=BORDER)
_wrap.pack(fill="both",expand=True,padx=12,pady=(0,4))
_frames=[]
for _ in _TAB_LABELS:
    sf=ctk.CTkScrollableFrame(_wrap,fg_color="transparent",
                              scrollbar_button_color=ENTRY,
                              scrollbar_button_hover_color=BORDER)
    _frames.append(sf)
ctab,wtab,ftab=_frames
ctab.pack(fill="both",expand=True)
tab_bar.set("Color")

# ══════════════════════════════════════════════════════════════════════
#  COLOR TAB
# ══════════════════════════════════════════════════════════════════════
PICKER_W=318; HUE_H=32

ctk.CTkLabel(ctab,text="HUE",text_color=FG_DIM,
             font=("Segoe UI",8,"bold")).pack(anchor="w",padx=10,pady=(6,1))

hue_canvas=tk.Canvas(ctab,width=PICKER_W,height=HUE_H,bg=CARD,highlightthickness=0)
hue_canvas.pack(padx=10,pady=(0,1))

def draw_hue_bar():
    hue_canvas.delete("hbar"); steps=200; cell=PICKER_W/steps
    for i in range(steps):
        hue_canvas.create_rectangle(i*cell,5,i*cell+cell+1,HUE_H-5,
                                     fill=hue_to_hex(i*360/steps),outline="",tags="hbar")

def draw_hue_cursor():
    hue_canvas.delete("hcur")
    x=max(5,min(PICKER_W-5,(hue_deg[0]/360.0)*PICKER_W))
    hue_canvas.create_polygon(x-5,0,x+5,0,x,7,fill="white",outline="",tags="hcur")
    hue_canvas.create_polygon(x-5,HUE_H,x+5,HUE_H,x,HUE_H-7,fill="white",outline="",tags="hcur")
    hue_canvas.create_line(x,7,x,HUE_H-7,fill="white",width=2,tags="hcur")

deg_var=tk.StringVar(value="0°"); color_hex_var=tk.StringVar(value="#FF0000")

def refresh_hue():
    draw_hue_cursor(); deg_var.set(f"{int(round(hue_deg[0]))}°")
    color_hex_var.set(hue_to_hex(hue_deg[0]).upper())
    swatch_cv.itemconfig(swatch_rect,fill=hue_to_hex(hue_deg[0]))

hue_drag=[False]
def hue_press(e):  hue_drag[0]=True;  _move_hue(e)
def hue_motion(e):
    if hue_drag[0]: _move_hue(e)
def hue_release(e):
    if hue_drag[0]: hue_drag[0]=False; send_color()
def _move_hue(e):
    hue_deg[0]=max(0.0,min(360.0,(e.x/PICKER_W)*360.0)); refresh_hue()

hue_canvas.bind("<ButtonPress-1>",  hue_press)
hue_canvas.bind("<B1-Motion>",      hue_motion)
hue_canvas.bind("<ButtonRelease-1>",hue_release)

irow=ctk.CTkFrame(ctab,fg_color="transparent")
irow.pack(fill="x",padx=10,pady=(1,3))
ctk.CTkLabel(irow,text="0°",text_color=FG_DIM,font=("Segoe UI",8)).pack(side="left")
ctk.CTkLabel(irow,textvariable=deg_var,text_color=FG,
             font=("Segoe UI",9,"bold")).pack(side="left",expand=True)
ctk.CTkLabel(irow,textvariable=color_hex_var,text_color=ACCENT2,
             font=("Consolas",8)).pack(side="left",expand=True)
ctk.CTkLabel(irow,text="360°",text_color=FG_DIM,font=("Segoe UI",8)).pack(side="right")

swatch_cv=tk.Canvas(ctab,width=PICKER_W,height=18,bg=CARD,highlightthickness=0)
swatch_cv.pack(padx=10,pady=(0,5))
swatch_rect=swatch_cv.create_rectangle(0,0,PICKER_W,18,fill="#ff0000",outline="")

_bri_target_card(ctab,"color",color_bri_var,debounce_color)

# Color presets
SLOT_W,SLOT_H=44,26; COLOR_SLOT_COUNT=5
color_slots=[None]*COLOR_SLOT_COUNT
color_slot_cvs=[]; color_slot_rect=[]; color_slot_txt=[]
_color_click_pending=[None]

_PRESET_TIP = (
    "COLOR PRESETS\n"
    "─────────────────────────\n"
    "· Click empty slot  →  saves current hue + brightness\n"
    "· Click saved slot  →  recalls and sends to bulbs\n"
    "· Double-click      →  overwrites a saved slot"
)

def _render_color_slot(i):
    if i>=len(color_slot_cvs): return
    if color_slots[i] is None:
        color_slot_cvs[i].itemconfig(color_slot_rect[i],fill=ENTRY)
        color_slot_cvs[i].itemconfig(color_slot_txt[i],text=str(i+1),fill=FG_DIM)
    else:
        hex_c=hue_to_hex(color_slots[i]["hue"])
        color_slot_cvs[i].itemconfig(color_slot_rect[i],fill=hex_c)
        color_slot_cvs[i].itemconfig(color_slot_txt[i],text="✓",fill="white")

def _do_color_single(i):
    _color_click_pending[0]=None
    if color_slots[i] is None:
        color_slots[i]={"hue":hue_deg[0],"bri":color_bri_var.get()}
        _render_color_slot(i); _save_slots_to_disk()
    else:
        hue_deg[0]=color_slots[i]["hue"]
        if "bri" in color_slots[i]: color_bri_var.set(color_slots[i]["bri"])
        refresh_hue(); send_color()

def _do_color_double(i):
    if _color_click_pending[0]: app.after_cancel(_color_click_pending[0]); _color_click_pending[0]=None
    color_slots[i]={"hue":hue_deg[0],"bri":color_bri_var.get()}
    _render_color_slot(i); _save_slots_to_disk()

def _color_click(i):
    if _color_click_pending[0]: app.after_cancel(_color_click_pending[0])
    _color_click_pending[0]=app.after(220, lambda:_do_color_single(i))

def _make_slot(parent, idx, click_fn, dbl_fn):
    c=tk.Canvas(parent,width=SLOT_W,height=SLOT_H,bg=CARD,
                highlightthickness=1,highlightbackground=BORDER,cursor="hand2")
    r=c.create_rectangle(0,0,SLOT_W,SLOT_H,fill=ENTRY,outline="")
    t=c.create_text(SLOT_W//2,SLOT_H//2,text=str(idx+1),
                    fill=FG_DIM,font=("Segoe UI",7,"bold"),anchor="center")
    c.bind("<Button-1>",        lambda e,i=idx:click_fn(i))
    c.bind("<Double-Button-1>", lambda e,i=idx:dbl_fn(i))
    c.bind("<Enter>",  lambda e,cv=c:cv.configure(highlightbackground=ACCENT))
    c.bind("<Leave>",  lambda e,cv=c:cv.configure(highlightbackground=BORDER))
    return c,r,t

# Presets card with tooltip label
csc_frame=ctk.CTkFrame(ctab,fg_color=CARD,corner_radius=12,border_width=1,border_color=BORDER)
csc_frame.pack(fill="x",padx=12,pady=(0,8))
csc_body=ctk.CTkFrame(csc_frame,fg_color="transparent")
csc_body.pack(fill="both",expand=True,padx=10,pady=(8,8))

csc_hdr=ctk.CTkFrame(csc_body,fg_color="transparent")
csc_hdr.pack(fill="x",pady=(0,6))
csc_title=ctk.CTkLabel(csc_hdr,text="COLOR PRESETS",text_color=FG_DIM,
                        font=("Segoe UI",8,"bold"))
csc_title.pack(side="left")
# Small "?" label for tooltip
csc_hint=ctk.CTkLabel(csc_hdr,text="?",text_color=FG_DIM,
                       fg_color=ENTRY,corner_radius=8,
                       width=16,height=16,font=("Segoe UI",7,"bold"),cursor="question_arrow")
csc_hint.pack(side="left",padx=(6,0))
_tip(csc_title, _PRESET_TIP)
_tip(csc_hint,  _PRESET_TIP)

csg=ctk.CTkFrame(csc_body,fg_color="transparent"); csg.pack(fill="x")
for _i in range(COLOR_SLOT_COUNT):
    _cv,_r,_t=_make_slot(csg,_i,_color_click,_do_color_double)
    _cv.grid(row=0,column=_i,padx=3,pady=2)
    color_slot_cvs.append(_cv); color_slot_rect.append(_r); color_slot_txt.append(_t)
    _tip(_cv, _PRESET_TIP)
for _c in range(COLOR_SLOT_COUNT): csg.columnconfigure(_c,weight=1)

# ══════════════════════════════════════════════════════════════════════
#  CCT TAB
# ══════════════════════════════════════════════════════════════════════
ctk.CTkLabel(wtab,text="COLOR TEMPERATURE",text_color=FG_DIM,
             font=("Segoe UI",8,"bold")).pack(anchor="w",padx=10,pady=(6,1))

cct_canvas=tk.Canvas(wtab,width=PICKER_W,height=HUE_H,bg=CARD,highlightthickness=0)
cct_canvas.pack(padx=10,pady=(0,1))

def draw_cct_bar():
    cct_canvas.delete("cct_bar"); steps=100; cell=PICKER_W/steps
    for i in range(steps):
        k=2200+i*(6500-2200)/steps
        cct_canvas.create_rectangle(i*cell,5,i*cell+cell+1,HUE_H-5,
                                     fill=kelvin_to_hex(k),outline="",tags="cct_bar")

def draw_cct_cursor():
    cct_canvas.delete("cct_cur")
    t=(cct_var.get()-2200)/(6500-2200)
    x=max(5,min(PICKER_W-5,t*PICKER_W))
    cct_canvas.create_polygon(x-5,0,x+5,0,x,7,fill="white",outline="",tags="cct_cur")
    cct_canvas.create_polygon(x-5,HUE_H,x+5,HUE_H,x,HUE_H-7,fill="white",outline="",tags="cct_cur")
    cct_canvas.create_line(x,7,x,HUE_H-7,fill="white",width=2,tags="cct_cur")

cct_k_var=tk.StringVar(value="4000 K")
def update_cct_label(): cct_k_var.set(f"{int(round(cct_var.get()/100))*100} K")

cct_drag=[False]
def cct_press(e):  cct_drag[0]=True;  _move_cct(e)
def cct_motion(e):
    if cct_drag[0]: _move_cct(e)
def cct_release(e):
    if cct_drag[0]: cct_drag[0]=False; send_white()
def _move_cct(e):
    t=max(0.0,min(1.0,e.x/PICKER_W))
    cct_var.set(int(round((2200+t*(6500-2200))/100))*100)
    draw_cct_cursor(); update_cct_label()

cct_canvas.bind("<ButtonPress-1>",  cct_press)
cct_canvas.bind("<B1-Motion>",      cct_motion)
cct_canvas.bind("<ButtonRelease-1>",cct_release)

ci=ctk.CTkFrame(wtab,fg_color="transparent")
ci.pack(fill="x",padx=10,pady=(1,3))
ctk.CTkLabel(ci,text="2200K",text_color=FG_DIM,font=("Segoe UI",8)).pack(side="left")
ctk.CTkLabel(ci,textvariable=cct_k_var,text_color=FG,
             font=("Segoe UI",9,"bold")).pack(side="left",expand=True)
ctk.CTkLabel(ci,text="6500K",text_color=FG_DIM,font=("Segoe UI",8)).pack(side="right")

_bri_target_card(wtab,"cct",cct_bri_var,debounce_white)

CCT_SLOT_COUNT=5
cct_slots=[None]*CCT_SLOT_COUNT
cct_slot_cvs=[]; cct_slot_rect=[]; cct_slot_txt=[]
_cct_click_pending=[None]

_CCT_PRESET_TIP = (
    "CCT PRESETS\n"
    "─────────────────────────\n"
    "· Click empty slot  →  saves current temp + brightness\n"
    "· Click saved slot  →  recalls and sends to bulbs\n"
    "· Double-click      →  overwrites a saved slot"
)

def _render_cct_slot(i):
    if i>=len(cct_slot_cvs): return
    if cct_slots[i] is None:
        cct_slot_cvs[i].itemconfig(cct_slot_rect[i],fill=ENTRY)
        cct_slot_cvs[i].itemconfig(cct_slot_txt[i],text=str(i+1),fill=FG_DIM)
    else:
        k=cct_slots[i]["temp"]; hx=kelvin_to_hex(k)
        lbl=f"{int(k//100)*100}K"; tc="#111" if k>4200 else "#fff"
        cct_slot_cvs[i].itemconfig(cct_slot_rect[i],fill=hx)
        cct_slot_cvs[i].itemconfig(cct_slot_txt[i],text=lbl,fill=tc)

def _do_cct_single(i):
    _cct_click_pending[0]=None
    if cct_slots[i] is None:
        cct_slots[i]={"temp":cct_var.get(),"bri":cct_bri_var.get()}
        _render_cct_slot(i); _save_slots_to_disk()
    else:
        cct_var.set(cct_slots[i]["temp"])
        if "bri" in cct_slots[i]: cct_bri_var.set(cct_slots[i]["bri"])
        draw_cct_cursor(); update_cct_label(); send_white()

def _do_cct_double(i):
    if _cct_click_pending[0]: app.after_cancel(_cct_click_pending[0]); _cct_click_pending[0]=None
    cct_slots[i]={"temp":cct_var.get(),"bri":cct_bri_var.get()}
    _render_cct_slot(i); _save_slots_to_disk()

def _cct_click(i):
    if _cct_click_pending[0]: app.after_cancel(_cct_click_pending[0])
    _cct_click_pending[0]=app.after(220, lambda:_do_cct_single(i))

wsc_frame=ctk.CTkFrame(wtab,fg_color=CARD,corner_radius=12,border_width=1,border_color=BORDER)
wsc_frame.pack(fill="x",padx=12,pady=(0,8))
wsc_body=ctk.CTkFrame(wsc_frame,fg_color="transparent")
wsc_body.pack(fill="both",expand=True,padx=10,pady=(8,8))
wsc_hdr=ctk.CTkFrame(wsc_body,fg_color="transparent")
wsc_hdr.pack(fill="x",pady=(0,6))
wsc_title=ctk.CTkLabel(wsc_hdr,text="CCT PRESETS",text_color=FG_DIM,font=("Segoe UI",8,"bold"))
wsc_title.pack(side="left")
wsc_hint=ctk.CTkLabel(wsc_hdr,text="?",text_color=FG_DIM,fg_color=ENTRY,
                       corner_radius=8,width=16,height=16,font=("Segoe UI",7,"bold"),cursor="question_arrow")
wsc_hint.pack(side="left",padx=(6,0))
_tip(wsc_title,_CCT_PRESET_TIP); _tip(wsc_hint,_CCT_PRESET_TIP)

wsg=ctk.CTkFrame(wsc_body,fg_color="transparent"); wsg.pack(fill="x")
for _i in range(CCT_SLOT_COUNT):
    _cv,_r,_t=_make_slot(wsg,_i,_cct_click,_do_cct_double)
    _cv.grid(row=0,column=_i,padx=3,pady=2)
    cct_slot_cvs.append(_cv); cct_slot_rect.append(_r); cct_slot_txt.append(_t)
    _tip(_cv,_CCT_PRESET_TIP)
for _c in range(CCT_SLOT_COUNT): wsg.columnconfigure(_c,weight=1)

# ══════════════════════════════════════════════════════════════════════
#  F.LUX TAB
# ══════════════════════════════════════════════════════════════════════
import http.server
flux_server=[None]; flux_running=[False]
flux_port=tk.IntVar(value=8888); flux_cct_var=tk.StringVar(value="––")
flux_status=tk.StringVar(value="Not running")

_FLUX_TIP = (
    "f.lux BRIDGE\n"
    "─────────────────────────\n"
    "· Open f.lux → Options → \"Extras\"\n"
    "· Enable  \"Post to URL when lighting changes\"\n"
    "· Set URL to:  http://localhost:8888\n"
    "· Press Start here — bulbs then follow f.lux\n"
    "· Set brightness below to control dimming level\n"
    "· Select which bulbs to sync under \"Send to\""
)

def _flux_cct_to_wiz(k): return max(2200,min(6500,int(k)))

class _FluxHandler(http.server.BaseHTTPRequestHandler):
    def _handle(self):
        try:
            import urllib.parse
            parsed=urllib.parse.urlparse(self.path)
            params=urllib.parse.parse_qs(parsed.query)
            length=min(int(self.headers.get("Content-Length",0) or 0), 65536)
            body=self.rfile.read(length)
            k=None
            for key in ("ct","colorTemp","color_temp","kelvin"):
                if key in params: k=int(params[key][0]); break
            if k is None and body and body!=b'\x00':
                try:
                    d=json.loads(body)
                    k=(d.get("colorTemp") or d.get("result",{}).get("colorTemp") or d.get("color",{}).get("ct"))
                except: pass
            if k is None and body and body!=b'\x00':
                try: k=int(body.decode("utf-8",errors="ignore").strip())
                except: pass
            if k:
                wk=_flux_cct_to_wiz(int(k))
                dim=max(1,min(100,int(flux_bri_var.get())))
                for _i,_b,ip in _selected_bulbs("flux"):
                    _udp_raw(ip,{"id":1,"method":"setPilot","params":{"temp":wk,"dimming":dim}},timeout=0)
                app.after(0, lambda t=wk:[flux_cct_var.set(f"{t} K"),
                                          flux_k_swatch.configure(fg_color=kelvin_to_hex(t)),
                                          flux_status.set(f"Last: {t}K")])
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        except Exception as e:
            self.send_response(200); self.end_headers()
            app.after(0, lambda err=e:flux_status.set(f"Error: {err}"))
    def do_POST(self): self._handle()
    def do_GET(self):  self._handle()
    def log_message(self,*a): pass

def _flux_thread():
    import socketserver
    port=flux_port.get()
    try:
        with socketserver.TCPServer(("127.0.0.1",port),_FluxHandler) as srv:
            flux_server[0]=srv
            app.after(0, lambda:flux_status.set(f"Listening :{port}"))
            srv.serve_forever()
    except Exception as e:
        app.after(0, lambda err=e:flux_status.set(f"Error: {err}"))
    finally:
        flux_running[0]=False
        app.after(0, lambda:[flux_status.set("Stopped"),
            flux_btn.configure(text="▶  Start",fg_color=ACCENT,hover_color=BORDER)])

def toggle_flux():
    if flux_running[0]:
        flux_running[0]=False
        if flux_server[0]: flux_server[0].shutdown(); flux_server[0]=None
        flux_btn.configure(text="▶  Start",fg_color=ACCENT,hover_color=BORDER)
        flux_status.set("Stopped")
    else:
        flux_running[0]=True
        flux_btn.configure(text="■  Stop",fg_color="#c0392b",hover_color="#a93226")
        threading.Thread(target=_flux_thread,daemon=True).start()

# Port card
fp=_card(ftab,pady=(6,6))
pr=ctk.CTkFrame(fp,fg_color="transparent")
pr.pack(fill="x",pady=(0,4))
ctk.CTkLabel(pr,text="Port",text_color=FG_DIM,
             font=("Segoe UI",9),width=36).pack(side="left")
ctk.CTkEntry(pr,textvariable=flux_port,width=68,
             fg_color=ENTRY,border_color=BORDER,text_color=FG,
             font=("Consolas",9),corner_radius=7,height=26).pack(side="left",padx=(6,0))
flux_k_swatch=ctk.CTkLabel(pr,text="",fg_color="#333333",
                             corner_radius=6,width=38,height=26)
flux_k_swatch.pack(side="right",padx=(6,0))
ctk.CTkLabel(pr,textvariable=flux_cct_var,text_color=ACCENT2,
             font=("Consolas",8)).pack(side="right")

# Status row with ⓘ button
fsr=ctk.CTkFrame(fp,fg_color="transparent")
fsr.pack(fill="x")
ctk.CTkLabel(fsr,textvariable=flux_status,text_color=FG_DIM,
             font=("Segoe UI",8)).pack(side="left")
flux_info_btn=ctk.CTkLabel(fsr,text="ⓘ",text_color=FG_DIM,
                            fg_color=ENTRY,corner_radius=8,
                            width=18,height=18,font=("Segoe UI",9),cursor="question_arrow")
flux_info_btn.pack(side="left",padx=(6,0))
_tip(flux_info_btn,_FLUX_TIP)

_bri_target_card(ftab,"flux",flux_bri_var,None)
flux_btn=_action_btn(ftab,"▶  Start",toggle_flux)

# ── Status bar ─────────────────────────────────────────────────────────
tk.Frame(app,bg=BORDER,height=1).pack(fill="x")
ctk.CTkLabel(app,textvariable=status_var,text_color=FG_DIM,
             font=("Consolas",8),anchor="w").pack(fill="x",padx=12,pady=(2,3))

# ══════════════════════════════════════════════════════════════════════
#  INIT
# ══════════════════════════════════════════════════════════════════════
draw_hue_bar(); draw_hue_cursor()
draw_cct_bar(); draw_cct_cursor()
for _i in range(COLOR_SLOT_COUNT): color_slots[_i]=_cdisk[_i]; _render_color_slot(_i)
for _i in range(CCT_SLOT_COUNT):   cct_slots[_i]=_wdisk[_i];   _render_cct_slot(_i)

# ══════════════════════════════════════════════════════════════════════
#  TRAY
# ══════════════════════════════════════════════════════════════════════
def _make_tray_img():
    img=Image.new("RGBA",(64,64),(0,0,0,0)); d=ImageDraw.Draw(img)
    d.ellipse([10,6,54,46],fill="#787873")
    d.rectangle([22,46,42,56],fill="#787873")
    d.rectangle([26,56,38,62],fill="#555555")
    return img

_tray_icon=[None]; _tray_started=[False]; _tray_ready=[False]

def _do_quit():
    _save_slots_to_disk()
    if _tray_icon[0]:
        try: _tray_icon[0].stop()
        except: pass
    app.destroy()

def _tray_show(icon=None,item=None):
    app.after(0, lambda:[app.deiconify(),app.lift(),app.focus_force()])

def _tray_quit(icon=None,item=None):
    app.after(0,_do_quit)

def _start_tray():
    try:
        import pystray
        icon=pystray.Icon("WizControl",_make_tray_img(),"WiZ Control",
            pystray.Menu(pystray.MenuItem("Show",_tray_show,default=True),
                         pystray.Menu.SEPARATOR,
                         pystray.MenuItem("Quit",_tray_quit)))
        _tray_icon[0]=icon; _tray_ready[0]=True; icon.run()
    except:
        _tray_ready[0]=False; _tray_started[0]=False
        app.after(0, lambda:[app.deiconify(),app.lift(),app.focus_force()])

def _on_close():
    if _tray_ready[0]: app.withdraw(); return
    if not _tray_started[0]:
        _tray_started[0]=True
        threading.Thread(target=_start_tray,daemon=True).start()
    app.after(250, lambda:app.withdraw() if _tray_ready[0] else None)

app.protocol("WM_DELETE_WINDOW",_on_close)

def _auto_status():
    for i in range(len(bulbs)): _fetch_one_status(i)
    app.after(0, lambda:status_var.set("Ready"))

threading.Thread(target=_auto_status,daemon=True).start()
app.mainloop()
