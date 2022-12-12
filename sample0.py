import sys
from lib import cl_parse as cl
from lib import cl_parse_functions as cf


args = sys.argv
# 試験用コマンドライン
if len(args) <= 1:
    args = 'this.py -a ABC --size=1024x480  --date 2021/10/3 # ---#'.split()

options = [
        ("help", "-h, --help", "使い方を表示する", None),
        ("all", "-a, --all", "すべて出力"),
        ("date", "-d, --date", "対象日//<年/月/日>", cf.strptime('%Y/%m/%d')),
        ("size", "-s, --size", "表示サイズを指定する//<縦x横>",
                               cf.sepalate_items(type=int, sep='x', count=0)),
]

# cl_parse 呼び出し（解析実行）
op = cl.Parse(args, options, debug=True)

# 解析エラー時の処理は自前で行う
if op.is_error:
    print(op.get_errormessage(1), file=sys.stderr)
    print()
    print("オプション一覧", file=sys.stderr)
    cl.tabprint(op.get_optionlist(), file=sys.stderr)
    exit(1)

# help情報の表示も自前
if op.OPT_help.isEnable:       # 使い方を表示する
    print("これは cl_parse のサンプルプログラムです。\n")
    print("オプション一覧")
    cl.tabprint(op.get_optionlist())
    exit()

# 解析結果
if op.OPT_all.isEnable:        # すべて出力
    print("オプション 'all' が指定されました。")

if op.OPT_date.isEnable:       # 対象日
    print("オプション 'date' が指定されました。")
    print(f'    {op.OPT_date.value=}')
    print()

if op.OPT_size.isEnable:       # 表示サイズを指定する
    print("オプション 'size' が指定されました。")
    print(f'    {op.OPT_size.value=}')
    print()

if len(op.params):
    print("以下のコマンド引数が入力されました。")
    print(op.params)
