from __future__ import annotations
from typing import List, Tuple, Sequence

optionname_list = ["help", "all", "date", "test"]

__set_exclusive: List[List[str]] = []


# -----------------------------------------------------
# 排他リスト読み込み処理
# -----------------------------------------------------
def __set_exclusive(exsv: Sequence[str] | Sequence[Sequence[str]]):
    """ 排他リスト読み込み処理 """
    def is_pair_of_string(sample: list[list[str]] | list[str]) -> bool:
        """ [str, str] じゃなかったら False """
        if (type(sample) is list) and (len(sample) == 2) and \
            (type(sample[0]) is str) and (type(sample[1]) is str):
            return True
        return False

    # optionname_list = __D_option.keys()

    if isinstance(exsv[0], str):
        exsv = (exsv, )
    
    print(exsv)

    assert isinstance(exsv, Sequence) and not isinstance(exsv, str), \
        f'incollect format in exclusive set {exsv}'

    # if is_pair_of_string(exsv):
    #     exsv = [exsv]

    for exset in exsv:
        print(exset)
        assert not isinstance(exset, str) and isinstance(exset, Sequence), \
            f'incollect format in exclusive list {exset}'
        assert len(exset) > 1, \
            f'incollect format in exclusive list {exset}'
        


    return
    for p in exsv:
        assert is_pair_of_string(p), \
            f'incollect format in exclusive list {p}'
        assert p[0] in optionname_list, \
            f'incollect option name "{p[0]}" for ["{p[0]}", "{p[1]}"] in exclusive list'
        assert p[1] in optionname_list, \
            f'incollect option name "{p[1]}" for ["{p[0]}", "{p[1]}"] in exclusive list'
        assert p[0] != p[1], \
            f'can\'t specify same pair for ["{p[0]}", "{p[1]}"] in exclusive list'
        self.__exclusive.append([p[0], p[1]])


__set_exclusive(["abc", "def"])
