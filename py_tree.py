'''
Treeviewのテスト（パソコン内のフォルダを階層表示する）
2022/10/11  by te.
'''
from typing import Any, List, Callable, Iterable, NamedTuple, Tuple, Dict
from pathlib import Path
from enum import Enum, auto
import e2_path as e2
from fnmatch import fnmatch


# -------------------------------------------------------------------
# 汎用モジュール
# -------------------------------------------------------------------
class S_Stack():
    def __init__(self, items: List[Any] = []) -> None:
        ''' 超簡易stack、push/pop/len()だけ実装。
            items: stackに積む itemのリスト
        '''
        self.__stack: List[Any] = items[::-1] if items else []

    def push(self, item: Any):
        self.__stack.append(item)

    def pop(self) -> Any:
        return self.__stack.pop() if len(self.__stack) else None

    def __len__(self) -> int:
        return len(self.__stack)


# -------------------------------------------------------------------
# 内部関数（Model）
# -------------------------------------------------------------------
class Ps(Enum):
    ''' 表示するパスの種類 '''
    FULL = auto()       # フルパス
    RELATIVE = auto()   # 相対パス
    NAMEONLY = auto()   # 単独（名前のみ）


class Options():
    ''' tree描画オプション '''
    inhibits: List[Callable[[str], bool]] = []  # 内部を展開しないディレクトリ条件
    pathtype: Ps = Ps.RELATIVE                  # 表示するディレクトリ名のパスの種類
    ascii: bool = False                         # tree表示にascii文字を使う
    wild: str = ""                              # 表示するファイル名（ワイルドカード）
    unmatch: str = ""                           # 表示しないファイル名（ワイルドカード）


class Footprint(NamedTuple):
# class Footprint():
    ''' iter_walk2の戻り値用「足跡」 '''
    # path: Path          # ディレクトリパス
    remain: int         # 親ディレクトリ内の、残りのディレクトリの数
    contain: int        # 子ディレクトリの数
    files: List[Path]   # ディレクトリ内の、検出したファイル(Path)のリスト
    result: str         # 空文字列: 正常、'p': 権限なし、'i': 展開しない


def select_files(p: Path, wild: str) -> List[Path]:
    ''' 指定ディレクトリ内の、ワイルドカードで指定したファイル(Path)のリストを返す
        p: ディレクトリのPath
        wild: ワイルドカード（空文字列の場合は全ファイルのリストを返す）
    '''
    if wild:
        # print(p.name, wild)
        return [q for q in p.iterdir() if q.is_file() and fnmatch(q.name, wild)]
    return [q for q in p.iterdir() if q.is_file()]


def subtract_files(files: List[Path], wild: str) -> List[Path]:
    ''' ワイルドカードで指定したファイルを削除したファイル(Path)のリストを返す
        files: 元のファイル(Path)のリスト
        wild: 削除するファイル名のワイルドカード（空文字列の場合は元のリストをそのまま返す）
    '''
    if wild:
        return [p for p in files if not fnmatch(p.name, wild)]
    return files


def iter_walk2(p: Path, op: Options) -> Iterable[Tuple[Path, Footprint]]:
    ''' 指定された先頭のディレクトリ配下にあるディレクトリを walkして返すイテレータ
        p: 先頭のディレクトリ
        inhibit: 中を探索しない、ディレクトリ名の条件
    '''
    def is_inhibit(s: str) -> bool:
        ''' 中を探索しないディレクトリ名かどうか '''
        for func in op.inhibits:
            if func(s):
                return True
        return False

    def get_dirs(p: Path) -> Tuple[List[Path], str]:
        ''' ディレクトリ内のディレクトリリストと、結果を返す
            結果: 空文字列: 正常、'p': 権限なし、'i': 展開しなかった
        '''
        if not is_inhibit(p.name):  # inhibit条件に該当しない場合のみ
            try:
                return [x for x in p.iterdir() if x.is_dir()], ''
            except PermissionError:     # 権限の無いディレクトリはパス
                return [], 'p'              # 権限エラー
        return [], 'i'  # 展開しなかった

    # -------------------------------------------------------------------------------------
    files: List[Path] = []

    dirstack = S_Stack()            # ディレクトリ一覧のスタック
    dirlist, result = get_dirs(p)
    dirs = S_Stack(dirlist)     # ディレクトリ配下のディレクトリ一覧のスタック

    if not result:
        workfiles = select_files(p, op.wild)
        files = subtract_files(workfiles, op.unmatch)

    yield p, Footprint(len(dirs), len(dirlist), files, result)

    dirstack.push(dirs)             # 現在のディレクトリ一覧を push
    while((dirs := dirstack.pop()) is not None):    # ディレクトリ一覧
        while(node := dirs.pop()):      # ディレクトリ一覧の中のディレクトリを pop
            subdirs, result = get_dirs(node)
            files = []
            if not result:
                workfiles = select_files(node, op.wild)
                files = subtract_files(workfiles, op.unmatch)
            yield node, Footprint(len(dirs), len(subdirs), files, result)

            wdirs = S_Stack(subdirs)        # 下位のディレクトリ一覧を取得
            if len(wdirs) > 0:                  # 下位ディレクトリが存在した
                dirstack.push(dirs)                 # 現在のディレクトリ一覧を push
                dirs = wdirs                        # 下位ディレクトリに移って続行
    return


def iter_prune(iwalk: Iterable[Tuple[Path, Footprint]]):
    ws_dict: Dict[Path, Footprint] = {}
    for p, node in iwalk:
        if len(node.files) <= 0 and node.contain <= 0:
            print(f"reject {str(p)}")
            p = p.parent
            # while(p != p.parent):
            #     print(f"    {str(p)}")
            #     data = ws_dict.get(p, "END")
            #     print(f'    {data}')
            #     p = p.parent
            while(data := ws_dict.get(p, None)):
                print(f"    {str(p)}, {data.contain=}, {len(data.files)=}")
                if len(data.files) > 0:
                    break
                if data.contain >= 1:
                    ws_dict[p] = Footprint(node.remain, node.contain - 1, node.files, node.result)
                p = p.parent

            continue
        ws_dict[p] = node

    for p, fp in ws_dict.items():
        print(str(p), f'{fp.contain=}, {len(fp.files)=}, {fp.result=}')


def edit_filelist(files: List[Path], ) -> List[str]:
    ''' ファイル(Path)のリストから、表示用のファイル情報の一覧を作成する '''
    ret: List[str] = []
    # files = [f for f in p.iterdir() if f.is_file()]
    if files:
        ret.append("ctime-----------  mtime-----------  --length  filename----")
        for f in files:
            dtctime = e2.get_dtctime(f).strftime("%Y/%m/%d %H:%M")
            dtmtime = e2.get_dtmtime(f).strftime("%Y/%m/%d %H:%M")
            length = format(e2.get_fileSize(f), ',').rjust(8)
            ''' memo
                数字を表示する桁数を調べるには、文字列にして len()
                カンマを入れないなら、len(整数) でも桁数を得られる
                （もし、size表示が 8桁を越える場合の検出方法）
            '''
            fname = f.name
            ret.append(f'{dtctime}  {dtmtime}  {length}  {fname}')
            # ret.append(f.name)
    return ret


# -------------------------------------------------------------------
# 描画処理（View）
# -------------------------------------------------------------------
def make_pathname(p: Path, head: Path, ps: Ps) -> str:
    ''' 表示用のディレクトリ名を作成する
        p: ディレクトリのPath
        head: 相対パスの先頭のPath
        ps: フルパスか、相対パスか、ディレクトリ名のみか
    '''
    if ps is Ps.FULL:       # フルパスで表示
        return str(p)
    if ps is Ps.RELATIVE:   # 先頭Pathからの相対パスで表示
        return str(p.relative_to(head.parent))
    return p.name           # ディレクトリ名のみを表示


def print_tree(head: Path, t_op: Options = Options()):
    ''' tree描画（本体）
        head: 先頭のディレクトリのパス
        op: 描画オプション
    '''
    str_vline = ["| ", "│  "]   # 階層表示用の縦線
    str_remain = ["|-", "├─"]   # 途中のディレクトリ表示用
    str_last = ["+-", "└─"]     # 親ディレクトリ内の最後のディレクトリ表示用

    def header(tlist: List[int]) -> str:
        ''' 階層表示、共通部分 '''
        ret = ""
        for d in tlist:
            ret += (str_vline[tMoji] if d else "    ")
        return ret

    def header0(tlist: List[int], remain: int) -> str:
        ''' ディレクトリ名表示用ヘッダー
            remain: 同レベルの、残りのディレクトリの数
        '''
        if tlist:
            return header(tlist[:-1]) + (str_remain[tMoji] if remain else str_last[tMoji])
        return ""

    def header1(tlist: List[int], contain: int) -> str:
        ''' その他表示用ヘッダー
            contain: そのディレクトリ配下のディレクトリの数
        '''
        return header(tlist) + (str_vline[tMoji] if contain else "    ")

    tMoji = 0 if t_op.ascii else 1
    tlist: List[int] = []

    d_base = len(head.parents)
    print(head, d_base)

    for p, node in iter_walk2(head, t_op):
        d_level = len(p.parents) - d_base                   # headからのnode階層

        dirname = make_pathname(p, head, t_op.pathtype)       # 表示するディレクトリ名
        mark = "[*]" if node.result == 'i' else "[e]" if node.result == 'p' else ""

        tlist = tlist[:d_level] + ([1] if node.remain else [0])     # treeの縦線フラグリスト
        print(header0(tlist[1:], node.remain) + dirname, mark)

        headern = header1(tlist[1:], node.contain)

        for s in edit_filelist(node.files):
            print(headern + "  " + s)
        print(headern)

    iter_prune(iter_walk2(head, t_op))

if __name__ == "__main__":
    # 内部を見ないディレクトリ条件
    inhibits: List[Callable[[str], bool]] = [
        lambda s: s.startswith("."),
        lambda s: s.endswith("cache"),
        lambda s: (s.startswith("__") and s.endswith("__"))
    ]

    option = Options()
    option.ascii = False
    option.pathtype = Ps.RELATIVE
    option.inhibits = inhibits
    option.wild = '*pa*'
    option.unmatch = ''

    # p = Path(r'C:\Users\bluep\myproject\code39b\tk')
    # p = Path(r'C:\Users\bluep\myproject\code39')
    p = Path(r'C:\Users\bluep\myproject\code39\test')
    print_tree(p, option)
