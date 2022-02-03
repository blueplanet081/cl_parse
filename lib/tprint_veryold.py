#!/usr/bin/env python3
# -------------------------------------------------------------
# 項目をタブ揃えして表示するモジュール        2021/12/30 by te.
# -------------------------------------------------------------
import sys
import unicodedata
from typing import Iterator, List, Any, TextIO


# -------------------------------------------------------------
# 日本語混じり文字列を整形するクラスの一部（汎用）
# -------------------------------------------------------------
Wstr_fullset = ('F', 'W', 'A')


class Wstr(str):
    @staticmethod
    def set_EastAsianAnbigous(width: int = 2):
        ''' EastAsianAnbigous な文字の表示幅を指定する。
            width = 1 で half、それ以外はみんな Full
        '''
        global Wstr_fullset
        if width == 1:
            Wstr_fullset = ('F', 'W')
        else:
            Wstr_fullset = ('F', 'W', 'A')

    def width(self) -> int:
        """ 日本語混じり文字列の表示幅を取得する
        """
        len = 0
        for c in self:
            len += 2 if unicodedata.east_asian_width(c) in Wstr_fullset else 1
        return len

    def ljust(self, __width: int, __fillchar: str = ...) -> 'Wstr':     # type: ignore ^^;
        """ 日本語混じり文字列を、左寄せ文字詰めする
            （str.ljust() のワイド文字対応版）
        """
        __fillchar = ' ' if __fillchar == Ellipsis else __fillchar[0:1]
        return Wstr(self + __fillchar*(__width - self.width()))


# -------------------------------------------------------------
# 以下、tprint用内部関数
# -------------------------------------------------------------
def iter_tabstop(tablist: List[int]) -> Iterator[int]:
    ''' tablist中のタブ量を順次返す。tablistを越える分は最後のタブ量を繰り返す
    '''
    for num in tablist:
        yield num
    while True:
        yield tablist[-1]


def normalize_table(table: List[List[Any]], fill: Any = 0) -> List[List[Any]]:
    ''' 2次ジャグ配列を正方配列に整形した、新しい配列を返す。
        項目の不足分は[fill]を付加する
    '''
    new_table: List[List[Any]] = []
    maxcount: int = 0
    for line in table:
        maxcount = max(maxcount, len(line))
    for line in table:
        newline: List[Any] = line + [fill] * (maxcount - len(line))
        new_table.append(newline)
    return new_table


def get_maxlinewidth(list_widthlist: List[List[int]]) -> int:
    ''' 「個々のlineの、表示幅リスト」のlistから、最大のline表示幅を返す
        （目盛り表示用）
    '''
    maxwidth: int = 0
    for line in list_widthlist:
        maxwidth = max(maxwidth, sum(line))
    return maxwidth


def get_maxwidthlist(list_widthlist: List[List[int]]) -> List[int]:
    ''' 「個々のlineの、表示幅リスト」のlistから、
        各項目が最大幅になる表示幅listを返す
    '''
    new_lines = normalize_table(list_widthlist)
    maxwidthlist = new_lines[0]
    for line in list_widthlist[1:]:
        for i, size in enumerate(line):
            maxwidthlist[i] = max(maxwidthlist[i], size)
    return maxwidthlist


def make_list_withlist(table: List[List[str]], tablist: List[int]) -> List[List[int]]:
    ''' tablistを元に、table中の各line中の個々のtextの表示幅の2次元配列を作成する
    '''
    list_widthlist: List[List[int]] = []
    for line in table:                      # table中の各lineの処理
        tabstop = iter_tabstop(tablist)
        widthlist: List[int] = []
        for text in line:                   # 各line中のtextの表示幅を計算
            wsize = 0
            textsize = Wstr(text).width()
            for tabsize in tabstop:
                wsize += tabsize
                if wsize > textsize:
                    break
            widthlist.append(wsize)
        list_widthlist.append(widthlist)
    return list_widthlist


# -------------------------------------------------------------
# tprint本体
# -------------------------------------------------------------
def tprint_tabline(tablist: List[int], count: int = 0, file: TextIO = sys.stdout):
    ''' tablistの目盛りをcountの数だけ表示する。count省略時は、tablistの個数分を表示する
    '''
    if count <= 0:
        count = sum(tablist)
    tabstop = iter_tabstop(tablist)
    wlength = 0
    for size in tabstop:
        print('-' * (size - 1) + '+', end="", file=file)
        wlength += size
        if wlength >= count:
            break
    print(file=file)


def tprint_line(textlist: List[str], tablist: List[int], file: TextIO = sys.stdout):
    ''' タブ揃え一行表示
        （textlist中の文字列を、widthlist中の表示幅で表示する）
    '''
    for text, width in zip(textlist, iter_tabstop(tablist)):
        print(Wstr(text).ljust(width), end="", file=file)
    print(file=file)


def tprint(table: List[List[str]], tablist: List[int],
           tabscale: bool = False, file: TextIO = sys.stdout):
    ''' 単純タブ揃え表示
        （table中の各lineの、各項目を直近のタブに揃えて表示する）
    '''
    # print("単純タブ揃え表示", tablist, file=file)

    # 個々の表示幅リストを作成
    list_widthlist = make_list_withlist(table, tablist)

    # タブ目盛り（最大項目幅分）
    if tabscale:
        tprint_tabline(tablist, get_maxlinewidth(list_widthlist), file=file)

    # 個々の表示幅リストで、個々のlineを表示する
    for line, tabs in zip(table, list_widthlist):
        tprint_line(line, tabs, file=file)


def tprint_maxtab(table: List[List[str]], tablist: List[int],
                  tabscale: bool = False, file: TextIO = sys.stdout):
    ''' 最大タブ揃え表示
        （table中の各lineの各項目を、項目ごとの最大タブに揃えて表示する）
    '''
    # print("最大タブ揃え表示", tablist)

    # 個々の表示幅リストを作成
    list_widthlist = make_list_withlist(table, tablist)

    # 個々の表示幅リストから、項目ごとの最大タブ幅のリストを取得する
    maxwidthlist = get_maxwidthlist(list_widthlist)

    # タブ目盛り（最大タブ幅）
    if tabscale:
        tprint_tabline(maxwidthlist, file=file)

    # 最大タブ幅で各lineを表示する
    for line in table:
        tprint_line(line, maxwidthlist, file=file)


if __name__ == '__main__':
    text_lines = [
        ["this_is_a_pen", "Boy", "meets", "Girl"],
        ["国境の", "long_tunnnel", "A!"],
        ["Oh! be a fine", "girl kiss me", "◎abc", "hello everybody", "someday"],
        ["aoi", "海原→←", "konokono"],
    ]

    tablist = [12, 12, 8]

    Wstr.set_EastAsianAnbigous(1)

    tprint(text_lines, [16, 12, 8], tabscale=True)

    print()
    tprint(text_lines, [12, 8, 8], tabscale=True, file=sys.stderr)

    print()
    tprint(text_lines, [8, 8, 8], tabscale=True)

    print()
    tprint_maxtab(text_lines, tablist, tabscale=True)

    print()
    tprint_maxtab(text_lines, [8], tabscale=True)

    print()
    tprint_maxtab(text_lines, [14, 8], tabscale=True)

    print()
    tprint_maxtab(text_lines, [2], tabscale=True)

    print()
    tprint_maxtab(text_lines, [1], tabscale=True)
