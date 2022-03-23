# -------------------------------------------------------------
# cl_parse用デバッグ用モジュール               2022/3/23 by te.
# （このモジュールが無ければ、デバッグ表示は無視されます）
# -------------------------------------------------------------
from __future__ import annotations
from typing import Any
import cl_parse as cl


def show_templatex(ps: cl.Parse, options: list[str] | dict[str, cl.Opset]):
    """ テンプレートを表示する（デバッグ／ユーティリティ用） """

    def __show_one(stropt: str, objopt: Any):
        print((f'if ps.{stropt}.isEnable:').ljust(30), f"# {objopt.comment.splitlines()[0]}")
        if objopt.afunc:
            print(f'    value = ps.{stropt}.value')
        elif "help" in objopt.l_options:
            print('    print("使用方法を書く")')
            print('    # ps.get_optionlist() 等を表示する')
            print('    exit()')
        else:
            print('    pass')

    print('# please replace "ps" to appropriate instance name.')
    print('if ps.is_error:')
    print('    # ps.get_errormessage() 等を表示する')
    print('    exit(1)')
    if type(options) is list:
        for opt in options:
            opx = getattr(ps, opt)
            __show_one(opt, opx)
    elif type(options) is dict:
        for opt in options.keys():
            __show_one(f'OPT_["{opt}"]', ps.OPT_[opt])
    print()
    print("print(f'{ps.params=}')         # コマンド引数")


def show_definitionlist(ps: cl.Parse) -> None:
    """ オプション設定一覧を表示する（デバッグ／ユーティリティ用） """
    for opt in ps.option_attrs:
        opx = getattr(ps, opt)
        print(opt)
        print(f'    s_options = {opx.s_options}')
        print(f'    l_options = {opx.l_options}')
        print(f'    comment = [{opx.comment}], acomment = [{opx.acomment}]')
        print(f'    afunc = {opx.afunc}')
        print(f'    atype = {opx.atype}')
    print()
    if len(ps._Parse__exclusive):
        print("exclusive =")
    else:
        print("exclusive = []")
    for pair in ps._Parse__exclusive:
        print(f'    {pair}')


def show_result(ps: cl.Parse) -> None:
    """ オプション解析結果一覧を表示する（デバッグ用） """
    for opt in ps.option_attrs:
        opx = getattr(ps, opt)
        strvalue = ""
        if opx.afunc or opx.atype:
            strvalue = str(opx.value)
            if type(opx.value) is str:
                strvalue = "'"+strvalue+"'"     # 文字列(str)なら''で囲って表示する
        print(opt.ljust(12),
              f"=> {str(opx.isEnable).ljust(5)}  {strvalue}")


def show_errormessage() -> None:
    import cl_parse as cl

    """ 解析エラーメッセージ一覧を表示する（デバッグ用） """
    # for eno in cl.emsg:
    #     print(cl.Parse._Parse__error_message(eno,
    #                 arg="<ARG>", opt="<OPT>", ext0="<EXT0>", ext1="<EXT1>"))
    # print()
    cl.Parse.show_errormessage()
    print()
    print(cl.emsg)


def show_debug(ps: cl.Parse, __dmode: str):
    """ デバッグ表示振り分け """
    if __dmode.startswith("##"):
        if __dmode == "##":
            print("オプション設定一覧")
            show_definitionlist(ps)
            exit()
        elif __dmode == "##1":
            print("テンプレート１")
            show_templatex(ps, ps.option_attrs)
            exit()
        elif __dmode == "##2":
            print("テンプレート２")
            show_templatex(ps, ps._Parse__D_option)
            exit()
        elif __dmode == "##e":
            print("エラーメッセージ一覧")
            show_errormessage()
            exit()

    elif __dmode.startswith("#"):
        if __dmode in ["#", "#1"]:
            print("入力引数一覧")
            for i, arg in enumerate(ps._Parse__args):
                print(f"arg[{i}]: {arg}")
            print()
        if __dmode in ["#", "#2"]:
            print("オプション解析結果一覧")
            show_result(ps)
            print()
            print("コマンド引数一覧")
            for i, param in enumerate(ps.params):
                print(f"arg[{i}]: {param}")
            if ps.remain:
                print()
                print("残りの入力引数一覧")
                for i, param in enumerate(ps.remain):
                    print(f"arg[{i}]: {param}")
            print()
            if ps.is_error:
                print("解析エラーあり")
                print(ps.get_errormessage(2))
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
