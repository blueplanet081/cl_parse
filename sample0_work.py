import sys
from lib import cl_parse as cl
from datetime import datetime as dt


args = sys.argv
# 試験用コマンドライン
if len(args) <= 1:
    args = 'this.py -a ABC --size=1024x480  --date 2021/10/3 # ---#'.split()

date = lambda d: dt.strptime(d, '%Y/%m/%d')

options = [
        ["help", "-h, --help", "使い方を表示する", None],
        ["all", "-a, --all", "すべて出力"],
        # ["date", "-d, --date", "対象日//<年/月/日>", cl.date],
        # ["date", "-d, --date", "対象日//<年/月/日>", cl.strptime('%Y/%m/%d')],
        # ["date", "-d, --date", "対象日//<年/月/日>", lambda d: dt.strptime(d, '%Y/%m/%d')],
        ["date", "-d, --date", "対象日//<年/月/日>", date],
        ["size", "-s, --size", "表示サイズを指定する//<縦x横>",
            cl.sepalate_items(type=int, sep='x', count=0)],
]

# cl_parse 呼び出し（解析実行）
op = cl.Parse(args, options, debug=True)

# 解析エラー時の処理は自前で行う
if op.is_error:
    print(op.get_errormessage(1), file=sys.stderr)
    print("オプション一覧", file=sys.stderr)
    cl.tabprint(op.get_optionlist(), file=sys.stderr)
    exit(1)

# help情報の表示も自前
if op.OPT_help.isEnable:       # 使い方を表示する
    print("これは cl_parse のサンプルプログラムです。\n")
    print("オプション一覧")
    cl.tabprint(op.get_optionlist())
    exit()

if op.OPT_all.isEnable:        # すべて出力
    pass
if op.OPT_date.isEnable:       # 対象日
    value = op.OPT_date.value
if op.OPT_size.isEnable:       # 表示サイズを指定する
    value = op.OPT_size.value

