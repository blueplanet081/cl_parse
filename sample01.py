import sys
from lib import cl_parse as cl
from lib import cl_parse_functions as cf


args = sys.argv
# 試験用コマンドライン
if len(args) <= 1:
    args = 'this.py -a ABC --name=私だ  --date 2021/10/3 # ---#'.split()

options = [
        ["#Usage: 使い方をここに書く"],
        ["help", "-h, --help", "使い方を表示する", None],
        ["all", "-a, --all", "すべて出力"],
        ["name", "-n, --name", "使用者名を指定する//<名前>", str],
        ["count", "-c, --count", "数量を指定する//<数(整数)>", int],
        ["date", "-d, --date", "対象日//<年/月/日>", cf.strptime('%Y/%m/%d')],
]

# cl_parse 呼び出し（解析実行）
ps = cl.Parse(args, options, emessage_header="@stem", debug=True)

# 解析エラー時の処理は自前で行う
if ps.is_error:
    print(ps.get_errormessage(1), file=sys.stderr)
    print()
    cl.tabprint(ps.get_optionlist(), file=sys.stderr)
    exit(1)

# help情報の表示も自前
if ps.OPT_help.isEnable:       # 使い方を表示する
    print("これは cl_parse のサンプルプログラムです。\n")
    cl.tabprint(ps.get_optionlist())
    exit()

# 解析結果
if ps.OPT_all.isEnable:        # すべて出力
    print("オプション 'all' が指定されました。")

if ps.OPT_name.isEnable:       # 使用者名を指定する
    print("オプション 'name' が指定されました。")
    print(f'    {ps.OPT_name.value=}')
    print()

if ps.OPT_count.isEnable:       # 数量を指定する
    print("オプション 'count' が指定されました。")
    print(f'    {ps.OPT_count.value=}')
    print()

if ps.OPT_date.isEnable:       # 対象日
    print("オプション 'date' が指定されました。")
    print(f'    {ps.OPT_date.value=}')
    print()

if len(ps.params):
    print("以下のコマンド引数が入力されました。")
    print(ps.params)
