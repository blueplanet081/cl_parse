# -------------------------------------------------------------
# cl_parse用デバッグ用モジュール                2022/2/5 by te.
# （このモジュールが無ければ、デバッグ表示は無視されます）
# -------------------------------------------------------------
from typing import Union, List, Dict, Any
import cl_parse as cl


def show_templatex(op: cl.Parse, options: Union[List[str], Dict[str, cl.Opset]]):
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


def show_definitionlist(op: cl.Parse) -> None:
    """ オプション設定一覧を表示する（デバッグ／ユーティリティ用） """
    for opt in op.option_attrs:
        opx = getattr(op, opt)
        print(opt)
        print(f'    s_options = {opx.s_options}')
        print(f'    l_options = {opx.l_options}')
        print(f'    comment = [{opx.comment}], acomment = [{opx.acomment}]')
        print(f'    atype = {opx.atype}')


def show_result(op: cl.Parse) -> None:
    """ オプション解析結果一覧を表示する（デバッグ用） """
    for opt in op.option_attrs:
        opx = getattr(op, opt)
        strvalue = ""
        if opx.atype:
            strvalue = str(opx.value)
            if type(opx.value) is str:
                strvalue = "'"+strvalue+"'"     # 文字列(str)なら''で囲って表示する
        print(opt.ljust(12),
              f"=> {str(opx.isEnable).ljust(5)}  {strvalue}")


def show_debug(op: cl.Parse, __dmode: str):
    """ デバッグ表示振り分け """
    if __dmode.startswith("##"):
        if __dmode == "##":
            print("オプション設定一覧x")
            show_definitionlist(op)
            exit()
        elif __dmode == "##1":
            print("テンプレート１x")
            show_templatex(op, op.option_attrs)
            exit()
        elif __dmode == "##2":
            print("テンプレート２x")
            show_templatex(op, op._Parse__D_option)
            exit()

    elif __dmode.startswith("#"):
        if __dmode in ["#", "#1"]:
            print("入力引数一覧")
            for i, arg in enumerate(op._Parse__args):
                print(f"arg[{i}]: {arg}")
            print()
        if __dmode in ["#", "#2"]:
            print("オプション解析結果一覧")
            show_result(op)
            print()
            print("コマンド引数一覧")
            for i, param in enumerate(op.params):
                print(f"arg[{i}]: {param}")
            if op.remain:
                print()
                print("残りの入力引数一覧")
                for i, param in enumerate(op.remain):
                    print(f"arg[{i}]: {param}")
            print()
            if op.is_error:
                print("解析エラーあり")
                print(op.get_errormessage(2))
            else:
                print("解析エラーなし")
            print()
        if __dmode in ["#", "#1", "#2"]:
            input('Hit any key for start program:')
            print("-------- START PROGRAM --------")
            return

    print('debugmode for "---##" の指定方法')
    print('---##  :オプション設定一覧を表示して終了')
    print('---##1 :テンプレート（OPT_xxxx）を表示して終了')
    print('---##2 :テンプレート（OPT_["xxxx"]）を表示して終了')
    print()
    print('debugmode for "---#" の指定方法')
    print('---#  :入力引数一覧、解析結果を表示して続行')
    print('---#1 :入力引数一覧を表示して続行')
    print('---#2 :解析結果を表示して続行')
    print()
    exit()
