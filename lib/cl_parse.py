#!/usr/bin/env python3
# -------------------------------------------------------------
# 簡易コマンドラインパーサー cl_parse改の途中   2022/2/2 by te.
# -------------------------------------------------------------
import sys
import glob
import pathlib
import platform
from datetime import datetime as dt
from enum import Enum, EnumMeta, Flag, IntFlag, auto
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union
from typing import TextIO


# -------------------------------------------------------------
# 日本語混じり文字列を整形するクラスの一部の超簡易版 for tabprint
# tabplintが不要なら、両方削ってください。
# -------------------------------------------------------------
import unicodedata
class Wstr(str):
    def width(self) -> int:
        """ 日本語混じり文字列の表示幅を取得する """
        return sum([(2 if unicodedata.east_asian_width(c) in 'FWA' else 1) for c in self])

    def ljust(self, __width: int, __fillchar: str = " ") -> 'Wstr':     # type: ignore
        """ str.ljust() のワイド文字対応版） """
        return Wstr(self + __fillchar*(__width - self.width()))


# -------------------------------------------------------------
# tabprint（付録）
# -------------------------------------------------------------
def _eter_list(anylist: List[Any], eter: Any = ...) -> Iterator[Any]:
    ''' listの要素を無限に繰り返す Iterator。
        anylistの要素数を越えた場合は、eterを返す。eter省略時は、anylistの最終要素を返す
    '''
    for num in anylist:
        yield num
    if eter == Ellipsis:    # 最後の要素を繰り返す
        while True:
            yield anylist[-1]
    else:                   # eter を繰り返す
        while True:
            yield eter


def _makeline(line: List[str], tablist: List[int]) -> str:
    ''' タブを揃えた文字列（一行分）を作成する '''
    def _addtab(width: int) -> int:     # 個々のtext幅の、tab揃えの計算
        w = 0
        while w <= width:
            w += next(tabstop)
        return w

    tabstop = _eter_list(tablist)
    return ''.join([Wstr(text).ljust(_addtab(Wstr(text).width())) for text in line]).rstrip()


def tabprint(table: List[List[str]], tablist: List[int] = [8],
             file: TextIO = sys.stdout):
    ''' 単純タブ揃え表示
        （table中の各lineの、各項目を直近のタブに揃えて表示する）
    '''
    for line in table:
        print(_makeline(line, tablist), file=file)


# -------------------------------------------------------------
# こまかいの（一応汎用）
# -------------------------------------------------------------
def split2(text: str, sp: str) -> Tuple[str, Optional[str]]:
    """ 文字列をspで２分割してタプルで返す """
    """ セパレータ(sp) 以降が無ければ、ret[1]は空文字、
        セパレータ(sp) が存在しなければ、ret[1]は None
    """
    ret: List[Any] = text.split(sp, 1)
    ret = ret + [None]
    return ret[0], ret[1]
    # return tuple((text.split(sp, 1) + [None])[0:2])


def count_prefix(text: str, prefix_char: str, max_count: int = 0) -> int:
    ''' プリフィックス文字の数を返す
    '''
    count = 0
    for char in text:
        if char == prefix_char[0]:
            count += 1
            if max_count and count >= max_count:
                return count
            continue
        break
    return count


# -------------------------------------------------------------
# ターンチェック（一応、汎用クラス）
# -------------------------------------------------------------
class CheckTurn():
    def __init__(self):
        """ ターンをチェックするクラス """
        self.__turn = None                  # 現在のターン
        self.d_turn: Dict[Enum, int] = {}   # ターン回数記録用

    def checkTurn(self, turn: Enum) -> bool:
        """ ターンの状態をチェックする。前回のターンから変わったら True """
        check = True if turn is not self.__turn else False
        self.__turn = turn
        if check:
            self.d_turn[turn] = self.d_turn.get(turn, 0) + 1
        return check

    def getTimes(self, turn: Enum) -> int:
        """ そのターンになった回数を返す。初回が 1 """
        return self.d_turn.get(turn, 0)

    def isRepeat(self, turn: Enum) -> bool:
        """ そのターンが２回目以降だったら True """
        return self.d_turn.get(turn, 0) > 1


class Turn(Enum):
    """ cl_parse用、解析のターン（OPT:オプション、ARG:コマンド引数） """
    OPT = auto()    # オプション解析のターン
    ARG = auto()    # コマンド引数解析のターン


# -------------------------------------------------------------
# ワイルドカード展開モジュール（Windows汎用）
# -------------------------------------------------------------

# Windowsかどうか判定
isWin = True if platform.system() == 'Windows' else False


def __getWild(wild: str) -> List[str]:
    """ ホームディレクトリ '~'、ワイルドカードを展開して、リストで返す。
        頭にハイフンが付いているもの、ワイルドカードに展開できないものはそのまま返す
        （その時は、「要素が1つ」のリストになる）
    """
    ret: List[str] = []
    if wild.startswith(' ') or wild.startswith('\\'):
        ret.append(wild[1:])
        return ret
    if wild.startswith('~'):
        wild = str(pathlib.Path.home()) + wild[1:]

    if '*' in wild or '?' in wild or ('[' in wild and len(wild) > 1):
        for w in glob.glob(wild):
            ret.append(w)
        if not ret:
            ret.append(wild)
    else:
        ret.append(wild)
    return ret


def _wArgs(__args: List[str]) -> List[str]:
    """ 渡されたリスト中の項目をワイルドカード展開する """
    ret: List[str] = []
    for p in __args:
        ret += __getWild(p)
    return ret


# -------------------------------------------------------------
# ファイル展開モジュール（ほとんど cl_parse専用）
# 使い物になるか（コマンドラインで @xxxx を取得できるか）要検証★★★
# -------------------------------------------------------------
def file_expand(args: List[str]) -> List[str]:
    """ リスト中の、”@<ファイル名>" の要素を展開する """
    ret: List[str] = []
    for item in args:
        if item.startswith("@"):
            try:
                with open(item[1:]) as f:
                    text = f.read().split()
            except FileNotFoundError:
                raise Exception(item)
            ret += text
        else:
            ret += [item]
    return ret


# ---------------------------------------------------------------------------
# Instant Closureクラス（まあ汎用）
# ---------------------------------------------------------------------------
class Mu:
    """ Instant Closure クラス """
    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any):
        """ 普通の関数(func)をクロージャーとして埋め込むクラス """

        # 仕様は functools.partial() とほとんど同じ（多分）だけど、
        # 埋め込んだ functionを呼び出すときの位置引数の順番が逆
        # （呼び出し時の引数が先、埋め込んだ引数が後）

        self.args = args
        self.kwargs = kwargs
        self.func = func

    def __call__(self, *args2: Any, **kwargs2: Any):
        return self.func(*args2, *self.args, **{**self.kwargs, **kwargs2})

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} {repr(self.func)} {repr(self.args)} {repr(self.kwargs)}'


class Mu2:
    """ Instant Closure ^2 クラス """
    def __init__(self, func: Callable[..., Any],
                 func2: Callable[..., Any], *args: Any, **kwargs: Any):
        """ functionと、そこから呼び出すfunctionを一緒に埋め込むクラス
            （仕様、使い方検討中）
        """
        self.args = args
        self.kwargs = kwargs
        self.func = func
        self.func2 = func2

    def __call__(self, *args2: Any, **kwargs2: Any):
        return self.func(self.func2, *args2, *self.args, **{**self.kwargs, **kwargs2})

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} {repr(self.func)} {repr(self.func2)} ' + \
               f'{repr(self.args)} {repr(self.kwargs)}'


# -----------------------------------------------------
# 追加の、オプション引数のタイプ（cl_parse用）
# -----------------------------------------------------
def sepalate_items__(
        moto: str, type: Optional[Callable[[str], Any]] = None,
        sep: str = ',', count: int = 0) -> List[Any]:
    """ オプション引数をセパレータ(sep)で指定個数(count)に分割して解釈する。
        エラー時の処理が cl_parse 用
    """
    motos = moto.split(sep)
    if count != 0 and len(motos) != count:
        raise ValueError(f"sepalate items count error. required {count} "
                         f"/ detected {len(motos)} at arg=[{moto}]")
    if type:
        motos = list(map(type, motos))
    return motos


sepalate_items = Mu2(Mu, sepalate_items__)

# int_literal = functools.partial(int, base=0)
int_literal = Mu(int, base=0)           # 数値リテラル（"0x4F3e"みたいな）を解釈するタイプ
date = Mu(dt.strptime, '%Y/%m/%d')      # 日付 <年>/<月>/<日> 入力


# -----------------------------------------------------
# cl_parse 内部使用関数
# -----------------------------------------------------
def cnv_enum(atype: EnumMeta, ename: str) -> Any:
    """ 列挙型(atype)の「名前(ename)から、列挙型メンバーを作成する
        （Flag、IntFlagの演算子は | のみ解釈）
    """
    """ 型ヒントをどのように書けば良いのか、模索中 ^^;
    """
    wmembers = list(atype.__members__.keys())
    try:
        if atype.__base__ is Flag or IntFlag:
            flist = [t.strip() for t in ename.split('|')]
            ret = atype[flist[0]]
            for t in flist[1:]:
                ret |= atype[t]
            return ret
        return atype[ename]

    except KeyError as e:
        raise ValueError(f"option argument {e} must be a member of {wmembers}")


# -----------------------------------------------------
# エラーメッセージのテンプレート
# -----------------------------------------------------
emsg = {
    "N00": "no error",
    "E01": "{eno}: FileNotFoundError at {arg}",
    "E11": "{eno}: missing argument for option {arg}",
    "E12": "{eno}: illegal argument for option {arg}",
    "E13": "{eno}: unnecessary argument for option {arg}",
    "E14": "{eno}: illegal option {arg}",
    "E21": "{eno}: missing argument for option {opt} in {arg}",
    "E22": "{eno}: illegal argument for option {opt} in {arg}",
    "E23": "{eno}: illegal option {opt} in {arg}",
    "E99": "{eno}: unknown error opt={opt}, arg={arg}, ext0={ext0}, ext1={ext1}",
}


# -----------------------------------------------------
# 解析用条件
# -----------------------------------------------------
class Smode(Enum):
    """ コマンドライン解析モード
        （NONE:全解析、ONEPAIR:1組、OPTFIRST:オプション先、ARGFIRST:コマンド引数先）
    """
    NONE = auto()           # モードなし（全解析）
    ONEPAIR = auto()        # 1組モード（オプションとコマンド引数、1組で終了）
    OPTFIRST = auto()       # オプション先モード（コマンド引数後のオプションは無視）
    ARGFIRST = auto()       # コマンド引数先モード（オプション後の引数は無視）


# -----------------------------------------------------
# コマンドライン・ブロックタイプ判定用
# -----------------------------------------------------
class Bt(Flag):
    """ コマンドライン・ブロックタイプ """
    SOPTn = auto()      # １文字オプションブロックで、最初が数字
    SOPTs = auto()      # １文字オプションブロックで、最初が数字以外
    SOPT = SOPTs | SOPTn    # １文字オプションブロック
    LOPT = auto()       # ロング名オプションブロック
    SONLY = auto()      # １文字オプション・プリフィックス（"-"） のみ
    LONLY = auto()      # ロング名オプション・プリフィックス（"--"） のみ
    NORMAL = auto()     # 通常ブロック
    NONE = auto()       # None
    BLANK = auto()      # 空ブロック


def check_blocktype(blk: Optional[str], prefix: str) -> Bt:
    """ コマンドライン・ブロックのタイプを返す """
    if blk is None:
        return Bt.NONE      # None
    bs = iter(blk)
    c1 = next(bs, None)
    if c1 is None:          # 空文字列（１文字もなし）
        return Bt.BLANK         # NONE
    if c1 != prefix:        # 頭が "-" でない
        return Bt.NORMAL        # NORMAL（オプション文字列ではない）
    c2 = next(bs, None)
    if c2 is None:          # ２文字目以降がない
        return Bt.SONLY         # SONLY（"-" のみ）
    if c2 != prefix:        # ２文字目が "-" でない
        if c2.isdecimal():      # ２文字目が数字
            return Bt.SOPTn         # SOPTn（"-9xxx"）
        return Bt.SOPTs         # SOPTs（"-xxxx"）
    c3 = next(bs, None)
    if c3 is None:          # ３文字目以降がない
        return Bt.LONLY         # LONLY（"--" のみ）
    return Bt.LOPT          # LOPT（"--xxxx"）


# -----------------------------------------------------
# 定義されたオプションセット格納用クラス
# -----------------------------------------------------
class Opset:
    def __init__(self, l_options: List[str], s_options: List[str],
                 comment: str, acomment: str, atype: Any) -> None:
        """ オプションセット格納用クラス """
        self.__l_options = l_options
        self.__s_options = s_options
        self.__comment = comment        # コメント
        self.__acomment = acomment      # オプション引数のコメント
        self.__atype = atype            # オプション引数のタイプ

        self.__isEnable: bool = False   # オプション有効/無効
        self.__value: Any = None        # オプション引数

    @property
    def l_options(self) -> List[str]:
        return self.__l_options

    @property
    def s_options(self) -> List[str]:
        return self.__s_options

    @property
    def comment(self) -> str:
        return self.__comment

    @property
    def acomment(self) -> Any:
        return self.__acomment

    @property
    def atype(self) -> Any:
        return self.__atype

    @property
    def isEnable(self) -> bool:
        return self.__isEnable

    def _set_isEnable(self, isenable: bool):
        self.__isEnable = isenable

    @property
    def value(self) -> bool:
        return self.__value

    def _set_value(self, value: bool):
        self.__value = value


# -----------------------------------------------------
# パーサー本体
# -----------------------------------------------------
class Parse:
    def __init__(self, options: List[List[Any]],
                 args: List[str],                   # 解析するコマンドライン
                 smode: Smode = Smode.NONE,         # 解析モード
                 winexpand: bool = True,            # Windowsで、ワイルドカードを展開するかどうか
                 file_expand: bool = False,         # コマンド引数の @<filename> を展開するかどうか
                 comment_sp: str = '//',            # オプションコメントのセパレータ
                 debug: bool = False,               # デバッグ指定（--@ で結果一覧出力）
                 option_name_prefix: str = "OPT_",  # 自プログラム内でオプションを指定する時のprefix
                 option_string_prefix: str = "-",   # オプションの前に付ける - とか --
                 ) -> None:
        """ コマンドラインパーサー """

        self.__args = args
        self.__smode = smode
        self.__winexpand = winexpand
        self.__filexpand = file_expand
        self.__commentsp = comment_sp
        self.__debug = debug
        self.__option_name_prefix = option_name_prefix
        self.__option_string_prefix = option_string_prefix[0:1]

        self.__debugmode: str = ""              # デバッグモードを格納

        self.__options: List[str] = []          # 設定されたオプション属性リスト
        self.__ltoOPS: Dict[str, str] = {}
        self.__stoOPS: Dict[str, str] = {}

        # オプション情報（Dict タイプ）
        self.__D_option: Dict[str, Opset] = {}  # OPT_["option"] で取得する

        # オプションセット読み込み処理実行
        self.__set_options(options)

        self.__s_options = list(self.__stoOPS.keys())     # 1文字オプション一覧
        self.__l_options = list(self.__ltoOPS.keys())     # ロング名オプション一覧

        # コマンドライン解析結果格納用 ---------------------------------
        self.__params: List[str] = []           # コマンド引数リスト
        self.__error: bool = True               # 解析エラーがあったかどうか
        self.__error_reason: Dict[str, str] = {"eno": "N00"}    # エラー理由
        self.__additional_emsg = ""             # 追加のエラーメッセージ
        self.__remain: List[str] = []           # 解析の残り

        # コマンドライン解析処理実行
        self.__parse()

        # デバッグモード
        if self.__debugmode:
            __dmode = str(self.__debugmode)[1:]
            if __dmode.startswith("##"):
                if __dmode == "##":
                    print("オプション設定一覧")
                    self.show_definitionlist()
                    exit()
                elif __dmode == "##1":
                    print("テンプレート１")
                    self.__show_template(self.option_attrs)
                    exit()
                elif __dmode == "##2":
                    print("テンプレート２")
                    self.__show_template(self.__D_option)
                    exit()

            elif __dmode.startswith("#"):
                if __dmode in ["#", "#1"]:
                    print("入力引数一覧")
                    for i, arg in enumerate(self.__args):
                        print(f"arg[{i}]: {arg}")
                    print()
                if __dmode in ["#", "#2"]:
                    print("オプション解析結果一覧")
                    self.show_result()
                    print()
                    print("コマンド引数一覧")
                    for i, param in enumerate(self.params):
                        print(f"arg[{i}]: {param}")
                    if self.remain:
                        print()
                        print("残りの入力引数一覧")
                        for i, param in enumerate(self.remain):
                            print(f"arg[{i}]: {param}")
                    print()
                    if self.is_error:
                        print("解析エラーあり")
                        print(self.get_errormessage(2))
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

    # -----------------------------------------------------
    # オプションセット読み込み処理
    # -----------------------------------------------------
    def __set_options(self, options: List[List[Any]]) -> None:
        """ オプションセットを読み込む """
        for iopset in options:
            iopset = (iopset + [None] * (4 - len(iopset)))[0:4]

            import keyword

            # オプション名の処理 --------------------------------
            opt_name = iopset[0]
            if not opt_name.startswith(self.__option_name_prefix):     # 頭に prefixが付いてなかったら
                opt_name = self.__option_name_prefix + opt_name            # 頭に prefixを付加

            # Python変数としての文字種チェック
            assert opt_name.isidentifier() and (not keyword.iskeyword(opt_name)),\
                f'illegal option name [{opt_name}] in {iopset}'
            # 重複チェック
            assert opt_name not in self.__options,\
                f'duplicated option name [{opt_name}] in {iopset}'

            # オプション文字列の処理 ----------------------------
            s_options: List[str] = []
            l_options: List[str] = []
            option_strings = list(map(lambda x: x.strip(), iopset[1].split(',')))
            for s in option_strings:
                count = count_prefix(s, self.__option_string_prefix, max_count=0)
                if count == 1:
                    s_options.append(s[1:])
                elif count == 2:
                    l_options.append(s[2:])
                else:
                    assert False, \
                        f'illegal option string [{s}] in {iopset}'

            # iopset[0] : 1文字オプション、iopset[1] : ロング名オプション
            assert isinstance(iopset[1], str) and isinstance(iopset[2], str), \
                f'illegal type of "option" {iopset}'

            # iopset[2] : コメント//オプション引数のコメント
            assert isinstance(iopset[2], str), \
                f'illegal type of "comment//option-argument comment" {iopset}'
            icomment, ioacomment = split2(iopset[2], self.__commentsp)
            ioacomment = "" if ioacomment is None else ioacomment

            # iopset[3] : オプション引数のタイプ（存在しなければ None）
            ioatype = iopset[3]
            assert ioatype is None or callable(ioatype), \
                f'illegal type of "option-argument type" {iopset}'

            # cl改用★★★
            setattr(self, opt_name, Opset(l_options, s_options, icomment, ioacomment, ioatype))
            self.__D_option[iopset[0]] = getattr(self, opt_name)     # オプション情報 Dictバージョン
            self.__options.append(opt_name)
            for s in l_options:
                assert s not in self.__ltoOPS.keys(), f'duplicated option string --{s} in {iopset}'
                self.__ltoOPS[s] = opt_name
            for s in s_options:
                assert s not in self.__stoOPS.keys(), f'duplicated option string -{s} in {iopset}'
                self.__stoOPS[s] = opt_name

    # -----------------------------------------------------
    # コマンドライン解析の本文
    # -----------------------------------------------------
    def __parse(self) -> None:
        """ コマンドラインを解析する """
        t = CheckTurn()         # ターンチェック用

        if self.__debug:        # デバッグモード指定を取得
            wargs: List[str] = []
            for item in self.__args:
                if item.startswith("---"):
                    self.__debugmode = "*" + item[3:]
                else:
                    wargs += [item]
            self.__args = wargs

        if self.__filexpand:    # ファイル展開
            try:
                self.__args = file_expand(self.__args)
            except Exception as e:
                self.__set_error_reason('E01', str(e))
                return

        if isWin and self.__winexpand:  # Windows用、ワイルドカード展開
            self.__args = _wArgs(self.__args)

        # 解析本文
        b_args = iter(self.__args)      # コマンドライン（文字列のリスト）をイテレータに
        for arg in b_args:
            # コマンドラインの１ブロックずつ、ブロックタイプを判定
            blk_type = check_blocktype(arg, self.__option_string_prefix)

            if blk_type in Bt.LONLY:    # ロング名オプション・プリフィックス（"--"） のみ ==========
                if t.checkTurn(Turn.ARG):   # ターンチェック（コマンド引数）
                    if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.ARG)) or \
                       (self.__smode == Smode.ARGFIRST and t.getTimes(Turn.OPT)):
                        break

                wparam = next(b_args, None)     # 次のブロックを取得
                if wparam is None:              # 次のブロックが無ければ終了
                    break
                self.__params.append(str(wparam))   # 次のブロックは無条件に「コマンド引数」
                continue

            elif blk_type in Bt.LOPT:   # ロング名オプションブロック（頭が「--」） =================
                if t.checkTurn(Turn.OPT):   # ターンチェック（オプション）
                    if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.OPT)) or \
                       (self.__smode == Smode.OPTFIRST and t.getTimes(Turn.ARG)):
                        break

                opt, oarg = split2(arg[2:], '=')  # オプション名、引数を取得
                opt = self.__complete_l_option(opt)
                if opt:     # 正しいロング名オプション ----------
                    __ops = getattr(self, self.__ltoOPS[opt])
                    __ops._set_isEnable(True)

                    if __ops.atype:     # オプション引数が必要 ---------
                        harg = arg  # for 'E12' error_reason
                        if oarg is None:                    # オプション引数無し（= 以降が無い）
                            oarg = next(b_args, None)           # 次のブロックを引数として取得
                            if oarg is None:                    # それも無ければエラー
                                self.__set_error_reason('E11', arg=arg)
                                return
                            harg = harg + " " + oarg  # for 'E12' error_reason

                        ret = self.__set_value(__ops, oarg)    # オプション引数を格納
                        if not ret:     # オプション引数格納（変換）エラー
                            self.__set_error_reason('E12', arg=harg)
                            return

                    else:                   # オプション引数が不要 ---------
                        if oarg is not None:                     # オプション引数が不要なのに引数あり
                            self.__set_error_reason('E13', arg=arg)
                            return
                else:       # ロング名オプションが正しくない ----
                    self.__set_error_reason('E14', arg=arg)
                    return

            elif blk_type in Bt.SOPT | Bt.SONLY:    # 1文字オプションブロック（頭が「-」）===========
                # プリフィックスのみ、とりあえず無視 ★★★
                if t.checkTurn(Turn.OPT):   # ターンチェック（オプション）
                    if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.OPT)) or \
                       (self.__smode == Smode.OPTFIRST and t.getTimes(Turn.ARG)):
                        break

                c_arg = iter(arg[1:])
                for opt in c_arg:
                    if opt in self.__s_options:   # 正しい1文字オプション -----------
                        __ops = getattr(self, self.__stoOPS[opt])
                        __ops._set_isEnable(True)

                        if __ops.atype:             # オプション引数が必要か
                            oparg = "".join([c for c in c_arg])    # 後続文字列からオプション引数を取得
                            harg = arg  # for 'E22' error_reason

                            if not oparg:           # 無ければ、
                                oparg = next(b_args, None)  # 次のブロックを取得
                                if not oparg:               # それも無ければエラー
                                    self.__set_error_reason('E21', opt=opt, arg=arg)
                                    return
                                harg = harg + " " + oparg   # for 'E22' error_reason

                            ret = self.__set_value(__ops, oparg)  # オプション引数を格納
                            if not ret:     # オプション引数格納（変換）エラー
                                self.__set_error_reason('E22', opt=opt, arg=harg)
                                return
                    else:                       # 1文字オプションが正しくない ------
                        self.__set_error_reason('E23', opt=opt, arg=arg)
                        return

            else:   # コマンド引数ブロック（頭が「―」以外）===========================================
                # bt.LOPT、bt.LONLY、bt.SOPT、Bt.SONLY 以外（Bt.NORMAL、Bt.NONE、Bt.BLANK）
                if t.checkTurn(Turn.ARG):   # ターンチェック（コマンド引数）
                    if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.ARG)) or \
                       (self.__smode == Smode.ARGFIRST and t.getTimes(Turn.OPT)):
                        break

                self.__params.append(arg)

        else:   # ループ終了
            self.__error = False
            return

        # 途中終了
        self.__remain = [arg] + [_arg for _arg in b_args]       # 残りのコマンドラインを格納
        self.__error = False
        return

    def __set_value(self, __ops: Opset, optarg: Any) -> bool:
        """ このオプションのオプション引数を格納する。エラー時には Falseを返す """
        try:
            # 「str」の時はそのまま格納
            if __ops.atype is str:
                __ops._set_value(optarg)

            # Enum、Flag類
            elif isinstance(__ops.atype, EnumMeta):
                __ops._set_value(cnv_enum(__ops.atype, optarg))

            # 直接変換呼び出しできるもの
            else:
                __ops._set_value(__ops.atype(optarg))

            return True

        except ValueError as e:     # 変換エラー
            self.__additional_emsg = str(e)
            return False

    def __complete_l_option(self, opt: Optional[str]) -> str:
        """ 入力のオプション（省略形を含む）から、完全なロング名オプションを探す
            （一致しなければ空文字を返す）
        """
        if not opt:
            return ""
        keep = ""
        for lopt in self.__l_options:
            if lopt.startswith(opt):    # 先頭一致でロング名オプションリストを検索
                if keep:                    # 二度以上一致したらエラー（一意でない）
                    return ""
                keep = lopt                 # 一致したら、ロング名オプションをkeep
        return keep             # 一度だけ一致していたら、そのロング名オプションが入っている

    def __set_error_reason(self, eno: str, arg: str = "???", opt: str = "???",
                           ext0: str = "ext0", ext1: str = "ext1") -> None:
        """ 解析エラーの理由をセットする """
        self.__error_reason = {
            "eno": eno, "arg": arg, "opt": opt, "ext0": ext0, "ext1": ext1
        }

    @staticmethod
    def __error_message(eno: str, arg: str = "???", opt: str = "???",
                        ext0: str = "ext0", ext1: str = "ext1") -> str:
        """ 解析エラーメッセージを作成する """
        if eno in emsg.keys():
            return emsg[eno].format(eno=eno, arg=arg, opt=opt, ext0=ext0, ext1=ext1)
        return emsg["E99"].format(eno=eno, arg=arg, opt=opt, ext0=ext0, ext1=ext1)

    @property
    def OPT_(self) -> Dict[str, Opset]:
        """ オプション情報（Dict タイプ）を返す """
        return self.__D_option

    @property
    def params(self) -> List[str]:
        """ 入力されたコマンド引数のリストを返す """
        return self.__params

    @property
    def remain(self) -> List[str]:
        """ 残りのコマンドラインを返す """
        return self.__remain

    @property
    def is_error(self) -> bool:
        """ 解析エラーで中断時、Trueになる """
        return self.__error

    def get_errormessage(self, level: int = 0) -> str:
        """ 解析エラーが生じた時のエラーメッセージを返す。
            level=0、1(追加メッセージ含む)、以下もしかしたら追加予定
        """
        __message = self.__error_message(**self.__error_reason)
        if level >= 1 and self.__additional_emsg:
            __message += "\n-- " + self.__additional_emsg
        return __message

    # cl改用★★★
    @property
    def option_attrs(self) -> List[str]:
        """ オプション属性リストを取得する """
        return self.__options

    def get_optionlist(self) -> List[List[str]]:
        """ オプション設定一覧を取得する """
        optionlist: List[List[str]] = []

        for opt in self.option_attrs:
            op = getattr(self, opt)
            soption = ""
            loption = ""
            for s in op.s_options:
                soption += self.__option_string_prefix + s + ', '
            for s in op.l_options:
                loption += self.__option_string_prefix * 2 + s + ', '

            option = (soption + loption).rstrip(', ')
            if op.atype:
                option += " " + op.acomment

            optionlist.append([option, ": " + op.comment])
        return optionlist

    def show_definitionlist(self) -> None:
        """ オプション設定一覧を表示する（デバッグ／ユーティリティ用） """
        for opt in self.option_attrs:
            op = getattr(self, opt)
            print(opt)
            print(f'    s_options = {op.s_options}')
            print(f'    l_options = {op.l_options}')
            print(f'    comment = [{op.comment}], acomment = [{op.acomment}]')
            print(f'    atype = {op.atype}')

    def __show_template(self, options: Union[List[str], Dict[str, Opset]]):
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
                op = getattr(self, opt)
                __show_one(opt, op)
        elif type(options) is dict:
            for opt in options.keys():
                __show_one(f'OPT_["{opt}"]', self.OPT_[opt])

    def show_result(self) -> None:
        """ オプション解析結果一覧を表示する（デバッグ用） """
        for opt in self.option_attrs:
            op = getattr(self, opt)
            strvalue = ""
            if op.atype:
                strvalue = str(op.value)
                if type(op.value) is str:
                    strvalue = "'"+strvalue+"'"     # 文字列(str)なら''で囲って表示する
            print(opt.ljust(12),
                  f"=> {str(op.isEnable).ljust(5)}  {strvalue}")

    @staticmethod
    def show_errormessage() -> None:
        """ 解析エラーメッセージ一覧を表示する（デバッグ用） """
        for eno in emsg:
            print(Parse.__error_message(eno,
                        arg="<ARG>", opt="<OPT>", ext0="<EXT0>", ext1="<EXT1>"))


# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    class Color(IntFlag):
        RED = auto()
        GREEN = auto()
        BLUE = auto()
        PURPLE = RED | GREEN
        WHITE = RED | GREEN | BLUE

    args = sys.argv
    if len(args) <= 1:
        args = 'this.py -al BLUE|RED|GREEN ABC --display 1024x0X40 --exp -ar ---# 0.5 --ext 0x4a4f'.split()
        # args = 'this.py -al BLUE|RED|GREEN ABC --display 1024x0X40 --exp -ar 0.5 --ext 0x4a4f'.split()
        # args = 'this.py -al ---#'.split()
        pass

    # cl_parse 呼び出し用のオプション定義
    options = [
            ["help", "-h, -q , --sdf, --help", "使い方を表示する", None],
            ["all", "-a, --all", "すべて出力"],
            ["color", "-c, --color, -l", "表示色//<color>", Color],
            ["OPT_size", " --size, --display", "表示サイズを指定する//<縦x横>",
                sepalate_items(type=int_literal, sep='x', count=2)],
            ["OPT_ratio", "-r,--ratio", "比率を指定する//<比率>", float],
            ["extend", "-x, --extend ", "特別な奴"],
            ["expect", "-e, --expect", "紛らわしい奴"],
    ]

    # cl_parse 呼び出し（解析実行）
    op = Parse(options, args, debug=True)

    # 解析エラー時の処理は自前で行う
    if op.is_error:
        print(op.get_errormessage(1), file=sys.stderr)
        print("オプション一覧", file=sys.stderr)
        tabprint(op.get_optionlist(), [22, 4], file=sys.stderr)
        exit(1)

    # help情報の表示も自前
    if op.OPT_help.isEnable:
        print("使い方を表示する。")
        tabprint(op.get_optionlist(), [22, 4])
        exit()

    # ここから自分のプログラム
    if op.OPT_all.isEnable:
        print("-a, --all : すべて出力、が指定されました。")

    if op.OPT_["color"].isEnable:
        print('OPT_["color"] is Enable,', f'value = {op.OPT_["color"].value}')

    if op.OPT_size.isEnable:     # type: ignore
        print(f"-s, --size : 表示サイズ、が指定されました。size={repr(op.OPT_size.value)}")     # type: ignore


    if op.OPT_ratio.isEnable:
        print(f"-r, --ratio : 比率を指定する、が指定されました。ratio={repr(op.OPT_ratio.value)}")

    if op.OPT_["OPT_ratio"].isEnable:
        print(f"-r, --ratio : 比率を指定する、が指定されました。ratio={repr(op.OPT_['OPT_ratio'].value)}")

    if op.OPT_extend.isEnable:
        print("-x, --extend : 特別な奴、が指定されました。")

    if op.OPT_expect.isEnable:
        print("-e, --expect : 紛らわしい奴、が指定されました。")
