#!/usr/bin/env python3
# -------------------------------------------------------------
# 簡易コマンドラインパーサー cl_parse改の途中 2021/12/18 by te.
# -------------------------------------------------------------
import sys
import glob
import pathlib
import platform
from datetime import datetime as dt
from enum import Enum, EnumMeta, Flag, IntFlag, auto
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, TextIO, Tuple


# # -------------------------------------------------------------
# # 日本語混じり文字列を整形するクラスの一部（汎用）
# # 以下の関数で使っているだけなので、要らなかったら両方削ってください
# # ->  show_optionslist() オプション設定一覧を表示する（デバッグ用）
# # -------------------------------------------------------------
# class Wstr(str):
#     def width(self) -> int:
#         """ 日本語混じり文字列の表示幅を取得する
#         """
#         len = 0
#         for c in self:
#             len += 2 if unicodedata.east_asian_width(c) in ('F', 'W', 'A') else 1
#         return len

#     def ljust(self, __width: int, __fillchar: str = ...) -> 'Wstr':     # type: ignore ^^;
#         """ 日本語混じり文字列を、左寄せ文字詰めする
#             （str.ljust() のワイド文字対応版）
#         """
#         __fillchar = ' ' if __fillchar == Ellipsis else __fillchar[0:1]
#         return Wstr(self + __fillchar*(__width - self.width()))

#     def tjust(self, tab0: int = 16, tabn: int = 8) -> 'Wstr':
#         """ 日本語混じり文字列を、タブサイズに左寄せ文字詰めする
#             （tab0:最初のタブサイズ、tabn:その後のタブサイズ）
#         """
#         num = (self.width() - tab0) // tabn + 1
#         return self.ljust(tab0 + tabn * (num if num > 0 else 0))


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
# シーケンスから要素を取り出す勝手ストリーム（一応汎用）
# -------------------------------------------------------------
class F_Stream():
    def __init__(self, sblock: Sequence[Any]) -> None:
        """ シーケンスを１要素ずつ取り出すためのクラス
            （先読み機能あり）
        """
        self.buf = sblock
        self.pos: int = 0
        self.len = len(sblock)

    def stream(self) -> Iterator[Any]:
        """ ストリームから１要素ずつ取り出す（これだけイテレータ）
        """
        while self.pos < self.len:
            blk = self.buf[self.pos]
            self.pos += 1
            yield blk

    def getone(self) -> Sequence[Any]:
        """ ストリームから１要素を取り出す。無ければ空要素
        """
        blk = self.buf[self.pos:self.pos+1]
        if self.pos < self.len:
            self.pos += 1
        if blk:
            return blk[0]
        return blk

    def getn(self, num: int) -> Sequence[Any]:
        """ ストリームからn要素を取り出す。無ければ空要素
            （注意：getone() != getn(1) かもしれない？）
        """
        if num <= 0:
            num = 1
        blk = self.buf[self.pos: self.pos + num]
        self.pos += num
        if self.pos > self.len:
            self.pos = self.len
        return blk

    def getall(self) -> Sequence[Any]:
        """ ストリームの残りの全ての要素を取り出す。無ければ空要素
        """
        all = self.buf[self.pos:]
        self.pos = self.len
        return all

    def peekone(self) -> Sequence[Any]:
        """ ストリームの次の１要素を見る。無ければ空要素
            （ポインタを進めない）
        """
        blk = self.buf[self.pos:self.pos+1]
        if blk:
            return blk[0]
        return blk

    def peekall(self) -> Sequence[Any]:
        """ ストリームの残りの全ての要素を見る。無ければ空要素
            （ポインタを進めない）
        """
        all = self.buf[self.pos:]
        return all


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
# -------------------------------------------------------------
def file_expand(args: List[str]) -> List[str]:
    """ リスト中の、”@<ファイル名>" の要素を展開する
    """
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
    """ Instant Closure クラス
    """
    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any):
        """ 普通の関数(func)をクロージャーとして埋め込むクラス
        """
        """ 仕様は functools.partial() とほとんど同じ（多分）だけど、
            埋め込んだ functionを呼び出すときの位置引数の順番が逆
            （呼び出し時の引数が先、埋め込んだ引数が後）
        """
        self.args = args
        self.kwargs = kwargs
        self.func = func

    def __call__(self, *args2: Any, **kwargs2: Any):
        return self.func(*args2, *self.args, **{**self.kwargs, **kwargs2})

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} {repr(self.func)} {repr(self.args)} {repr(self.kwargs)}'


class Mu2:
    """ Instant Closure ^2 クラス
    """
    def __init__(self, func: Callable[..., Any], func2: Callable[..., Any], *args: Any, **kwargs: Any):
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
        return f'{self.__class__.__name__} {repr(self.func)} {repr(self.func2)} {repr(self.args)} {repr(self.kwargs)}'


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
        raise ValueError(f"sepalate items count error. required {count} / detected {len(motos)} at arg=[{moto}]")
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
    "E11": "{eno}: illegal argument for option {arg}",
    "E12": "{eno}: missing argument for option {arg}",
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
# 定義されたオプションセット格納用クラス
# -----------------------------------------------------
# class Opset:
#     def __init__(self, comment: str, acomment: str, atype: Any) -> None:
#         """ オプションセット格納用クラス """
#         self.__comment = comment        # コメント
#         self.__atype = atype            # オプション引数のタイプ
#         self.__acomment = acomment      # オプション引数のコメント

#         self.isEnable: bool = False     # オプション有効/無効
#         self.value: Any = None          # オプション引数

#     @property
#     def comment(self) -> str:
#         return self.__comment

#     @property
#     def acomment(self) -> Any:
#         return self.__acomment

#     @property
#     def atype(self) -> Any:
#         return self.__atype


# -----------------------------------------------------
# cl改用★★★
# 定義されたオプションセット格納用クラス
# -----------------------------------------------------
class Opset2:
    def __init__(self, l_options: List[str], s_options: List[str], comment: str, acomment: str, atype: Any) -> None:
        """ オプションセット格納用クラス """
        self.__l_options = l_options
        self.__s_options = s_options
        self.__comment = comment        # コメント
        self.__acomment = acomment      # オプション引数のコメント
        self.__atype = atype            # オプション引数のタイプ

        self.isEnable: bool = False     # オプション有効/無効
        self.value: Any = None          # オプション引数

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
                 option_name_prefix: str = "OPT_",
                 option_string_prefix: str = "-",
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

        self.__debugmode = ""           # デバッグモードを格納

        # ユーザー定義のオプションセット格納用 -------------------------
        # self.ops: Dict[str, Opset] = {}         # 1文字オプション: オプションセット
        # self.__stol: Dict[str, str] = {}        # 1文字オプション: ロング名オプション

        # cl改★★★
        self.__options: List[str] = []          # 設定されたオプション属性リスト
        self.__ltoOPS: Dict[str, str] = {}
        self.__stoOPS: Dict[str, str] = {}

        # オプションセット読み込み処理実行
        self.__set_options(options)

        # ロング名オプション: 1文字オプション
        # self.__ltos = {v: k for k, v in self.__stol.items()}
        # self.__s_options = list(self.__stol.keys())     # 1文字オプション一覧
        # self.__l_options = list(self.__ltos.keys())     # ロング名オプション一覧

        self.__s_options = list(self.__stoOPS.keys())     # 1文字オプション一覧
        print(f'{self.__s_options=}')
        self.__l_options = list(self.__ltoOPS.keys())     # ロング名オプション一覧
        print(f'{self.__l_options=}')

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
            print(f"__debugmode [{self.__debugmode}]")
            if self.__debugmode not in ["#", "#0", "#1", "#2"]:
                print("入力引数一覧                 [#], [#1]")
                print("オプション設定一覧           [#], [#0]")
                print("オプション解析結果一覧       [#], [#1], [#2]")
                print("コマンド引数一覧             [#], [#1], [#2]")
                print("残りの入力引数一覧（あれば） [#], [#1], [#2]")
                print("解析エラー情報               [#], [#1], [#2]")

            if self.__debugmode in ["#", "#1"]:
                print("入力引数一覧")
                for i, arg in enumerate(self.__args):
                    print(f"arg[{i}]: {arg}")
                print()
            if self.__debugmode in ["#", "#0"]:
                print("オプション設定一覧")
                self.show_definitionlist()
                print()
            if self.__debugmode in ["#", "#1", "#2"]:
                print("オプション解析結果一覧")
                self.show_result()
                print()
            if self.__debugmode in ["#", "#1", "#2"]:
                print("コマンド引数一覧")
                for i, param in enumerate(self.params):
                    print(f"arg[{i}]: {param}")
                if self.remain:
                    print()
                    print("残りの入力引数一覧")
                    for i, param in enumerate(self.remain):
                        print(f"arg[{i}]: {param}")
                print()
            if self.__debugmode in ["#", "#1", "#2"]:
                if self.is_error:
                    print("解析エラーあり")
                    print(self.get_errormessage(2))
                else:
                    print("解析エラーなし")
                print()

            input('Hit any key for start program:')
            print("-------- START PROGRAM --------")

    # -----------------------------------------------------
    # オプションセット読み込み処理
    # -----------------------------------------------------
    def __set_options(self, options: List[List[Any]]) -> None:
        """ オプションセットを読み込む
        """
        for iopset in options:
            iopset = (iopset + [None] * (4 - len(iopset)))[0:4]

            # self.__option_name_prefix = "OPT_"
            # opt_prefix = ""
            # self.__option_string_prefix = '-'

            import keyword

            # オプション名の処理 --------------------------------
            opt_name = iopset[0]
            if not opt_name.startswith(self.__option_name_prefix):     # 頭に prefixが付いてなかったら
                opt_name = self.__option_name_prefix + opt_name            # 頭に prefixを付加
            print(opt_name)

            # Python変数としての文字種チェック
            assert opt_name.isidentifier() and (not keyword.iskeyword(opt_name)),\
                f'illegal option name [{opt_name}]'
            # 重複チェック
            assert opt_name not in self.__options,\
                f'duplicated option name [{opt_name}]'

            # オプション文字列の処理 ----------------------------
            s_options: List[str] = []
            l_options: List[str] = []
            # option_strings = iopset[1]
            option_strings = list(map(lambda x: x.strip(), iopset[1].split(',')))
            print(option_strings)
            for s in option_strings:
                count = count_prefix(s, self.__option_string_prefix, max_count=2)
                if count == 1:
                    s_options.append(s[1:])
                elif count >= 2:
                    l_options.append(s[2:])
                else:
                    assert True, \
                        f'illegal option string [{s}]'

            print(s_options)
            print(l_options)

            # iopset[0] : 1文字オプション、iopset[1] : ロング名オプション
            assert isinstance(iopset[1], str) and isinstance(iopset[2], str), \
                f'illegal type of "option" {iopset}'

            # iopset[2] : コメント//オプション引数のコメント
            assert isinstance(iopset[2], str), \
                f'illegal type of "comment//option-argument comment" {iopset}'
            icomment, ioacomment = split2(iopset[2], self.__commentsp)
            ioacomment = "" if ioacomment is None else ioacomment

            # iopset[3] : オプション引数のタイプ（存在しなければ None）
            # ioatype = iopset[3] if len(iopset) > 3 else None
            ioatype = iopset[3]
            assert ioatype is None or callable(ioatype), \
                f'illegal type of "option-argument type" {iopset}'

            # オプションセット格納（1文字オプション: オプションセット）
            # assert iopset[0] not in self.ops.keys(), \
            #     f'double definition of option [{iopset[0]}]'
            # self.ops[iopset[0]] = Opset(icomment, ioacomment, ioatype)
            # assert iopset[1] not in self.__stol.values(), \
            #     f'double definition of option [{iopset[1]}]'
            # self.__stol[iopset[0]] = iopset[1]  # 1文字オプション: ロング名オプションに追加

            # cl改用★★★
            # opt_name = "OPT_" + iopset[0]
            setattr(self, opt_name, Opset2(l_options, s_options, icomment, ioacomment, ioatype))
            self.__options.append(opt_name)
            for s in l_options:
                self.__ltoOPS[s] = opt_name
            for s in s_options:
                self.__stoOPS[s] = opt_name

            # self.__ops = None

    # -----------------------------------------------------
    # コマンドライン解析の本文
    # -----------------------------------------------------
    def __parse(self) -> None:
        """ コマンドラインを解析する
        """
        t = CheckTurn()         # ターンチェック用

        if self.__debug:        # デバッグモード指定を取得
            wargs: List[str] = []
            for item in self.__args:
                if item.startswith("@@#"):
                    # if item in ["#", "#0", "#1", "#2"]:
                    self.__debugmode = item[2:]
                else:
                    wargs += [item]
            self.__args = wargs

        if self.__filexpand:    # ファイル展開
            try:
                self.__args = file_expand(self.__args)
            except Exception as e:
                # print(e)
                self.__set_error_reason('E01', str(e))
                return

        if isWin and self.__winexpand:  # Windows用、ワイルドカード展開
            self.__args = _wArgs(self.__args)

        # 解析本文
        b_args = F_Stream(self.__args)
        for arg in b_args.stream():
            jst = F_Stream(arg)
            if arg.startswith("-"):
                if arg.startswith("--"):    # ロング名オプションブロック（頭が「--」） ----------------
                    jst.getn(2)
                    if jst.peekone() is None:   # 「--」のみのブロック

                        if t.checkTurn(Turn.ARG):   # ターンチェック（コマンド引数）
                            if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.ARG)) or \
                               (self.__smode == Smode.ARGFIRST and t.getTimes(Turn.OPT)):
                                break
                        if wparam := b_args.getone():
                            self.__params.append(str(wparam))   # 次のブロックは無条件に「コマンド引数」
                            continue

                    if t.checkTurn(Turn.OPT):   # ターンチェック（オプション）
                        if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.OPT)) or \
                           (self.__smode == Smode.OPTFIRST and t.getTimes(Turn.ARG)):
                            break

                    opt, oarg = split2(str(jst.getall()), '=')  # オプション名、引数を取得
                    opt = self.__complete_l_option(opt)
                    if opt:     # 正しいロング名オプション ----------
                        __ops = getattr(self, self.__ltoOPS[opt])
                        __ops.isEnable = True

                        # opt = self.s_option(opt)
                        # self.ops[opt].isEnable = True
                        # if self.atype(opt):     # オプション引数が必要 ---------
                        if __ops.atype:     # オプション引数が必要 ---------
                            harg = arg  # for 'E11' error_reason
                            if oarg is None:                   # オプション引数無し（= 以降が無い）
                                oarg = b_args.getone()     # 次のブロックをオプション引数として取得
                                harg = harg + " " + oarg  # for 'E11' error_reason
                                if not oarg:               # それも無ければエラー
                                    self.__set_error_reason('E12', arg=arg)
                                    return
                            # ret = self.__set_value(opt, oarg)   # オプション引数を格納
                            ret = self.__set_value2(__ops, oarg)   # オプション引数を格納
                            if not ret:     # オプション引数格納（変換）エラー
                                self.__set_error_reason('E11', arg=harg)
                                return
                        else:                   # オプション引数が不要 ---------
                            if oarg:                     # オプション引数が不要なのに引数あり
                                self.__set_error_reason('E13', arg=arg)
                                return
                    else:       # ロング名オプションが正しくない ----
                        self.__set_error_reason('E14', arg=arg)
                        return

                else:                       # 1文字オプションブロック（頭が「-」） ------------------
                    if t.checkTurn(Turn.OPT):   # ターンチェック（オプション）
                        if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.OPT)) or \
                           (self.__smode == Smode.OPTFIRST and t.getTimes(Turn.ARG)):
                            break
                    jst.getone()
                    # jst.getch()
                    for opt in jst.stream():
                        if opt in self.__s_options:   # 正しい1文字オプション -----------
                            __ops = getattr(self, self.__stoOPS[opt])
                            __ops.isEnable = True

                            # self.ops[opt].isEnable = True
                            # if self.atype(opt):             # オプション引数が必要か
                            if __ops.atype:             # オプション引数が必要か
                                oparg = jst.getall()    # 後続文字列からオプション引数を取得
                                harg = arg  # for 'E22' error_reason
                                if not oparg:           # 無ければ、
                                    oparg = str(b_args.getone())     # 次のブロックを取得
                                    harg = harg + " " + oparg   # for 'E22' error_reason
                                    if not oparg:               # それも無ければエラー
                                        self.__set_error_reason('E21', opt=opt, arg=arg)
                                        return
                                # ret = self.__set_value(opt, oparg)  # オプション引数を格納
                                ret = self.__set_value2(__ops, oparg)  # オプション引数を格納
                                if not ret:     # オプション引数格納（変換）エラー
                                    self.__set_error_reason('E22', opt=opt, arg=harg)
                                    return
                        else:                       # 1文字オプションが正しくない ------
                            self.__set_error_reason('E23', opt=opt, arg=arg)
                            return

            else:   # コマンド引数ブロック（頭が「―」以外） -----------------------------------------
                if t.checkTurn(Turn.ARG):   # ターンチェック（コマンド引数）
                    if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.ARG)) or \
                       (self.__smode == Smode.ARGFIRST and t.getTimes(Turn.OPT)):
                        break
                self.__params.append(arg)
        else:   # 全終了
            self.__error = False
            return

        # 途中終了
        self.__remain = [arg] + list(b_args.getall())       # 残りのコマンドラインを格納
        self.__error = False
        return

    # -----------------------------------------------------
    # 内部処理
    # -----------------------------------------------------
    # def __set_value(self, option: str, optarg: Any) -> bool:
    #     """ このオプションのオプション引数を格納する。エラー時には Falseを返す
    #     """
    #     atype = self.atype(option)
    #     try:
    #         # 「str」の時はそのまま格納
    #         if atype is str:
    #             self.ops[self.s_option(option)].value = optarg

    #         # Enum、Flag類
    #         elif isinstance(atype, EnumMeta):
    #             self.ops[self.s_option(option)].value = cnv_enum(atype, optarg)

    #         # 直接変換呼び出しできるもの
    #         else:
    #             self.ops[self.s_option(option)].value = atype(optarg)

    #         return True

    #     except ValueError as e:     # 変換エラー
    #         self.__additional_emsg = str(e)
    #         return False

    # @staticmethod
    def __set_value2(self, __ops: 'Parse', optarg: Any) -> bool:
        """ このオプションのオプション引数を格納する。エラー時には Falseを返す
        """
        atype = __ops.atype
        try:
            # 「str」の時はそのまま格納
            if atype is str:
                __ops.value = optarg

            # Enum、Flag類
            elif isinstance(atype, EnumMeta):
                __ops.value = cnv_enum(atype, optarg)

            # 直接変換呼び出しできるもの
            else:
                __ops.value = atype(optarg)

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
        """ 解析エラーの理由をセットする
        """
        self.__error_reason = {
            "eno": eno, "arg": arg, "opt": opt, "ext0": ext0, "ext1": ext1
        }

    @staticmethod
    def __error_message(eno: str, arg: str = "???", opt: str = "???",
                        ext0: str = "ext0", ext1: str = "ext1") -> str:
        """ 解析エラーメッセージを作成する
        """
        if eno in emsg.keys():
            return emsg[eno].format(eno=eno, arg=arg, opt=opt, ext0=ext0, ext1=ext1)
        return emsg["E99"].format(eno=eno, arg=arg, opt=opt, ext0=ext0, ext1=ext1)

    # -----------------------------------------------------
    # ユーザ提供メソッド
    # -----------------------------------------------------
    # def s_option(self, option: str) -> str:
    #     """ オプション -> 1文字オプションに変換する
    #     """
    #     if option in self.l_options:            # 引数のoptionがロング名オプションだったら、
    #         return self.__ltos[option]          # 1文字オプションを返す
    #     elif option in self.s_options:          # 1文字オプションだったら、
    #         return option                       # そのまま返す
    #     assert False, f'illegal option [{option}]'
    #     return ""

    # def l_option(self, option: str) -> str:
    #     """ オプション -> ロング名オプションに変換する
    #     """
    #     if option in self.s_options:            # 引数のoptionが１文字オプションだったら、
    #         return self.__stol[option]          # ロング名オプションを返す
    #     elif option in self.l_options:          # 引数のoptionがロング名オプションだったら、
    #         return option                       # そのまま返す
    #     assert False, f'illegal option [{option}]'
    #     return ""

    # @property
    # def l_options(self) -> List[str]:
    #     """ ロング名オプションの一覧 """
    #     return self.__l_options

    # @property
    # def s_options(self) -> List[str]:
    #     """ 一文字オプションの一覧 """
    #     return self.__s_options

    # @property
    # def options(self) -> List[str]:
    #     """ すべてのオプションの一覧 """
    #     return self.l_options + self.s_options

    # def isEnable(self, option: str) -> bool:
    #     """ このオプションが有効かどうか（指定されたかどうか）を返す """
    #     return self.ops[self.s_option(option)].isEnable

    # def comment(self, option: str) -> str:
    #     """ このオプションのコメントを返す """
    #     return self.ops[self.s_option(option)].comment

    # def atype(self, option: str) -> Any:
    #     """ このオプションのオプション引数タイプを返す """
    #     return self.ops[self.s_option(option)].atype

    # def value(self, option: str) -> Any:
    #     """ このオプションのオプション引数を返す """
    #     return self.ops[self.s_option(option)].value

    # def acomment(self, option: str) -> str:
    #     """ このオプションのオプション引数のコメントを返す """
    #     return self.ops[self.s_option(option)].acomment

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
        return self.__options

    # -----------------------------------------------------
    # ユーティリティ関数
    # -----------------------------------------------------
    # def show_optionlist(self, tab0: int = 16, tabn: int = 8, file: TextIO = sys.stdout) -> None:
    #     """ オプション設定一覧を表示する
    #     """
    #     # for opt in self.s_options:
    #     for opt in self.option_attrs:
    #         op = getattr(self, opt)
    #         soption = ""
    #         loption = ""
    #         for s in op.s_options:
    #             soption += self.__option_string_prefix + s + ', '
    #         for s in op.l_options:
    #             loption += self.__option_string_prefix * 2 + s + ', '


    #     #     soption = f"-{opt}, " if len(opt) < 2 else ""
    #     #     loption = "--" + self.l_option(opt)
    #         option = (soption + loption).rstrip(', ')
    #         if op.atype:
    #             option += " " + op.acomment
    #         print(Wstr(option).tjust(tab0, tabn) + f": {op.comment}", file=file)

    #     # print()
    #     # for opt in self.option_attrs:
    #     #     op = getattr(self, opt)
    #     #     print(opt)
    #     #     print(f'    s_options = {op.s_options}')
    #     #     print(f'    l_options = {op.l_options}')
    #     #     print(f'    comment = [{op.comment}], acomment = [{op.acomment}]')
    #     #     print(f'    atype = {op.atype}')


    def get_optionlist(self) -> List[List[str]]:
        """ オプション設定一覧を取得する
        """
        # for opt in self.s_options:
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
        """ オプション設定一覧を表示する
        """
        # for opt in self.s_options:

        #     soption = f"-{opt}, " if len(opt) < 2 else ""
        #     loption = "--" + self.l_option(opt)
        #     if self.atype(opt):
        #         loption += " " + self.acomment(opt)
        #     option = soption + loption
        #     print(Wstr(option).tjust(tab0, tabn) + f": {self.comment(opt)}", file=file)

        # print()
        for opt in self.option_attrs:
            op = getattr(self, opt)
            print(opt)
            print(f'    s_options = {op.s_options}')
            print(f'    l_options = {op.l_options}')
            print(f'    comment = [{op.comment}], acomment = [{op.acomment}]')
            print(f'    atype = {op.atype}')

    def show_result(self) -> None:
        """ オプション解析結果一覧を表示する（デバッグ用）
        """
        # for opt in self.s_options:
        #     strvalue = str(self.value(opt))
        #     if type(self.value(opt)) is str:
        #         strvalue = "'"+strvalue+"'"     # 文字列(str)なら''で囲って表示する
        #     print(f"-{opt}, --{self.l_option(opt)}".ljust(14),
        #           f"=> {str(self.isEnable(opt)).ljust(5)}  {strvalue}")

        # print()
        for opt in self.option_attrs:
            op = getattr(self, opt)
            strvalue = str(op.value)
            if type(op.value) is str:
                strvalue = "'"+strvalue+"'"     # 文字列(str)なら''で囲って表示する
            print(opt.ljust(12),
                  f"=> {str(op.isEnable).ljust(5)}  {strvalue}")

    @staticmethod
    def show_errormessage() -> None:
        """ 解析エラーメッセージ一覧を表示する（デバッグ用）
        """
        for eno in emsg:
            print(Parse.__error_message(eno,
                        arg="<ARG>", opt="<OPT>", ext0="<EXT0>", ext1="<EXT1>"))


# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    import tprint

    class Color(IntFlag):
        RED = auto()
        GREEN = auto()
        BLUE = auto()
        PURPLE = RED | GREEN
        WHITE = RED | GREEN | BLUE

    args = 'this.py -hal BLUE|RED|GREEN ABC --display 1024x0X40 --exp -ar @@# 0.5 --ext 0x4a4f'.split()
    # args = sys.argv

    # cl_parse 呼び出し用のオプション定義
    options = [
            ["help", "-h, -q , --sdf, --help","使い方を表示する", None],
            ["all", "-a, --all", "すべて出力"],
            ["color", "-c, --color, -l", "表示色//<color>", Color],
            ["OPT_size", " --size, --display", "表示サイズを指定する//<縦x横>",
                sepalate_items(type=int_literal, sep='x', count=0)],
            ["OPT_ratio", "-r,--ratio", "比率を指定する//<比率>", float],
            ["extend", "-x, --extend ", "特別な奴"],
            ["expect", "-e, --expect", "紛らわしい奴"],
    ]

    # cl_parse 呼び出し（解析実行）
    op = Parse(options, args, debug=True)

    print(op.option_attrs)

    # 解析エラー時の処理は自前で行う
    if op.is_error:
        print(op.get_errormessage(1), file=sys.stderr)
        print("オプション一覧", file=sys.stderr)
        # op.show_optionlist(tab0=24, file=sys.stderr)
        tprint.tprint(op.get_optionlist(), [22, 4], tabscale=True, file=sys.stderr)
        exit(1)

    # help情報の表示も自前
    if op.OPT_help.isEnable:
        print("使い方を表示する。")
        # op.show_optionlist(tab0=24)
        tprint.tprint(op.get_optionlist(), [22, 4], tabscale=True)
        exit()

    # ここから自分のプログラム
    # if op.isEnable("all"):
    #     print("-a, --all : すべて出力、が指定されました。")

    if op.OPT_all.isEnable:
        print("-a, --all : すべて出力、が指定されましたよ。")

    if op.OPT_color.isEnable:
        print(f"-c, --color : 表示色、が指定されましたよ。color={repr(op.OPT_color.value)}")

    # if op.OPT_size.isEnable:
    #     print(f"-s, --size : 表示サイズ、が指定されましたよ。size={repr(op.OPT_size.value)}")

    if op.OPT_size.isEnable:     # type: ignore
        print(f"-s, --size : 表示サイズ、が指定されましたよ。size={repr(op.OPT_size.value)}")     # type: ignore

    if op.OPT_ratio.isEnable:
        print(f"-r, --ratio : 比率を指定する、が指定されましたよ。ratio={repr(op.OPT_ratio.value)}")

    if op.OPT_extend.isEnable:
        print("-x, --extend : 特別な奴、が指定されましたよ。")

    if op.OPT_expect.isEnable:
        print("-e, --expect : 紛らわしい奴、が指定されましたよ。")
