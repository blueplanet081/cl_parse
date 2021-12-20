import sys
from lib import cl_parse_old as cl

# import functools

# 試験用コマンドライン
args = 'this.py -a ABC --size 1024x480  -ar 0.5 --date 2021/10/3 #'.split()
# args = sys.argv

options = [
        ["h", "help", "使い方を表示する", None],
        ["a", "all", "すべて出力"],
        ["d", "date", "対象日//<年/月/日>", cl.date],
        ["s", "size", "表示サイズを指定する//<縦x横>",
            cl.sepalate_items(type=int, sep='x', count=0)],
        ["r", "ratio", "比率を指定する//<比率>", float],
]

# cl_parse 呼び出し（解析実行）
op = cl.Parse(options, args, debug=True)

# 解析エラー時の処理は自前で行う
if op.is_error:
    print(op.get_errormessage(1), file=sys.stderr)
    print("オプション一覧", file=sys.stderr)
    op.show_optionslist(file=sys.stderr)
    exit(1)

# help情報の表示も自前
if op.isEnable("help"):
    print("使い方を表示する。")
    op.show_optionslist()
    exit()

# ここから自分のプログラム
if op.isEnable("all"):
    print("-a, --all : すべて出力、が指定されました。")

if op.isEnable("date"):
    print(f"-d, --date : 対象日、が指定されました。date={op.value('date')}")

if op.isEnable("size"):
    print(f"-s, --size : 表示サイズ、が指定されました。size={op.value('size')}")

if op.isEnable("ratio"):
    print(f"-r, --ratio : 比率を指定する、が指定されました。ratio={op.value('ratio')}")

