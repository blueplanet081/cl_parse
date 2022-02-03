#!/usr/bin/env python3
# -------------------------------------------------------------
# 項目をタブ揃えして表示するモジュール         2022/1/27 by te.
# -------------------------------------------------------------
import sys
from typing import Iterator, List, Any, TextIO
import unicodedata


# -------------------------------------------------------------
# Wstrクラス                                    2021/1/8 by te.
# -------------------------------------------------------------
class Wstr(str):
    ''' 表示幅の異なる文字が混在する文字列を扱うクラス（str のサブクラス）。
        str のメソッドが「文字数による編集処理」をするのに対して、
        「表示幅による編集処理」を行うメソッドを提供する
    '''
    ''' ここでは、ascii文字、表示幅が Halfwidth、Nallowの文字を便宜的に「半角」、
        表示幅が Fullwidth、Wideの文字を「全角」と表現する。
    '''
    # 表示幅が全角になる、east_asian_widthの特性値セット（デフォルト）
    __Fullset = ('FWA')

    @classmethod
    def wlist(cls, slist: List[str, ]) -> List['Wstr']:
        ''' リスト内の strオブジェクトを Wstrオブジェクトに変換する
        '''
        ret: List[Wstr, ] = []
        for item in slist:
            ret.append(cls(item))
        return ret

    @staticmethod
    def widthOfCharacter(char: str) -> int:
        ''' 先頭１文字の表示幅、1（主にASCII文字）か 2（主に漢字）を返す '''
        return 2 if unicodedata.east_asian_width(char[0]) in Wstr.__Fullset else 1

    def width(self) -> int:
        ''' 日本語混じり文字列の表示幅を取得する '''
        return sum([Wstr.widthOfCharacter(c) for c in self])

    def __adjustwidth(self, __width: int) -> int:
        ''' 文字幅（__width）を、先頭からの文字数に変換する内部メソッド。
            指定文字幅の最後が、表示幅2の文字の途中であった場合、self.hanpa が Trueになる
            （トリッキーなので self.hanpaの振る舞いに注意！）
        '''
        i = w = 0
        self.__hanpa = False
        if __width <= 0:    # 指定文字幅が 0以下の場合、文字数は 0固定
            return 0
        for c in self:
            w += Wstr.widthOfCharacter(c)
            if w > __width:     # 表示幅 2の文字の途中（半端あり）
                self.__hanpa = True
                return i
            i += 1
            if w == __width:    # 半端がない
                return i
        # 指定文字幅が指定文字列より長い場合
        return __width - (w - i)

    def ljust(self, width: int, fillchar: str = ' ') -> 'Wstr':     # type: ignore ^^;
        ''' 元の文字列の、左から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、不足分を fillchar（半角であること）で文字詰めする。
            元の文字列が width より長い場合は、元の文字列を返す
        '''
        return Wstr(super().ljust(self.__adjustwidth(width), fillchar[0:1]))

    def __left(self, width: int, fillchar2: str = " ") -> 'Wstr':
        ''' 元の文字列の、左から表示幅（width）分の文字列を返す内部メソッド。
            元の文字列が width より短い場合は、元の文字列をそのまま返す。
            元の文字列が表示幅より長い場合は右端をカットする。
            カットすることにより表示幅に端数が出た場合は、右端に fillchar2（半角であること）を追加する。
        '''
        ret = self.__adjustwidth(width)
        return Wstr(self[0:ret] + (fillchar2[0:1] if self.__hanpa else ""))

    def left(self, width: int, fillchar2: str = " ", marker: str = '') -> 'Wstr':
        ''' 元の文字列の、左から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、元の文字列をそのまま返す。
            元の文字列が表示幅より長い場合は右端をカットする。
            カットすることにより表示幅に端数が出た場合は、右端に fillchar2（半角であること）を追加する。
            省略記号（marker）が指定された場合、右端の文字列を markerで置きかえる。
        '''
        if self.width() <= width:
            return self
        else:
            return Wstr(self.__left(width - Wstr(marker).width(), fillchar2) + marker)

    def l_adjust(self, width: int, fillchar: str = ' ', fillchar2: str = ' ',
                                                                    marker: str = '') -> 'Wstr':
        ''' 元の文字列の、左から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、不足分を fillchar（半角であること）で文字詰めする。
            元の文字列が表示幅より長い場合は右端をカットする。
            カットすることにより表示幅に端数が出た場合は、右端に fillchar2（半角であること）を追加する。
            省略記号（marker）が指定された場合、右端の文字列を markerで置きかえる。
        '''
        if self.width() <= width:
            return self.ljust(width, fillchar=fillchar)
        else:
            return Wstr(self.left(width, fillchar2=fillchar2, marker=marker))


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


# -------------------------------------------------------------
# 以下、tprint用内部関数
# -------------------------------------------------------------
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
def _makeline(textlist: List[str], tablist: List[int],) -> str:
    ''' タブを揃えた文字列（一行分）を作成する
        （textlist中の文字列を、widthlist中の表示幅で結合する）
    '''
    _line = ""
    for text, width in zip(Wstr.wlist(textlist), eter_list(tablist)):
        _line += (text.l_adjust(width - 1, marker='.') + " ")
    return _line.rstrip()


def tprint(table: List[List[str]], tablist: List[int] = [8],
           file: TextIO = sys.stdout):
    ''' 単純タブ揃え表示
        （table中の各lineの、各項目を直近のタブに揃えて表示する）
    '''
    # 個々の表示幅リストを作成
    width_table = _make_widthtable(table, tablist)

    # 個々の表示幅リストで、個々のlineを表示する
    for line, tabs in zip(table, width_table):
        print(_makeline(line, tabs), file=file)


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
    test("tprint(text_lines2)")
    # test("tprint(text_lines, [12, 8, 8], tabscale=True)")
    test("tprint(text_lines2, [16, 12, 8])")

