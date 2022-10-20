#!/usr/bin/env python3
'''
    ptree プロトタイプ版
    2020/08/21 by te.
'''
import sys
import pathlib
from typing import List
from lib import cl_parse_old as cl
import e2_path as e2


def show_directory(path: pathlib.Path, tlist: List[int] = []):
    ''' ディレクトリ以下の情報を再帰的に表示する。
        tlistは、ディレクトリ深度を表示するためのリスト
    '''
    tlevel = len(tlist)     # ツリーレベル

    dir_list: List[pathlib.Path] = []   # そのディレクトリ内のサブディレクトリのリスト
    file_list: List[pathlib.Path] = []  # そのディレクトリ内のファイルのリスト
    for po in path.iterdir():
        if not dispAll and (e2.is_HiddenName(po) or e2.is_SystemName(po)):
            continue
        if po.is_dir():         # ディレクトリのリストを作成
            dir_list.append(po)
        elif po.is_file():      # ファイルのリストを作成
            file_list.append(po)

    if (dispTreeLevel == 0 or tlevel < dispTreeLevel) and dir_list:
        dispDirs = True
    else:
        dispDirs = False

    # strHeader0  そのディレクトリを表示する、左側のヘッダー
    strHeader0 = ''
    for pre in tlist[0:-1]:
        strHeader0 += ['|   ', '│   '][tMoji] if pre else '    '

    # strHeader1  そのディレクトリ名を表示する、左側のヘッダー
    if tlevel == 0:             # 自分のディレクトリ名を表示（ツリーの先頭の場合）
        strHeader1 = ''
    elif tlist[-1] == 1:        # 自分のディレクトリ名を表示
        strHeader1 = strHeader0 + ['|-- ', '├── '][tMoji]
    else:                       # 自分のディレクトリ名を表示（最後のディレクトリの場合）
        strHeader1 = strHeader0 + ['+-- ', '└── '][tMoji]

    # strHeader2  そのディレクトリ内の情報を表示する、左側のヘッダー
    strHeader2 = strHeader0
    if tlevel != 0:
        strHeader2 += ['|   ', '│   '][tMoji] if tlist[-1] else '    '
    strHeader2 += ['|   ', '│   '][tMoji] if dispDirs else '   '

    print(strHeader1 + str(path))   # 自分のディレクトリ名を表示

    print(strHeader2 + f'dirs = {len(dir_list)}  files = {len(file_list)}')

    if dispFiles and file_list:
        print(strHeader2 + ' ',
              "ctime".ljust(17),
              "mtime".ljust(17),
              "length".rjust(8),
              "name"
              )
        for fn in file_list:            # ファイル名表示
            print(strHeader2 + ' ',
                  e2.get_dtctime(fn).strftime("%Y/%m/%d %H:%M "),
                  e2.get_dtmtime(fn).strftime("%Y/%m/%d %H:%M "),
                  f"{e2.get_fileSize(fn):>8,}",
                  fn.name)
    print(strHeader2)

    if dispDirs:              # ディレクトリあり→下位のディレクトリに潜る
        for po in dir_list[0:-1]:
            show_directory(po, tlist + [1])
        show_directory(dir_list[-1], tlist + [0])   # 最後のディレクトリ


''' ここからメイン ---------------------------- '''

options = [
        ["all", "-a, --all", 'ドットやシステムディレクトリも表示'],
        ["level", "-L, --level", '表示するディレクトリの深さを指定する//<深さ>', int],
        ["directoryonly", "-d, --directory-only", 'ディレクトリのみ表示'],
        ["extrachar", "-e, --extra-char", 'ツリーの表示に拡張文字を使用'],
        ["help", "-h, --help", '使い方を表示する'],
]

ps = cl.Parse(sys.argv[1:], options,  debug=True)

# オプションエラー処理
if ps.is_error:
    print(ps.get_errormessage(1), file=sys.stderr)
    print("オプション一覧", file=sys.stderr)
    cl.tabprint(ps.get_optionlist(), [18, 4], file=sys.stderr)
    exit(1)

if ps.OPT_["help"].isEnable:            # 使い方を表示する
    print('ディレクトリやファイルのツリーを表示します。')
    print()
    print("usage: ptree [-ade][-L <int>] | [-h]  [開始ディレクトリ]")
    cl.tabprint(ps.get_optionlist(), [18, 4], file=sys.stderr)
    exit()

args = ps.params
if args:
    path = pathlib.Path(args[0])
    if not path.is_dir():
        print(f'無効なディレクトリです {path}', file=sys.stderr)
        sys.exit(1)

else:
    path = pathlib.Path('.')

tMoji = 0                   # tree表記に使う文字種類  0: ASCII記号、1:拡張文字
dispFiles: bool = True      # ファイル情報を表示するかどうか
dispAll: bool = False       # すべてのファイル／ディレクトリを表示するかどうか
dispTreeLevel = 0           # 表示するツリーの深さ（0 は無制限）

if ps.OPT_["all"].isEnable:             # ドットやシステムディレクトリも表示
    dispAll = True

if ps.OPT_["directoryonly"].isEnable:   # ディレクトリのみ表示
    dispFiles = False

if ps.OPT_["extrachar"].isEnable:       # ツリーの表示に拡張文字を使用
    tMoji = 1

if ps.OPT_["level"].isEnable:           # 表示するディレクトリの深さを指定する
    dispTreeLevel = ps.OPT_["level"].value

show_directory(path.resolve())
