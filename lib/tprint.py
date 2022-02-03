#!/usr/bin/env python3
# -------------------------------------------------------------
# 項目をタブ揃えして表示するモジュール         2022/1/27 by te.
# -------------------------------------------------------------
import sys
from typing import Iterator, NamedTuple, List, Any, Union, TextIO
from e2_wstr import Wstr


# -------------------------------------------------------------
#    左詰めとか、右詰めとか、フィールド幅の指定とかのフォーマット文字列を
#    解析して分解する関数（tprintモジュール用）
# -------------------------------------------------------------
def split_digits(text: str) -> List[str]:
    ''' 書式文字列を、単独文字、数字列のリストに分解する。
        ex) "=^320" -> ["=", "^", "320"]
    '''
    ret: List[str] = []
    for c in (_itext := iter(text)):
        _digits = ""
        while c.isdigit():
            _digits += c
            c = next(_itext, "")
        if _digits:
            ret.append(_digits)
        if c:
            ret.append(c)
    return ret


class PFormat(NamedTuple):
    ''' 分解された書式データ '''
    fill: str = ""      # 埋め文字（未指定時は ""）
    align: str = ""     # 配置方法（'^', '<', '>'）（未指定時は ""）
    width: int = 0      # フィールド幅（未指定時は 0）


def split_formatstring(format_string: str) -> PFormat:
    ''' フォーマット文字列を、fill、align、width に分解する
    '''
    align_set = ['^', '<', '>']     # align 指定文字のセット

    _fill = ""      # 解析中の fill
    _align = ""     # 解析中の align
    _width = ""     # 解析中の width（文字列）

    for item in split_digits(format_string):
        if not _width:
            if item in align_set:   # item が '^', '<', '>'
                if not _align:          # alignが未取得だったら align
                    _align = item
                elif not _fill:         # alignあって、fillが未取得だったら
                    _fill = _align          # 前回のは fillだった
                    _align = item           # 今回のが本当の align
                else:                   # どっちも取得済み（エラー）
                    raise ValueError(f'Invalid format specifier on "{format_string}"')

            elif item.isdigit():    # item が数字列
                if not _fill and not _align and len(item) == 1:
                    _fill = item        # 数字1文字なら fillかも
                else:
                    _width = item       # 数字2文字以上なら width決定

            elif not _fill and not _align:
                # item が align_set でも数字でもなくて、fillも alignもまだだったら、
                _fill = item            # それは、fill
            else:           # それ以外のパターンはエラー
                raise ValueError(f'Invalid format specifier on "{format_string}"')

        else:           # width まで取得済みなのにまだデータがある(エラー）
            raise ValueError(f'Invalid format specifier on "{format_string}"')

    if not _align and _fill.isdigit() and not _width:
        # 1文字数字が fillだと思ったけど、alignも widthもなければ、
        _width = _fill     # fillじゃなくて widthだった
        _fill = ""

    return PFormat(_fill, _align, int(_width) if _width else 0)


# -------------------------------------------------------------
# 以下、tprint用内部関数（汎用関数候補）
# -------------------------------------------------------------
def eter_list(anylist: List[Any], eter: Any = ...) -> Iterator[Any]:
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


def normalize_table(table: List[List[Any]], fill: Any = 0) -> List[List[Any]]:
    ''' 2次ジャグ配列を正方配列に整形した、新しい配列を返す。
        項目の不足分は[fill]を付加する
    '''
    maxlen = max([len(item) for item in table])     # table内の各行の最大項目数
    return [[i2 for i2, _ in zip(eter_list(ln, fill), range(maxlen))] for ln in table]


# -------------------------------------------------------------
# 以下、tprint用内部関数
# -------------------------------------------------------------
def _get_maxtablist(list_widthlist: List[List[int]]) -> List[int]:
    ''' 「個々のlineの、表示幅リスト」のlistから、
        各項目が最大幅になる表示幅listを返す
    '''
    # 正規化して転置して最大値のリストを作成する
    return [max(ll) for ll in zip(*normalize_table(list_widthlist))]


def _make_widthtable(table: List[List[str]], tablist: List[int]) -> List[List[int]]:
    ''' table中の各line中の個々のtextの表示幅をtab揃えした、
        新しい表示幅table（2次元配列）を作成する
    '''
    def _addtab(width: int) -> int:     # 個々のtext幅の、tab揃えの計算
        w = 0
        while w <= width:
            w += next(tabstop)
        return w

    widthtable: List[List[int]] = []
    for line in table:                      # table中の各lineの処理
        tabstop = eter_list(tablist)
        widthlist = [_addtab(Wstr(text).width()) for text in line]
        widthtable.append(widthlist)
    return widthtable


# -------------------------------------------------------------
# tprint本体
# -------------------------------------------------------------
def _maketabline(tablist: List[int], line_width: int = 0) -> str:
    ''' tablistの目盛りを line_widthの幅だけ表示する
        （line_width省略時は、tablistの幅だけ）
    '''
    _width = sum(tablist) if line_width <= 0 else line_width
    tabstop = eter_list(tablist)
    tabline = ""
    while(len(tabline) < _width):
        tabline += '-' * (next(tabstop) - 1) + '+'
    return tabline


def _makeline(textlist: List[str], tablist: List[int],) -> str:
    ''' タブを揃えた文字列（一行分）を作成する
        （textlist中の文字列を、widthlist中の表示幅で結合する）
    '''
    _line = ""
    for text, width in zip(Wstr.wlist(textlist), eter_list(tablist)):
        _line += (text.l_adjust(width - 1, marker='.') + " ")
    return _line.rstrip()


def _makeline2(textlist: List[str], pflist: List[PFormat],
               separator: str = " ", cutmarker: Union[str, List[str]] = '*') -> str:
    ''' タブを揃えた文字列（一行分）を作成する
        （textlist中の文字列を、pflist中のフォーマットで結合する）
    '''
    l_cutmarker = r_cutmarker = ""
    if type(cutmarker) is list:
        l_cutmarker: str = cutmarker[0] if len(cutmarker) > 0 else ""
        r_cutmarker: str = cutmarker[1] if len(cutmarker) > 1 else l_cutmarker
    elif type(cutmarker) is str:
        l_cutmarker = r_cutmarker = cutmarker

    _line = ""
    for text, pf in zip(Wstr.wlist(textlist), pflist):
        _width = pf.width if pf.width else text.width()
        # print(_width)
        _fill = pf.fill if pf.fill else ' '
        if pf.align == '^':
            _line += (text.center(_width, _fill).l_adjust(_width, marker=r_cutmarker)
                     + separator)
        elif pf.align == '>':
            _line += (text.r_adjust(_width, _fill, marker=l_cutmarker) + separator)
        else:
            _line += (text.l_adjust(_width, _fill, marker=r_cutmarker) + separator)
    return (_line if len(separator) <= 0 else _line[0:-len(separator)]).rstrip()


def tprint(table: List[List[str]], tablist: List[int] = [8],
           tabscale: bool = False, file: TextIO = sys.stdout):
    ''' 単純タブ揃え表示
        （table中の各lineの、各項目を直近のタブに揃えて表示する）
    '''
    # 個々の表示幅リストを作成
    width_table = _make_widthtable(table, tablist)

    # タブ目盛り（最大項目幅分）
    if tabscale:
        maxlinewidth = max([sum(line) for line in width_table])
        print(_maketabline(tablist, maxlinewidth), file=file)

    # 個々の表示幅リストで、個々のlineを表示する
    for line, tabs in zip(table, width_table):
        print(_makeline(line, tabs), file=file)


def tprint_maxtab(table: List[List[str]], tablist: List[int] = [1],
                  tabscale: bool = False, file: TextIO = sys.stdout):
    ''' 最大タブ揃え表示
        （table中の各lineの各項目を、項目ごとの最大タブに揃えて表示する）
    '''
    # 個々の表示幅リストを作成
    width_table = _make_widthtable(table, tablist)

    # 個々の表示幅リストから、項目ごとの最大タブ幅のリストを取得する
    maxtablist = _get_maxtablist(width_table)

    # タブ目盛り（最大タブ幅）
    if tabscale:
        print(_maketabline(maxtablist), file=file)

    # 最大タブ幅で各lineを表示する
    for line in table:
        print(_makeline(line, maxtablist), file=file)


def fprint(table: List[List[str]], flist: List[Union[str, int]] = [],
           separator: str = " ", cutmarker: Union[str, List[str]] = "",
           titleline: int = 0,
           tabscale: bool = False, file: TextIO = sys.stdout):
    ''' 強制桁揃え表示／
        table中の各lineの各項目を、表示フォーマットリスト（flist）に従って表示する。
        表示幅が省略（または 0）されている項目は、タイトル行の項目の表示幅を使用する
    '''
    # タイトル行から、各項目の表示幅リストを作成
    maxcount = max([len(line) for line in table])   # 行の最大項目数を取得
    title_widthlist = [Wstr(text).width() for text in table[titleline]]
    title_widthlist += [title_widthlist[-1]] * (maxcount - len(title_widthlist))

    # str|int 混在の引数から、表示フォーマットリストを作成
    pflist = [PFormat("", "", item) if type(item) is int else split_formatstring(item)
              for item in flist]

    # 表示フォーマットリストの、省略された表示幅をタイトル行の表示幅で補完
    new_pflist: List[PFormat] = []
    for w, pf in zip(title_widthlist, eter_list(pflist, pflist[-1])):
        new_pflist.append(pf if pf.width else PFormat(pf.fill, pf.align, w))

    # タブ目盛り
    if tabscale:
        tablist = [pf.width for pf in new_pflist]
        print(_maketabline(tablist), file=file)

    # 各lineを表示する
    for line in table:
        print(_makeline2(line, new_pflist, separator=separator, cutmarker=cutmarker), file=file)


def fprint_limit(table: List[List[str]], flist: List[Union[str, int]] = [],
                 separator: str = " ", cutmarker: Union[str, List[str]] = "",
                 tabscale: bool = False, file: TextIO = sys.stdout):
    ''' 制限付き最大桁揃え表示／
        table中の各lineの各項目を、表示フォーマットリスト（flist）に従って表示する。
        各項目の表示幅は最大の項目に揃えられるが、表示フォーマットリストで指定する
        表示幅を最大値とする
    '''
    # 各行各項目の表示幅のテーブルを作成
    width_table: List[List[int]] = [[Wstr(item).width() for item in line] for line in table]
    # 各行各項目の表示幅のテーブルから、項目ごとの最大タブ幅のリストを取得する
    maxwidthlist = _get_maxtablist(width_table)

    # str|int 混在の引数から、表示フォーマットリストを作成
    pflist = [PFormat("", "", item) if type(item) is int else split_formatstring(item)
              for item in flist]

    # pflistの各表示幅を limitにした、新しい表示フォーマットリストを作成
    new_pflist: List[PFormat] = []
    for w, pf in zip(maxwidthlist, eter_list(pflist, pflist[-1])):
        new_pflist.append(pf if pf.width and pf.width < w else PFormat(pf.fill, pf.align, w))

    # タブ目盛り
    if tabscale:
        tablist = [pf.width for pf in new_pflist]
        print(_maketabline(tablist), file=file)

    # 各lineを表示する
    for line in table:
        print(_makeline2(line, new_pflist, separator=separator, cutmarker=cutmarker), file=file)


if __name__ == '__main__':
    def test(sample: str):
        print(sample)
        print()
        eval(sample)
        print()
        print()

    text_lines = [
        ["NAME", "MATH.", "LANG.", "SCI.", "Eval.", "Notes"],
        ["------------", "------", "----", "----", "--------", "---------------"],
        ["Scarlet Warrior", "50", "45", "100", "B"],
        ["John Manjiro", "60", "20", "90"],
        ["Elice Graystork", "2", "80", "20", "unknown", "I can't say anything."],
        ["Yamada Taro", "100", "80", "80", "AA"],
    ]

    text_lines2 = [
        ["名前", "算数", "国語", "理科", "総合評価", "備考"],
        ["------------", "------", "----", "----", "--------", "---------------"],
        ["紅の戦士", "50", "45", "100", "B"],
        ["John 万次郎", "60", "20", "90"],
        ["Elice Graystork", "2", "80", "20", "不明", "何考えているのだか分からない"],
        ["山田　太郎", "100", "80", "80", "優"],
    ]

    # Wstr.set_EastAsianAnbigous(1)

    print()
    print("★ 単純タブ揃え表示")
    test("tprint(text_lines, tabscale=True)")
    # test("tprint(text_lines, [12, 8, 8], tabscale=True)")
    test("tprint(text_lines, [16, 12, 8], tabscale=True)")

    print()
    print("★ 最大タブ揃え表示")
    test("tprint_maxtab(text_lines, [12, 8], tabscale=True)")
    # test("tprint_maxtab(text_lines, [8], tabscale=True)")
    test("tprint_maxtab(text_lines, [1], tabscale=True)")

    print()
    print()
    print("★ 強制桁揃え表示")
    test("fprint(text_lines, [15, '>4', '>4', '>4', '>', '<'], cutmarker='*')")
    test("fprint(text_lines, ['>14', '>8', 10, '>', '6'])")
    test("fprint(text_lines, [10, '>4', '^'], cutmarker=['', '*'])")
    test("fprint(text_lines, [0, '>', '>', '>', '-^', '<'], separator='|', titleline=1, cutmarker='*')")
    # test("fprint(text_lines, [0, >, '>', '>15'], cutmarker='*', tabscale=True)")

    print()
    print()
    print("★ 制限付き最大桁揃え表示")
    
    # test("fprint_limit(text_lines, [0, '>', '>', '>15', '^', 15], cutmarker='*')")
    test("fprint_limit(text_lines, [0, '>', '>', '>', '-^', '<'], cutmarker='*')")
    test("fprint_limit(text_lines, [0, '>', '>', '>', '^', 0], separator = '|', cutmarker='*')")

    # text_lines2 = [
    #     ["名前", "算数", "国語", "理科", "総合評価", "備考"],
    #     ["------------", "------", "----", "----", "--------", "---------------"],
    #     ["紅の戦士", "50", "45", "100", "B"],
    #     ["John 万次郎", "60", "20", "90"],
    #     ["Elice Graystork", "2", "80", "20", "不明", "何考えているのだか分からない"],
    #     ["山田　太郎", "100", "80", "80", "優"],
    # ]

    # test("fprint_limit(text_lines2, [0, '>', '>', '>', '^', '<25'], separator = '|', cutmarker='*')")

    text_lines2 = [
        ["", "名前", "算数", "国語", "社会", "総合評価", "備考", ""],
        ["", "------------", "------", "----", "----", "--------", "---------------", ""],
        ["", "紅の戦士", "50", "45", "100", "B", "", ""],
        ["", "John 万次郎", "60", "20", "90", "", "", ""],
        ["", "Elice Graystork", "2", "80", "20", "不明", "何考えているのだか分からない", ""],
        ["", "山田　太郎", "100", "80", "80", "優", "", ""],
    ]

    test("fprint_limit(text_lines2, [0, 0, '>', '>', '>', '^', '<25'], separator = '|', cutmarker='*')")
