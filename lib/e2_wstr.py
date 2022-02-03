''' 表示幅の異なる文字が混在する文字列を扱うクラス、Wstr（str のサブクラス）を定義する
'''

import unicodedata
from typing import List


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

    @staticmethod
    def set_EastAsianAnbigous(width: int = 2):
        ''' EastAsianAnbigous な文字の表示幅を指定する。
            width = 1 で半角相当、それ以外はみんな全角相当
        '''
        if width == 1:
            Wstr.__Fullset = ('FW')
        else:
            Wstr.__Fullset = ('FWA')

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

    def center(self, width: int, fillchar: str = ' ') -> 'Wstr':     # type: ignore ^^;
        ''' 日本語混じり文字列を中央寄せする。str.center() のワイド文字対応版 '''
        return(Wstr(super().center(self.__adjustwidth(width), fillchar[0:1])))

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

    def rjust(self, width: int, fillchar: str = ' ') -> 'Wstr':     # type: ignore ^^;
        ''' 元の文字列の、右から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、不足分を fillchar（半角であること）で文字詰めする。
            元の文字列が width より長い場合は、元の文字列を返す
        '''
        return Wstr(super().rjust(self.__adjustwidth(width), fillchar[0:1]))

    def __right(self, width: int, fillchar2: str = ' ') -> 'Wstr':
        ''' 元の文字列の、右から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、元の文字列をそのまま返す。
            元の文字列が表示幅より長い場合は左端をカットする。
            カットすることにより表示幅に端数が出た場合は、左端に fillchar2（半角であること）を追加する
        '''
        return Wstr(Wstr(self[::-1]).__left(width, fillchar2)[::-1])

    def right(self, width: int, fillchar2: str = ' ', marker: str = '') -> 'Wstr':
        ''' 元の文字列の、右から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、元の文字列をそのまま返す。
            元の文字列が表示幅より長い場合は左端をカットする。
            カットすることにより表示幅に端数が出た場合は、左端に fillchar2（半角であること）を追加する。
            省略記号（marker）が指定された場合、左端の文字列を markerで置きかえる。
        '''
        if self.width() <= width:
            return self
        else:
            return Wstr(marker + self.__right(width - Wstr(marker).width(), fillchar2))

    def r_adjust(self, width: int, fillchar: str = ' ', fillchar2: str = ' ',
                                                                    marker: str = '') -> 'Wstr':
        ''' 元の文字列の、右から表示幅（width）分の文字列を返す。
            元の文字列が width より短い場合は、不足分を fillchar（半角であること）で文字詰めする。
            元の文字列が表示幅より長い場合は左端をカットする。
            カットすることにより表示幅に端数が出た場合は、左端に fillchar2（半角であること）を追加する。
            省略記号（marker）が指定された場合、左端の文字列を markerで置きかえる。
        '''
        if self.width() <= width:
            return self.rjust(width, fillchar)
        else:
            return Wstr(marker + self.right(width - Wstr(marker).width(), fillchar2))


if __name__ == '__main__':
    def testprint(sample: str, width_list: List[int], allign: str = ""):
        print()
        _lallign = max(32, len(sample)-2)
        for width in width_list:
            # print(f'[{"-" * width}]')
            _sample = sample.replace("width", str(width))
            if allign == ">":
                print(f'{_sample.ljust(_lallign)}: ' +
                      f'{Wstr(f"[{eval(_sample)}]").rjust(width_list[-1] + 2)}')
            elif allign == "^":
                print(f'{_sample.ljust(_lallign)}: ' +
                      f'{Wstr(f"[{eval(_sample)}]").center(width_list[-1] + 2)}')
            else:
                print(f'{_sample.ljust(_lallign)}: {Wstr(f"[{eval(_sample)}]")}')

    Wstr.set_EastAsianAnbigous(1)

    print(f'{Wstr.widthOfCharacter("abc") = }')
    print(f"{Wstr.widthOfCharacter('漢') = }")

    print()
    print(f"{len('なんとsutekiな世界') = }")
    print(f"{len(Wstr('なんとsutekiな世界')) = }")
    print(f"{Wstr('なんとsutekiな世界').width() = }")

    wtext1 = Wstr('なんとsutekiな世界')
    width_list = [5, 8, 12, 15, 22, 25]

    testprint("wtext1.ljust(width, '-')", width_list)
    testprint("wtext1.left(width, '*')", width_list)

    testprint("wtext1.left(width, marker='..')", width_list)

    testprint("wtext1.l_adjust(width, '-', '*')", width_list)

    testprint("wtext1.l_adjust(width, marker='..')", width_list)

    testprint("wtext1.center(width, '-')", width_list, "^")

    testprint("wtext1.rjust(width, '-')", width_list, ">")
    testprint("wtext1.right(width, '*')", width_list, ">")
    testprint("wtext1.right(width, marker='')", width_list, ">")

    testprint("wtext1.r_adjust(width, '-', '*')", width_list, ">")
    testprint("wtext1.r_adjust(width, marker='...')", width_list, ">")
