import ida_kernwin
import ida_segment
import ida_bytes
import ida_idaapi
import idc
import yara
import os

class YaraSettings(ida_kernwin.Form):
    def __init__(self):
        ida_kernwin.Form.__init__(self, r"""BUTTON YES* Search
BUTTON CANCEL Cancel
YaraScan

<##Yara Rules directory:{lPath}>
<Create comments:{lComments}>{lChkGroup}>""", { "lPath":  ida_kernwin.Form.DirInput(), "lChkGroup":  ida_kernwin.Form.ChkGroupControl(("lComments", )) })
        self.Compile()

    def Show(self):
        self.lComments.checked = True
        return self.Execute()

class YaraChoose(ida_kernwin.Choose):
    def __init__(self, title, vals):
        ida_kernwin.Choose.__init__(self, title, [
            ["Address", ida_kernwin.Choose.CHCOL_HEX | 10 ],
            ["Rule Name", ida_kernwin.Choose.CHCOL_PLAIN | 20 ],
            ["Description", ida_kernwin.Choose.CHCOL_PLAIN | 30 ],
            ["Filename", ida_kernwin.Choose.CHCOL_PLAIN | 15 ],
            ["Signature", ida_kernwin.Choose.CHCOL_PLAIN | 30 ],
        ])
        self.vals = vals

    def OnGetSize(self):
        return len(self.vals)

    def OnGetLine(self, n):
        return [ f"0x{hex(self.vals[n][0]).upper()[2:]}", self.vals[n][1], self.vals[n][2], self.vals[n][3], self.vals[n][4]]

    def OnSelectLine(self, sel):
        ida_kernwin.jumpto(self.vals[sel][0])

def GetSections():
    sec, sec_m = ida_segment.get_first_seg(), []
    for i in range(5):
        if sec == None:
            break
        sec_m.append(sec)
        sec = ida_segment.get_next_seg(sec.start_ea)
    return sec_m

def YaraScan(rule_file, comments):
    rule, matches = yara.compile(file = open(rule_file)), []
    for sec in GetSections():
        bytes = ida_bytes.get_bytes(sec.start_ea, sec.end_ea - sec.start_ea)
        for r in rule.match(data = bytes):
            for d in r.strings:
                matches.append([ sec.start_ea + d[0], r.rule, r.meta["description"] if "description" in r.meta else "", rule_file[rule_file.rfind("\\") + 1:], str(d[2])])
                if comments:
                    ida_bytes.set_cmt(sec.start_ea + d[0], r.rule + " / " + (r.meta["description"] if "description" in r.meta else ""), True)
    return matches

class YaraIDA(ida_idaapi.plugin_t):
    comment = ""
    help = ""
    wanted_name = "YaraScan"
    wanted_hotkey = "Shift-Y"
    flags = ida_idaapi.PLUGIN_KEEP

    def init(self):
        return ida_idaapi.PLUGIN_KEEP

    def term(self):
        pass

    def run(self, arg):
        settings = YaraSettings()
        res = settings.Show()
        if res == 1:
            matches = []
            for file in os.listdir(settings.lPath.value):
                if file[-4:] == ".yar":
                    matches_l = YaraScan(settings.lPath.value + "\\" + file, settings.lComments.checked)
                    matches += matches_l
            c = YaraChoose(f"Yara Detections (" + settings.lPath.value[settings.lPath.value.rfind("\\") + 1:] + ")", matches).Show()

def PLUGIN_ENTRY():
    return YaraIDA()