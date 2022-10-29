"""
## コマンドラインパーサー cl_parse改の途中      2022/3/23 by te.
"""

# -------------------------------------------------------------
# コマンドラインパーサー cl_parse改の途中      2022/3/23 by te.
# -------------------------------------------------------------
from __future__ import annotations
import sys
import glob
import pathlib
import platform
from enum import Enum, EnumMeta, Flag, IntFlag, auto
from typing import Any, Optional, TextIO, Sequence, Union
from collections.abc import Iterator, Callable, Iterable


exist_debugmodule = False
# -------------------------------------------------------------
# デバッグ用モジュール（cl_parse_debug）読み込み
# モジュールが不要であれば、下の節を削除してください。
# -------------------------------------------------------------
sys.path.append(str(pathlib.Path(__file__).parent))
try:
    import cl_parse_debugmodule as cld
    exist_debugmodule = True

except ModuleNotFoundError:
    exist_debugmodule = False


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
def _eter_list(anylist: list[Any], eter: Any = ...) -> Iterator[Any]:
    ''' listの要素を無限に繰り返す Iterator '''
    if eter == Ellipsis:    # eter省略時は
        eter = anylist[-1]      # 最後の要素を繰り返す
    for num in anylist:     # 通常の繰り返し
        yield num
    while True:             # 以降無限の繰り返し
        yield eter


def _tab_expand(line: list[str]) -> list[str]:
    ''' リスト中の文字列を、tab により分割、要素に展開する '''
    ret: list[str] = []
    for text in line:
        ret += text.split("\t")
    return ret


def _linefolding_list(line: list[str]) -> list[list[str]]:
    ''' 改行コードを含む文字列リストを改行して、行数分の文字列リストのリストを返す '''
    ls = [text.split('\n') for text in line]    # 改行して複数行リストにする
    lc = max([len(item) for item in ls])        # 最大行数を取得
    return [list(ll) for ll in zip(*[item + [""] * (lc - len(item)) for item in ls])]   # 正規化して転置


def _tablist(line: list[str], tablist: list[int]) -> list[int]:
    ''' 複数行の文字列リストから、単純揃え用のタブ・リストを作成する
    '''
    def _addtab(width: int) -> int:     # 個々のtext幅の、tab揃えの計算
        w = 0
        while w <= width:
            w += next(tabstop)
        return w

    tabstop = _eter_list(tablist)
    return [_addtab(Wstr(text).width()) for text in line]


def _makelines(line: list[str], tablist: list[int]) -> list[str]:
    ''' １行の文字列リストから、
        改行をいれて複数行になった、表示用にタブを揃えた文字列（１行分）のリストを作成する
    '''
    table = _linefolding_list(line)
    tabtable = [_tablist(text, tablist) for text in table]
    mtl = [max(mm) for mm in [ll for ll in zip(*tabtable)]]
    ret: list[str] = []
    for line in table:
        ret.append(''.join([Wstr(text).ljust(tab) for text, tab in zip(line, mtl)]).rstrip())
    return ret


def tabprint(lines: list[str], tablist: list[int] = [8],
             file: TextIO = sys.stdout):
    ''' 単純タブ揃え表示（table中の各lineの、各項目を直近のタブに揃えて表示する） '''
    for text in lines:
        line = _tab_expand([text])
        for text in _makelines(line, tablist):
            print(text, file=file)


# -------------------------------------------------------------
# こまかいの（一応汎用）
# -------------------------------------------------------------
def split2(text: str, sp: str) -> tuple[str, Optional[str]]:
    """ 文字列をspで２分割してタプルで返す """
    """ セパレータ(sp) 以降が無ければ、ret[1]は空文字、
        セパレータ(sp) が存在しなければ、ret[1]は None
    """
    ret: list[Any] = text.split(sp, 1)
    return ret[0], ret[1] if len(ret) > 1 else None


def count_prefix(text: str, prefix_char: str, max_count: int = 0) -> int:
    ''' プリフィックス文字の数を返す（max_count > 0 のとき、max_countが最大値） '''
    count = 0
    iter_text = iter(text[0:len(text) if max_count <= 0 else max_count])
    while next(iter_text, None) == prefix_char:
        count += 1
    return count


class NamedTupleLike:
    def __init__(self, values: tuple[Any, ...] | Any, attr_names: Sequence[str]) -> None:
        ''' Tuple を NamedTuple みたいなものに変換する。注意！ attrは全部mutable。
            足りないvalue は None、余った分は overflowに格納
        '''
        self.overflow: Any = None       # valuesのうち、余った分が入る
        self.__attrs: list[str] = []    # 属性名のリスト
        if isinstance(values, str) or not isinstance(values, Sequence):
            values = (values, )
        ivalue = iter(values)
        for name in attr_names:
            setattr(self, name, next(ivalue, None))
            self.__attrs.append(name)

        if len(values) > len(attr_names):
            self.overflow = values[len(attr_names):]

    def __str__(self) -> str:
        strs: list[str] = []
        for name in self.__attrs:
            strs.append(name + "=" + str(getattr(self, name)))
        return "\n".join(strs)


# -------------------------------------------------------------
# ターンチェック（一応、汎用クラス）
# -------------------------------------------------------------
class CheckTurn():
    def __init__(self):
        """ ターンをチェックするクラス """
        self.__turn = None                  # 現在のターン
        self.d_turn: dict[Enum, int] = {}   # ターン回数記録用

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


def __getWild(wild: str) -> list[str]:
    """ ホームディレクトリ '~'、ワイルドカードを展開して、リストで返す。
        頭にハイフンが付いているもの、ワイルドカードに展開できないものはそのまま返す
        （その時は、「要素が1つ」のリストになる）
    """
    ret: list[str] = []
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


def _wArgs(__args: list[str]) -> list[str]:
    """ 渡されたリスト中の項目をワイルドカード展開する """
    ret: list[str] = []
    for p in __args:
        ret += __getWild(p)
    return ret


# -------------------------------------------------------------
# ファイル展開モジュール（ほとんど cl_parse専用）
# 使い物になるか（コマンドラインで @xxxx を取得できるか）要検証★★★
# -------------------------------------------------------------
def file_expand(args: list[str]) -> list[str]:
    """ リスト中の、”@<ファイル名>" の要素を展開する """
    ret: list[str] = []
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


# -----------------------------------------------------
# cl_parse 内部使用関数
# -----------------------------------------------------
def cnv_enum(afunc: EnumMeta, ename: str) -> Any:
    """ 列挙型(afunc)の「名前(ename)から、列挙型メンバーを作成する
        （Flag、IntFlagの演算子は | のみ解釈）
    """
    # 型ヒントをどのように書けば良いのか、模索中 ^^;

    wmembers = list(afunc.__members__.keys())
    try:
        if afunc.__base__ is Flag or IntFlag:
            flist = [t.strip() for t in ename.split('|')]
            ret = afunc[flist[0]]
            for t in flist[1:]:
                ret |= afunc[t]
            return ret
        return afunc[ename]

    except KeyError as e:
        raise ValueError(f"option argument {e} must be a member of {wmembers}")


# -----------------------------------------------------
# エラーメッセージのテンプレート
# -----------------------------------------------------
emsg = {
    "N00": "no error",
    "E01": "{eno}: FileNotFoundError at {arg}",
    "E11": "{eno}: argument required for option {arg}",
    "E12": "{eno}: illegal argument specified for option {arg}",
    "E13": "{eno}: unnecessary argument specified for option {arg}",
    "E14": "{eno}: illegal option {arg}",
    "E21": "{eno}: argument required for option {opt} in {arg}",
    "E22": "{eno}: illegal argument specified for option {opt} in {arg}",
    "E23": "{eno}: illegal option {opt} in {arg}",
    "E31": "{eno}: option ({ext0}) and ({ext1}) cannot be specified together",
    "E99": "{eno}: unknown error opt={opt}, arg={arg}, ext0={ext0}, ext1={ext1}",
}


# -----------------------------------------------------
# オプション引数のタイプ
# -----------------------------------------------------
class At(Flag):
    NORMAL = 0
    OPTIONAL = auto()       # オプション引数省略可能
    APPEND = auto()         # オプション引数をリストに格納
    COUNT = auto()


_OATYPE_SET = {
        "OPTIONAL": At.OPTIONAL,
        "APPEND":   At.APPEND,
        "COUNT":    At.COUNT
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
    def __init__(self, l_options: list[str], s_options: list[str],
                 comment: str, acomment: str, afunc: Optional[list[Any]], atype: At) -> None:
        """ オプションセット格納用クラス """
        self.__l_options = l_options
        self.__s_options = s_options
        self.__comment = comment        # コメント
        self.__acomment = acomment      # オプション引数のコメント
        self.__afunc = afunc            # オプション引数の処理タイプ
        self.__atype = atype            # オプション引数のタイプ

        self.__isEnable: bool = False   # オプション有効/無効
        self.__value: Any = None        # オプション引数

    @property
    def l_options(self) -> list[str]:
        return self.__l_options

    @property
    def s_options(self) -> list[str]:
        return self.__s_options

    @property
    def comment(self) -> str:
        return self.__comment

    @property
    def acomment(self) -> Any:
        return self.__acomment

    @property
    def afunc(self) -> Optional[list[Any]]:
        return self.__afunc

    @property
    def atype(self) -> At:
        return self.__atype

    @property
    def isEnable(self) -> bool:
        return self.__isEnable

    def _set_isEnable(self, isenable: bool):
        self.__isEnable = isenable

    @property
    def value(self) -> Any:
        return self.__value

    def _set_value(self, value: Any):
        self.__value = value

    def _store_value(self, value: Any):
        if At.APPEND in self.__atype:
            if self.__value is None:
                self.__value = []
            self.__value.append(value)
        else:
            self.__value = value

    def _count_value(self, value: int):
        if self.__value is None:
            self.__value = 0
        self.__value += value


# -----------------------------------------------------
# パーサー本体
# -----------------------------------------------------
TAction = Union[Optional[str],
                Callable[..., Any],
                Iterable[Union[str, Callable[..., Any]]]
                ]

TOptionset = Union[str,
                   tuple[str],
                   tuple[str, str],
                   tuple[str, str, Optional[str]],
                   tuple[str, str, Optional[str], TAction],
                   ]

TOptions = Iterable[TOptionset]

TExclusiveset = Union[Sequence[str],
                      Sequence[Sequence[str]]
                      ]


class Parse:
    """Parseのドキュメント"""
    def __init__(self,
                 args: list[str],                   # 解析するコマンドライン
                 options: TOptions,                 # オプション情報
                 exclusive: TExclusiveset = [],     # 排他オプションリスト
                 cancelable: bool = False,          # オプションキャンセル可能モード
                 smode: Smode = Smode.NONE,         # 解析モード
                 winexpand: bool = True,            # Windowsで、ワイルドカードを展開するかどうか
                 file_expand: bool = False,         # コマンド引数の @<filename> を展開するかどうか
                 emessage_header: str = "@name",    # エラーメッセージの頭に付けるコマンド名
                 comment_sp: str = '//',            # オプションコメントのセパレータ
                 debug: bool = False,               # デバッグ機能を有効にする
                 option_name_prefix: str = "OPT_",  # オプション属性を生成する時のprefix
                 option_string_prefix: str = "-",   # オプションの前に付ける - とか --
                 ) -> None:
        """ コマンドラインパーサー """

        self.__args = args
        self.__cancelable = cancelable
        self.__smode = smode
        self.__winexpand = winexpand
        self.__filexpand = file_expand
        self.__commentsp = comment_sp
        self.__debug = debug
        self.__option_name_prefix = option_name_prefix
        self.__option_string_prefix = option_string_prefix[0:1]

        self.__debugmode: str = ""              # デバッグモードを格納

        self.__options: list[str] = []          # 設定されたオプション属性リスト
        self.__options_and_comments: list[str] = []          # 設定されたオプション属性リスト
        self.__exclusive: list[set[str]] = []  # 読み込まれた排他リスト
        self.__ltoOPS: dict[str, str] = {}
        self.__stoOPS: dict[str, str] = {}

        # エラーメッセージの頭に付けるプログラム名を格納
        if emessage_header == "@name":
            self.__emessage_header = pathlib.Path(sys.argv[0]).name
        elif emessage_header == "@stem":
            self.__emessage_header = pathlib.Path(sys.argv[0]).stem
        else:
            self.__emessage_header = emessage_header

        # オプション情報（dict タイプ）
        self.__D_option: dict[str, Opset] = {}  # OPT_["option"] で取得する

        # オプションセット読み込み処理実行
        self.__set_options(options)
        # 排他リスト読み込み処理を実行
        if exclusive:
            self.__set_exclusive(exclusive)

        self.__s_options = list(self.__stoOPS.keys())     # 1文字オプション一覧
        self.__l_options = list(self.__ltoOPS.keys())     # ロング名オプション一覧

        # コマンドライン解析結果格納用 ---------------------------------
        self.__params: list[str] = []           # コマンド引数リスト
        self.__error: bool = True               # 解析エラーがあったかどうか
        self.__error_reason: dict[str, str] = {"eno": "N00"}    # エラー理由
        self.__additional_emsg: list[str] = []  # 追加のエラーメッセージ
        self.__remain: list[str] = []           # 解析の残り

        # コマンドライン解析処理実行
        self.__parse()

        if not self.__error:
            # 排他チェック処理実行
            self.__exclusive_check()

        # デバッグモード
        if self.__debugmode and exist_debugmodule:
            cld.show_debug(self, str(self.__debugmode)[1:])

    # -----------------------------------------------------
    # オプションセット読み込み処理
    # -----------------------------------------------------
    def __set_options(self, options: TOptions) -> None:
        """ オプションセットを読み込む """
        def is_optionstringS(text: str) -> bool:
            """ １文字オプション文字列・文字種チェック """
            return text.replace("-", "").replace("_", "").isalnum() or text == "?"

        def is_optionstringL(text: str) -> bool:
            """ ロング名オプション文字列・文字種チェック """
            return len(text) > 0 and\
                text[-1] != "-" and\
                text.translate(str.maketrans("", "", "-_")).isalnum()

        def is_optionname(text: str) -> bool:
            """ オプション名・文字種チェック """
            import keyword
            return text.isidentifier() and (not keyword.iskeyword(text))

        for iopset in options:
            set = NamedTupleLike(iopset, ["opname", "opstrings", "comment", "actions"])

            assert isinstance(set.opname, str), \
                f'illegal type of option name(must be str) {set.opname} in {iopset}'

            # コメント行格納処理 ===============================================
            if set.opname.startswith("#"):
                self.__options_and_comments.append(set.opname)
                continue

            # オプション名の処理 ===============================================
            opt_name = set.opname
            if not opt_name.startswith(self.__option_name_prefix):     # 頭に prefixが付いてなかったら
                opt_name = self.__option_name_prefix + opt_name            # 頭に prefixを付加

            # Python変数としての文字種チェック
            assert is_optionname(opt_name),\
                f'illegal option name [{opt_name}] in {iopset}'
            # 重複チェック
            assert opt_name not in self.__options,\
                f'duplicated option name [{opt_name}] in {iopset}'

            # オプション文字列の処理 ===========================================
            assert isinstance(set.opstrings, str), \
                f'illegal type of option strings(must be str) {set.opstrings} in {iopset}'
            s_options: list[str] = []
            l_options: list[str] = []

            # 定義されたオプション文字列を個々に分割
            option_strings = list(map(lambda x: x.strip(), set.opstrings.split(',')))
            # 一個ずつチェックして格納
            for s in option_strings:
                count = count_prefix(s, self.__option_string_prefix, max_count=0)
                if count == 1:      # 1文字オプション
                    assert is_optionstringS(s[1:]), f'illegal option string [{s}] in {iopset}'
                    s_options.append(s[1:])
                elif count == 2:    # ロング名オプション
                    assert is_optionstringL(s[2:]), f'illegal option string [{s}] in {iopset}'
                    l_options.append(s[2:])
                else:
                    assert False, \
                        f'illegal option string [{s}] in {iopset}'

            # コメント//オプション引数のコメント
            set.comment = set.comment if set.comment else ""    # Noneだったら空文字列
            assert isinstance(set.comment, str), \
                f'illegal type of "comment//option-argument comment" {set.comment} in {iopset}'
            icomment, ioacomment = split2(set.comment, self.__commentsp)
            ioacomment = "" if ioacomment is None else ioacomment

            # アクションタイプの処理 ===========================================
            iatype: At = At.NORMAL
            if set.actions is not None:
                ioafunc: Optional[list[Any]] = []
                if type(set.actions) not in [list, tuple]:
                    set.actions = [set.actions]
                for item in set.actions:
                    assert callable(item) or (item in _OATYPE_SET.keys()), \
                        f'illegal "option/ option argument type" [{item}] in {iopset}'
                    if item in _OATYPE_SET.keys():
                        iatype = iatype | _OATYPE_SET[item]
                    else:
                        ioafunc.append(item)

                    assert At.COUNT == iatype or At.COUNT not in iatype, \
                        f'"COUNT" and other types are exclusive." [{iatype}] in {iopset}'
                    assert At.COUNT not in iatype or not ioafunc, \
                        f'"COUNT" and other functions are exclusive." [{iatype}] in {iopset}'
                if not ioafunc and At.COUNT not in iatype:
                    ioafunc.append(str)
            else:
                ioafunc = None

            # オプション属性を作成 =============================================
            setattr(self, opt_name,
                    Opset(l_options, s_options, icomment, ioacomment, ioafunc, iatype))

            self.__D_option[iopset[0]] = getattr(self, opt_name)     # オプション情報 dictバージョン
            self.__options.append(opt_name)
            self.__options_and_comments.append(opt_name)
            for s in l_options:
                assert s not in self.__ltoOPS.keys(), f'duplicated option string --{s} in {iopset}'
                self.__ltoOPS[s] = opt_name
            for s in s_options:
                assert s not in self.__stoOPS.keys(), f'duplicated option string -{s} in {iopset}'
                self.__stoOPS[s] = opt_name

    # -----------------------------------------------------
    # 排他リスト読み込み処理
    # -----------------------------------------------------
    def __set_exclusive(self, exsv: TExclusiveset):
        """ 排他リスト読み込み処理 """
        optionname_list = self.__D_option.keys()
        if isinstance(exsv[0], str):
            exsv = (exsv, )
    
        for exset in exsv:
            wset: set[str] = set()
            for p in exset:
                assert isinstance(p, str), \
                    f'incollect format in exclusive set {exset}'
                assert p in optionname_list, \
                    f'incollect option name "{p}" in exclusive set {exset}'
                assert p not in wset, \
                    f'option name "{p}" supecified twice in exclusive set {exset}'
                wset.add(p)

            self.__exclusive.append(wset)
        return

    # -----------------------------------------------------
    # 排他チェック処理
    # -----------------------------------------------------
    def __exclusive_check(self) -> None:
        ''' 排他チェック処理
            （オプションの排他セット中、二つ以上 Enableになったらエラー）
        '''
        for wset in self.__exclusive:
            hotseat = ""
            for p in wset:
                if self.OPT_[p].isEnable:
                    if hotseat:
                        self.__set_error_reason(
                            'E31', ext0=self.make_options(self.OPT_[hotseat]),
                            ext1=self.make_options(self.OPT_[p]))
                        self.__error = True
                        return
                    hotseat = p

    # -----------------------------------------------------
    # コマンドライン解析の本文
    # -----------------------------------------------------
    def __parse(self) -> None:
        """ コマンドラインを解析する """
        t = CheckTurn()         # ターンチェック用

        if self.__debug:        # デバッグモード指定を取得
            wargs: list[str] = []
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

        # ここから解析本文
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
                # opt: 入力されたロング名オプション
                # oarg: None 「=」が無い「--<opt> のみ」
                # oarg: None以外 「=」に続いて入力されたオプション引数「--<opt>=<oarg>」

                # オプションキャンセル処理
                if self.__cancelable and oarg is None and opt[-1] == "-":
                    opt2 = self.__complete_l_option(opt[:-1])
                    if opt2:    # 正しいロング名オプション ----------
                        __ops = getattr(self, self.__ltoOPS[opt2])
                        __ops._set_isEnable(False)
                        __ops._set_value(None)
                        continue
                    else:       # ロング名オプションが正しくない ----
                        self.__set_error_reason('E14', arg=arg)
                        return

                opt = self.__complete_l_option(opt)
                if opt:         # 正しいロング名オプション ----------
                    __ops = getattr(self, self.__ltoOPS[opt])
                    __ops._set_isEnable(True)

                    if __ops.afunc:     # オプション引数が必要 ---------
                        harg = arg  # for 'E12' error_reason
                        if oarg is None:                    # オプション引数無し（= 以降が無い）
                            if At.OPTIONAL in __ops.atype:    # オプション引数省略可能
                                self.__store_value(__ops, None)
                                continue
                            else:
                                oarg = next(b_args, None)           # 次のブロックを引数として取得
                                blk_type = check_blocktype(oarg, self.__option_string_prefix)
                                if blk_type not in Bt.NORMAL | Bt.SOPTn:    # それも無ければエラー
                                    self.__set_error_reason('E11', arg=arg)
                                    return

                                # for 'E12' error_reason
                                harg = harg + " " + ('"None"' if oarg is None else oarg)

                        ret = self.__store_value(__ops, oarg)    # オプション引数を格納
                        if not ret:     # オプション引数格納（変換）エラー
                            self.__set_error_reason('E12', arg=harg)
                            return

                    else:               # オプション引数が不要 ---------
                        if oarg is not None:                     # オプション引数が不要なのに引数あり
                            self.__set_error_reason('E13', arg=arg)
                            return
                        if At.COUNT in __ops.atype:
                            __ops._count_value(1)

                else:           # ロング名オプションが正しくない ----
                    self.__set_error_reason('E14', arg=arg)
                    return

            elif blk_type in Bt.SOPT:    # 1文字オプションブロック（頭が「-」）=======================
                if t.checkTurn(Turn.OPT):   # ターンチェック（オプション）
                    if (self.__smode == Smode.ONEPAIR and t.isRepeat(Turn.OPT)) or \
                       (self.__smode == Smode.OPTFIRST and t.getTimes(Turn.ARG)):
                        break

                # オプションキャンセル処理
                if self.__cancelable and len(arg) == 3 and arg[-1] == "-":
                    opt = arg[1]
                    if opt in self.__s_options:     # 正しい1文字オプション -----------
                        __ops = getattr(self, self.__stoOPS[opt])
                        __ops._set_isEnable(False)
                        __ops._set_value(None)
                        continue
                    else:                           # 1文字オプションが正しくない ------
                        self.__set_error_reason('E23', opt=opt, arg=arg)
                        return

                c_arg = iter(arg[1:])
                for opt in c_arg:
                    if opt in self.__s_options:     # 正しい1文字オプション -----------
                        __ops = getattr(self, self.__stoOPS[opt])
                        __ops._set_isEnable(True)

                        if __ops.afunc:                 # オプション引数が必要か
                            oparg = "".join([c for c in c_arg])    # 後続文字列からオプション引数を取得
                            harg = arg  # for 'E22' error_reason

                            if not oparg:               # 無ければ、
                                oparg = next(b_args, None)          # 次のブロックを取得
                                blk_type = check_blocktype(oparg, self.__option_string_prefix)
                                if blk_type not in Bt.NORMAL | Bt.SOPTn:
                                    self.__set_error_reason('E21', opt=opt, arg=arg)
                                    return

                                # for 'E22' error_reason
                                harg = harg + " " + ('"None"' if oparg is None else oparg)

                            ret = self.__store_value(__ops, oparg)  # オプション引数を格納
                            if not ret:                 # オプション引数格納（変換）エラー
                                self.__set_error_reason('E22', opt=opt, arg=harg)
                                return
                        elif At.COUNT in __ops.atype:
                            __ops._count_value(1)

                    else:                           # 1文字オプションが正しくない ------
                        self.__set_error_reason('E23', opt=opt, arg=arg)
                        return

            else:   # コマンド引数ブロック（頭が「―」以外、または「-」単独）==========================
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

    def __store_value(self, __ops: Opset, optarg: Any) -> bool:
        """ このオプションのオプション引数を格納する。エラー時には Falseを返す """
        if optarg is None:
            __ops._store_value(optarg)
            return True
        for __afunc in __ops.afunc:
            if callable(__afunc):
                try:
                    # 「str」の時はそのまま格納
                    if __afunc is str:
                        __ops._store_value(optarg)

                    # Enum、Flag類
                    elif isinstance(__afunc, EnumMeta):
                        __ops._store_value(cnv_enum(__afunc, optarg))

                    # 直接変換呼び出しできるもの
                    else:
                        __ops._store_value(__afunc(optarg))

                    self.__additional_emsg = []
                    return True

                except ValueError as e:     # 変換エラー
                    self.__additional_emsg.append(str(e))
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
    def OPT_(self) -> dict[str, Opset]:
        """ オプション情報（dict タイプ）を返す """
        return self.__D_option

    @property
    def params(self) -> list[str]:
        """ 入力されたコマンド引数のリストを返す """
        return self.__params

    @property
    def remain(self) -> list[str]:
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
        if self.__emessage_header:
            __message = self.__emessage_header + " " + __message

        if level >= 1:
            for _msg in self.__additional_emsg:
                __message += "\n  -- " + _msg
        return __message

    @property
    def option_attrs(self) -> list[str]:
        """ オプション属性リストを取得する """
        return self.__options

    def make_options(self, op: Opset) -> str:
        """ オプションの、すべての文字列を取得する """
        soption = ""
        loption = ""
        for s in op.s_options:
            soption += self.__option_string_prefix + s + ', '
        for s in op.l_options:
            loption += self.__option_string_prefix * 2 + s + ', '

        return (soption + loption).rstrip(', ')

    def get_optionlist(self) -> list[str]:
        """ オプション設定一覧を取得する """
        optionlist: list[str] = []

        for opt in self.__options_and_comments:
            if opt.startswith("#"):
                optionlist.append(opt[1:])
                continue
            op = getattr(self, opt)
            option = self.make_options(op)
            if op.afunc:
                option += " " + op.acomment

            optionlist.append(option + "\t" + ": " + op.comment)
        return optionlist

    @staticmethod
    def show_errormessage() -> None:
        """ 解析エラーメッセージ一覧を表示する（デバッグ用） """
        for eno in emsg:
            print(Parse.__error_message(eno, arg="<ARG>", opt="<OPT>",
                                        ext0="<EXT0>", ext1="<EXT1>"))


# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    import cl_parse_functions as cf

    class Color(IntFlag):
        RED = auto()
        GREEN = auto()
        BLUE = auto()
        PURPLE = RED | GREEN
        WHITE = RED | GREEN | BLUE

    args = sys.argv
    if len(args) <= 1:
        # args = 'this.py ---# -? ABC --all --size=200x0X2F -c RED|GREEN'.split()
        # args = 'this.py ---# ABC --all --size=200x0X2F --date=2022/1/31'.split()
        args = 'this.py ---# ABC --all --size=200x0X2F -c RED|GREEN'.split()

    # cl_parse 呼び出し用のオプション定義
    options: TOptions = (
            ("#オプション一覧"),
            ("help", "-h, -? ,  --help", "使い方を表示する", None),
            ("all", "-a, --all", "すべて出力"),
            ("date", "-d, --date", "作成日付（YYYY/MM/DD）//<日付>", cf.date),
            ("color", "-c, --color", "表示色を指定する\n（RED,GREEN,BLUE,PURPLE,WHITE）//<color>",
                Color),
            ("#  ※「作成日付」と「表示色」オプションは同時に指定できません。\n"),
            ("size", " --size, -s", "表示サイズを指定する//<縦x横>",
                cf.sepalate_items(type=cf.int_literal, sep='x', count=2)),
    )

    exclusive = [
        ("date", "color"),
    ]

    newemsg = {
        "E31": ": オプション ({ext0}) と ({ext1}) は同時に指定できません。",
    }

    emsg.update(newemsg)
    # Parse.show_errormessage()

    # cl_parse 呼び出し（解析実行）
    ps = Parse(args, options, exclusive=exclusive, cancelable=True, debug=True, emessage_header="@stem")

    if ps.is_error:
        # ps.get_errormessage() 等を表示する
        print(ps.get_errormessage(1), file=sys.stderr)
        print(file=sys.stderr)
        tabprint(ps.get_optionlist(), [16, 4], file=sys.stderr)
        exit(1)

    if ps.OPT_help.isEnable:       # 使い方を表示する
        # ps.get_optionlist() 等を表示する
        print("USAGE: cl_parse [option] ... [-d date | -c color] とかなんとか\n")
        tabprint(ps.get_optionlist(), [16, 4])
        exit()

    # ここからユーザープログラム

    if ps.OPT_all.isEnable:        # すべて出力
        print("「すべて出力」が指定されました。")
        pass
    if ps.OPT_date.isEnable:       # 作成日付（YYYY/MM/DD）
        value = ps.OPT_date.value
        print(f"「作成日付（{value=}）」が指定されました。")
    if ps.OPT_color.isEnable:      # 表示色を指定する
        value = ps.OPT_color.value
        print(f"「表示色を指定する（{value=}）」が指定されました。")
    if ps.OPT_size.isEnable:       # 表示サイズを指定する
        value = ps.OPT_size.value
        print(f"「表示サイズを指定する（{value=}）」が指定されました。")

    print(f'{ps.params=}')         # コマンド引数
    