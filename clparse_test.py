import sys
from enum import Flag, auto

from lib import cl_parse_old as cl

# import functools


# 試験用コマンドライン
args = 'this.py # -ac BLUE|RED|GREEN ABC --size 1024x0X40  --exp -ar 0.5 --date 2021/10/3'.split()
# args = sys.argv


class Color(Flag):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    # PURPLE = RED | GREEN
    WHITE = RED | GREEN | BLUE

# int_literal2 = functools.partial(int, base=0)

# date = functools.partial(
#     lambda strdate: dt.strptime(strdate, '%Y/%m/%d')
# )
# date = cl.Mu(dt.strptime, '%Y/%m/%d')


# dat2: Callable[..., Any] = lambda strdate: dt.strptime(strdate, '%Y/%m/%d')
# date = lambda strdate: dt.strptime(strdate, '%Y/%m/%d')
# tp: Callable[..., Any] = lambda x: list(map(int, x.split('.', 4)))

# cl_parse 呼び出し用のオプション定義
options = [
        ["h", "help", "使い方を表示する", None],
        ["a", "all", "すべて出力"],
        ["d", "date", "対象日//<年/月/日>", cl.date],
        ["c", "color", "表示色//<color>", Color],
        ["s", "size", "表示サイズを指定する//<縦x横>",
            cl.sepalate_items(type=cl.int_literal, sep='x', count=0)],
        ["r", "ratio", "比率を指定する//<比率>", float],
        ["x", "extend", "特別な奴"],
        ["e", "expect", "紛らわしい奴"],
]

# cl_parse 呼び出し（解析実行）
op = cl.Parse(options, args, debug=True)

# 解析エラー時の処理は自前で行う
if op.is_error:
    print(op.get_errormessage(2), file=sys.stderr)
    print("オプション一覧")
    op.show_optionslist()
    exit(1)

# help情報の表示も自前
if op.isEnable("help"):
    print("使い方を表示する。")
    op.show_optionslist()
    exit()

# ここから自分のプログラム
if op.isEnable("all"):
    print("-a, --all : すべて出力、が指定されました。")

if op.isEnable("color"):
    print(f"-c, --color : 表示色、が指定されました。color={op.value('color')}")

if op.isEnable("date"):
    print(f"-d, --date : 対象日、が指定されました。date={op.value('date')}")

if op.isEnable("size"):
    print(f"-s, --size : 表示サイズ、が指定されました。size={op.value('size')}")

if op.isEnable("ratio"):
    print(f"-r, --ratio : 比率を指定する、が指定されました。ratio={op.value('ratio')}")

if op.isEnable("extend"):
    print("-x, --extend : 特別な奴、が指定されました。")

if op.isEnable("expect"):
    print("-e, --expect : 紛らわしい奴、が指定されました。")

# options = [
#         ["h", "help", "使い方を表示する", None],
#         ["l", "list", "一覧出力をする", cl.sepalate_items(int, '.')],
#         ["a", "all", "すべて出力"],
#         ["c", "color", "背景色//<color>", Color],
#         ["x", "extend", "特別な奴", cl.int_literal],
#         ["e", "expect", "紛らわしい奴", int],
#         ["q", "question", ""],
#         ["d", "date", "日付を指定する//<日付>>", cl.date]
        
# ]

# print("set_conditionのテスト")
# print()
# print("解析エラーメッセージ、上書きテスト")
# print(cl.emsg["E22"])
# cl.emsg["E22"] = "{eno}: 引数 {arg} の中のオプション {opt} のオプション引数が間違っています。"
# print(cl.emsg["E22"])

# print()
# # print("解析エラーメッセージ一覧")
# # ops.OptParse.show_errormessage()
# # ops.set_condition(errorlevel=2)

# op = cl.Parse(options, args)

# print()
# print("オプション設定一覧")
# op.show_optionslist(16, 4)

# if op.is_error:
#     print(op.get_errormessage(2), file=sys.stderr)
#     exit(1)

# print()
# print("オプション解析結果一覧")
# op.show_result()

# print()
# print("コマンド引数一覧")
# for i, param in enumerate(op.params):
#     print(f"{i}: {param}")
