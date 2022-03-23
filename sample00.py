import sys
from lib import cl_parse as cl
from lib import cl_parse_functions as cf
from enum import Enum, EnumMeta, Flag, IntFlag, auto


class Color(Flag):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    PURPLE = RED | GREEN
    WHITE = RED | GREEN | BLUE


args = sys.argv
if len(args) <= 1:
    args = 'this.py ---#  ABC --ratio --all --size=200x300 --date=2022/1/31 --color=RED|GREEN '.split()

# cl_parse 呼び出し用のオプション定義
options = (
        ("#USAGE: なんてものを書いてみる\n "),
        ("all", "-a, --all", "すべて出力", ("COUNT")),
        ("help", "-h, -? ,  --help", "使い方を表示する", None),
        # ["date", "-d, --date", "対象日//<年/月/日>", (date, str_choices(["TODAY", "TOMORROW"]))],
        ("# "),
        # ("date", "-d, --date", "対象日//<年/月/日>", cf.date),
        ("date", "-d, --date", None, cf.date),
        ("color", "-c, --color, -l", "表示色//<color>", Color),
        ("#     これは、いろいろなコメントです。\n   なんでしょうかね。",),
        ("size", " --size, --display", "表示サイズを指定する//<縦x横>",
            cf.sepalate_items(type=cf.int_literal, sep='x', count=2)),
        ("OPT_ratio", "-r,--ratio", "比率を指定する//<比率>", ["OPTIONAL", int, float, str, "APPEND"]),
        ("extend", "-x, --extend ", "特別な奴", "OPTIONAL"),
        ("expect", "-e, --expect", "紛らわしい奴"),
)

exclusive = [
    ("all", "expect"),
    ("extend", "date"),
]

newemsg = {
    "E31": ": オプション ({ext0}) と ({ext1}) は同時に指定できません。",
}

cl.emsg.update(newemsg)
cl.Parse.show_errormessage()

# cl_parse 呼び出し（解析実行）
ps = cl.Parse(args, options, exclusive=exclusive, cancelable=True, debug=True, emessage_header="@stem")
# op = Parse(options, args, exclusive=exclusive, cancelable=True, debug=True)

# 解析エラー時の処理は自前で行う
if ps.is_error:
    # print(op.get_errormessage(1), file=sys.stderr)
    print(ps.get_errormessage(), file=sys.stderr)
    print()
    print("オプション一覧", file=sys.stderr)
    cl.tabprint(ps.get_optionlist(), [22, 4], file=sys.stderr)
    exit(1)

# help情報の表示も自前
if ps.OPT_help.isEnable:
    print("使い方を表示する。")
    tabprint(ps.get_optionlist(), [22, 4])

    exit()

# ここから自分のプログラム
if ps.OPT_all.isEnable:
    print("-a, --all : すべて出力、が指定されました。")

if ps.OPT_["color"].isEnable:
    print('OPT_["color"] is Enable,', f'value = {ps.OPT_["color"].value}')

if ps.OPT_size.isEnable:     # type: ignore
    print(f"-s, --size : 表示サイズ、が指定されました。size={repr(ps.OPT_size.value)}")     # type: ignore

if ps.OPT_ratio.isEnable:
    print(f"-r, --ratio : 比率を指定する、が指定されました。ratio={repr(ps.OPT_ratio.value)}")
    print(type(ps.OPT_ratio.value))

if ps.OPT_extend.isEnable:
    print("-x, --extend : 特別な奴、が指定されました。")

if ps.OPT_expect.isEnable:
    print("-e, --expect : 紛らわしい奴、が指定されました。")
