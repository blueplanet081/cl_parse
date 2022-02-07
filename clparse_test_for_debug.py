import sys
from enum import Flag, auto
from typing import List, Any

from lib import cl_parse_old5 as cl

# import functools


def show_definitionlist(op: cl.Parse) -> None:
    """ オプション設定一覧を表示する（デバッグ／ユーティリティ用） """
    for opt in op.option_attrs:
        opx = getattr(op, opt)
        print(opt)
        print(f'    s_options = {opx.s_options}')
        print(f'    l_options = {opx.l_options}')
        print(f'    comment = [{opx.comment}], acomment = [{opx.acomment}]')
        print(f'    atype = {opx.atype}')


def show_template(op: cl.Parse, options: cl.Union[List[str], cl.Dict[str, cl.Opset]]):
    """ テンプレートを表示する（デバッグ／ユーティリティ用） """

    def __show_one(stropt: str, objopt: Any):
        print((f'if op.{stropt}.isEnable:').ljust(30), f"# {objopt.comment}")
        if objopt.atype:
            print(f'    value = op.{stropt}.value')
        elif "help" in objopt.l_options:
            print('    print("使用方法を書く")')
            print('    # op.get_optionlist() 等を表示する')
            print('    exit()')
        else:
            print('    pass')

    print('# please replace "op" to appropriate instance name.')
    print('if op.is_error:')
    print('    # op.get_errormessage() 等を表示する')
    print('    exit(1)')
    if type(options) is list:
        for opt in options:
            opx = getattr(op, opt)
            __show_one(opt, opx)
    elif type(options) is dict:
        for opt in options.keys():
            __show_one(f'OPT_["{opt}"]', op.OPT_[opt])


args = sys.argv
if len(args) <= 1:
    # 試験用コマンドライン
    args = 'this.py # -ac BLUE|RED|GREEN ABC --size 1024x0X40  --exp -ar 0.5 --date 2021/10/3'.split()


class Color(Flag):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    # PURPLE = RED | GREEN
    WHITE = RED | GREEN | BLUE


# cl_parse 呼び出し用のオプション定義
options = [
        ["help", "-h, --help", "使い方を表示する", None],
        ["all", "-a, --all", "すべて出力"],
        ["date", "-d ,--date", "対象日//<年/月/日>", cl.date],
        ["color", "-c, --color", "表示色//<color>", Color],
        ["size", "-s, --size", "表示サイズを指定する//<縦x横>",
            cl.sepalate_items(type=cl.int_literal, sep='x', count=0)],
        ["ratio", "-r, --ratio", "比率を指定する//<比率>", float],
        ["xtend", "-x, --extend", "特別な奴"],
        ["expect", "-e, --expect", "紛らわしい奴"],
]

# cl_parse 呼び出し（解析実行）
op = cl.Parse(options, args, debug=True)

show_definitionlist(op)
show_template(op, op.option_attrs)
show_template(op, op._Parse__D_option)
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
if op.OPT_["date"].isEnable:   # 対象日
    value = op.OPT_["date"].value
    print(value)
if op.OPT_["color"].isEnable:  # 表示色
    value = op.OPT_["color"].value
if op.OPT_["size"].isEnable:   # 表示サイズを指定する
    value = op.OPT_["size"].value
if op.OPT_["ratio"].isEnable:  # 比率を指定する
    value = op.OPT_["ratio"].value
if op.OPT_["xtend"].isEnable:  # 特別な奴
    pass
if op.OPT_["expect"].isEnable: # 紛らわしい奴
    pass




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