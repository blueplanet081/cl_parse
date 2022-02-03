from typing import Iterator, NamedTuple, List, Any, Union, TextIO
import sys


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


def _maketabline(tablist: List[int], line_width: int = 0) -> str:
    ''' tablistの目盛りを line_widthの幅だけ表示する
        （line_width省略時は、tablistの幅だけ）
    '''
    _width = sum(tablist) if line_width <= 0 else line_width
    tabstop = _eter_list(tablist)
    tabline = ""
    while(len(tabline) < _width):
        tabline += '-' * (next(tabstop) - 1) + '+'
    return tabline


def _makeline(line: List[str], tablist: List[int]) -> str:
    ''' タブを揃えた文字列（一行分）を作成する '''
    def _addtab(width: int) -> int:     # 個々のtext幅の、tab揃えの計算
        w = 0
        while w <= width:
            w += next(tabstop)
        return w

    tabstop = _eter_list(tablist)
    return ''.join([text.ljust(_addtab(len(text))) for text in line])


def tabprint(table: List[List[str]], tablist: List[int] = [8],
             file: TextIO = sys.stdout):
    ''' 単純タブ揃え表示
        （table中の各lineの、各項目を直近のタブに揃えて表示する）
    '''
    # 個々の表示幅リストで、個々のlineを表示する
    for line in table:
        print(_makeline(line, tablist), file=file)


line = ["Oh'bea45", "gggsjkf", "kkk", "mmm"]
text_lines = [
    ["NAME", "MATH.", "LANG.", "SCI.", "Eval.", "Notes"],
    ["------------", "------", "----", "----", "--------", "---------------"],
    ["Scarlet Warrior", "50", "45", "100", "B"],
    ["John Manjiro", "60", "20", "90"],
    ["Elice Graystork", "2", "80", "20", "unknown", "I can't say anything."],
    ["Yamada Taro", "100", "80", "80", "AA"],
]


tablist = [12, 8, 8]
print(_maketabline(tablist, 60))
# print(_makeline(line, tablist))
tabprint(text_lines, tablist)
