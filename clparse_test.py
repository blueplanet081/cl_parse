import sys
from enum import Flag, auto

from lib import cl_parse as cl
from datetime import datetime as dt

# import functools

# date = cl.Mu(dt.strptime, '%Y/%m/%d')      # 日付 <年>/<月>/<日> 入力


args = sys.argv
if len(args) <= 1:
    # 試験用コマンドライン
    args = 'this.py # ---##e -ac BLUE|RED|GREEN ABC --size 1024x0X40  --exp -ar 0.5 --date 2021/10/30'.split()
    # args = 'this.py # ---# -ac BLUE|RED|GREEN ABC --size 1024x0X40  --exp -ar 0.5 --date '.split()


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
        # ["help", "/h, //help", "使い方を表示する", None],
        # ["all", "/a, //all", "すべて出力"],
        ["help", "-?, --help", "使い方を表示する", None],
        ["all", "-a, --all", "すべて出力"],
        # ["date", "-d, --date", "対象日//<年/月/日>", cl.date],
        ["date", "-d, --date", "対象日//<年/月/日>", cl.date],
        ["color", "-c, --color", "表示色//<color>", Color],
        ["size", "-s, --size", "表示サイズを指定する//<縦x横>",
            cl.sepalate_items(type=cl.int_literal, sep='x', count=0)],
        ["ratio", "-r, --ratio", "比率を指定する//<比率>", float],
        ["xtend", "-x, --extend", "特別な奴"],
        ["expect", "-e, --expect", "紛らわしい奴"],
]

exclusive = ["all", "ratio"]

cl.emsg["E31"] = ": オプション ({ext0}) と ({ext1}) は同時に指定できませんよ。"


# cl_parse 呼び出し（解析実行）
op = cl.Parse(options, args, debug=True, exclusive=exclusive)
# op = cl.Parse(options, args, option_string_prefix="/", debug=True)

# 解析エラー時の処理は自前で行う
# if op.is_error:
#     print(op.get_errormessage(2), file=sys.stderr)
#     print("オプション一覧")
#     op.show_optionslist()
#     exit(1)

# # help情報の表示も自前
# if op.isEnable("help"):
#     print("使い方を表示する。")
#     op.show_optionslist()
#     exit()

# please replace "op" to appropriate instance name.
if op.is_error:
    # op.get_errormessage() 等を表示する
    print(op.get_errormessage(2), file=sys.stderr)
    exit(1)

if op.OPT_["help"].isEnable:   # 使い方を表示する
    print("使用方法を書く")
    # op.get_optionlist() 等を表示する
    cl.tabprint(op.get_optionlist())
    exit()

if op.OPT_["all"].isEnable:    # すべて出力
    pass
# if op.OPT_["date"].isEnable:   # 対象日
#     value = op.OPT_["date"].value
# if op.OPT_["color"].isEnable:  # 表示色
#     value = op.OPT_["color"].value
# if op.OPT_["size"].isEnable:   # 表示サイズを指定する
#     value = op.OPT_["size"].value
# if op.OPT_["ratio"].isEnable:  # 比率を指定する
#     value = op.OPT_["ratio"].value
# if op.OPT_["xtend"].isEnable:  # 特別な奴
#     pass
# if op.OPT_["expect"].isEnable: # 紛らわしい奴
#     pass


# # ここから自分のプログラム
# if op.isEnable("all"):
#     print("-a, --all : すべて出力、が指定されました。")

# if op.isEnable("color"):
#     print(f"-c, --color : 表示色、が指定されました。color={op.value('color')}")

# if op.isEnable("date"):
#     print(f"-d, --date : 対象日、が指定されました。date={op.value('date')}")

# if op.isEnable("size"):
#     print(f"-s, --size : 表示サイズ、が指定されました。size={op.value('size')}")

# if op.isEnable("ratio"):
#     print(f"-r, --ratio : 比率を指定する、が指定されました。ratio={op.value('ratio')}")

# if op.isEnable("extend"):
#     print("-x, --extend : 特別な奴、が指定されました。")

# if op.isEnable("expect"):
#     print("-e, --expect : 紛らわしい奴、が指定されました。")

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
