# -------------------------------------------------------------
# コマンドラインパーサー cl_parse用変換関数     2022/2/2 by te.
# -------------------------------------------------------------
from __future__ import annotations
from typing import Any, Optional
from collections.abc import Callable
from datetime import datetime as dt


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
# sepalate_items(type=int_literal, sep='x', count=2) みたいな使い方をする


def str_choices__(arg: str, choices: List[str]) -> str:
    """ オプション引数が選択肢()内にあるかどうか判定する。
        エラー時の処理が cl_parse 用
    """
    if arg not in choices:
        raise ValueError(f'choices error. "{arg}" not in {choices}')
    return arg


str_choices = Mu2(Mu, str_choices__)


# int_literal = functools.partial(int, base=0)
int_literal = Mu(int, base=0)           # 数値リテラル（"0x4F3e"みたいな）を解釈するタイプ
date = Mu(dt.strptime, '%Y/%m/%d')      # 日付 <年>/<月>/<日> 入力
strptime = Mu2(Mu, dt.strptime)
