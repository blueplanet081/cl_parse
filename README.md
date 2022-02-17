# cl_parse -- コマンドラインパーサー

## 紹介
コマンドラインのオプション、オプション引数を解析するメソッドを提供します。  
Pythonで記述するコマンドライン・プログラムに組み込んで使うものです。  
<br>

## 動作環境

 * Python 3.8以降で動きます。
   - 作成と主なテストは Python 3.8 を使用しています。
   - 3.7 でも動くと思いますが、テストしていません。
   - Enum を使っているので、3.6より古い環境では絶対に動きません。
 * Windows10/11のPowerSheel、UbuntuのBash、MacOSのBash/zsh上で動作を確認しています。

<br>

## 作成経緯

CLIベースのコマンドを試作／製作するとき、起動オプションの処理を手軽に記述したかった。Python学習も兼ねて作成しています。  
標準ライブラリ argparseの仕様を一部参考にした部分もありますが、もともとこのライブラリの使い方が分からなかった（私には難解だった）ので、もっと簡単なものを、と思って作っています。

<br>

## 特徴（宣伝）

   - オプション情報を配列で定義するだけなので、手軽に（ビジュアルに？）利用できます。
   - オプション引数は指定のデータ型に変換されるので、プログラム内で容易に（改めて変換したり、型チェックをすることなく）使えます。
   - データ型の指定は、ユーザー側で定義することもできます。（補助関数があります）
   - 入力エラー時は、エラーメッセージ文字列とともにステータスに設定されます。その後の動作はユーザープログラム（呼び出し側のプログラム）に任されます。（argparseと最も違うところかも？）
   - エラーメッセージ文字列は、ユーザー側で再定義可能です。
   - usage:を表示したり作成したりする機能はありませんが、オプション一覧はそれなりに生成する機能があります。
   - コマンド引数の後ろにオプションを入力するパターンとか、わりといろいろ対処できるようにしたつもりです。
   - Windows環境では、解析に先立ってワイルドカード展開、~展開をします。Unix/Linux上と似たような動きで使えます。（ブレース展開は現段階ではサポートしていません）
   - コマンドラインの指定により、オプション情報の設定内容や解析結果などを表示するデバッグ機能があります。

<br>

## **ファイル構成**

ファイル名                    | 内容
------------------------------|----
lib/cl_parse.py               | cl_parse本体（使うのに必要なのはこのファイルだけです）
lib/cl_parse_debugmodule.py   | cl_parse用デバッグモジュール
----------------------------- |--------------------------------------------------------
README.md         | このドキュメント
options.md        | コマンドラインの構成とか、言葉の定義とか
sample01.py       | 一番シンプルなサンプル
ptree.py          | miniparse使用サンプル。いわゆる treeコマンドの試作版です。
e2_path.py        | ptree.pyが呼び出している自作ライブラリ（添付用簡易版）

<br>

## **履歴**

バージョン   |日付     |変更箇所        | コメント 
------------|----------|---------------|------
0.9くらい   |2021/11/23|               |いちおう完成


<br>

---

## **使い方（超簡易版）**

```py
import sys
from lib import cl_parse as cl

options = [
        ["help", "-h, --help", "使い方を表示する", None],
        ["all", "-a, --all", "すべて出力"],
        ["name", "-n, --name", "使用者名を指定する//<名前>", str],
        ["count", "-c, --count", "数量を指定する//<数(整数)>", int],
        ["date", "-d, --date", "対象日//<年/月/日>", cl.strptime('%Y/%m/%d')],
]

# cl_parse 呼び出し（解析実行）
args = sys.argv
op = cl.Parse(args, options, debug=True)
```

<br>

１．パーサー呼び出し手順

  - cl_parse を importします。
  - オプション情報を定義します。（上記、options）
  - 解析するコマンドライン、オプション情報で、*\<cl_parse\>.* **Parse()** を呼び出します。

<br>

---

```py
# 解析エラー時の処理は自前で行う
if op.is_error:
    print(op.get_errormessage(1), file=sys.stderr)
    print()
    print("オプション一覧", file=sys.stderr)
    cl.tabprint(op.get_optionlist(), file=sys.stderr)
    exit(1)
```

<br>

２．解析エラー時の処理

  - 解析エラー時には、 *\<option\>.* **is_error** プロパティが **True** になります。  
    その後の動作はユーザープログラム側に任されます。
  - 解析エラーの理由は、*\<option\>.* **get_errormessage()** メソッドで取得できます。
  - ここでオプション情報を表示したいときは、定義されたオプション情報の一覧を、*\<option\>.* **get_optionlist()** メソッドで取得することができます。
  - 上記プログラム例で、 *\<cl_parse\>.* **tabprint()** は、一覧表を表示するためのサービス関数です。
  - 通常は、ここでエラー終了します。

<br>

---

```py
# help情報の表示も自前
if op.OPT_help.isEnable:       # 使い方を表示する
    print("これは cl_parse のサンプルプログラムです。\n")
    print("オプション一覧")
    cl.tabprint(op.get_optionlist())
    exit()
```

<br>

３．helpメッセージの表示

  - helpオプション（-h、--help）の設定、helpオプションが指定された場合の helpメッセージの表示も、ユーザープログラム側で行います。
  - helpオプションが指定された時の判断方法（上記で *\<option\>.* **OPT_help.isEnable**プロパティを使用）は、次項の記述を参照してください。
  - オプション情報の一覧の取得や表示は、前項の記述を参照してください。

<br>

---


```py
# 解析結果
if op.OPT_all.isEnable:        # すべて出力
    print("オプション 'all' が指定されました。")

if op.OPT_name.isEnable:       # 使用者名を指定する
    print("オプション 'name' が指定されました。")
    print(f'    {op.OPT_name.value=}')
    print()

if op.OPT_count.isEnable:       # 数量を指定する
    print("オプション 'count' が指定されました。")
    print(f'    {op.OPT_count.value=}')
    print()

if op.OPT_date.isEnable:       # 対象日
    print("オプション 'date' が指定されました。")
    print(f'    {op.OPT_date.value=}')
    print()
```


<br>

４．指定されたオプション情報の取得

  - 定義したオプションが認識されると、 *\<option\>.* **OPT_\<オプション名\>** 属性が設定されます。
  - コマンドラインで該当のオプションが指定されると、*\<option\>.* **OPT_\<オプション名\>.isEnable** プロパティが **True**に設定されます。（指定されないと、初期値 = **False**のまま）
  - オプション引数が指定されると、*\<option\>.* **OPT_\<オプション名\>.value** プロパティにその値が設定されます。（オプションが指定されない場合、及びオプション引数が省略された場合は、初期値 = **None** のまま）
  - *\<option\>.* **OPT_\<オプション名\>.value** の型（type）は、オプション情報で定義されたものに対応します。

<br>
<br>

---

<br>

## サンプルプログラム（超簡易版）


```Python :sample01.py
import sys
from lib import cl_parse as cl


args = sys.argv
# 試験用コマンドライン
if len(args) <= 1:
    args = 'this.py -a ABC --name=私だ  --date 2021/10/3 # ---#'.split()

options = [
        ["help", "-h, --help", "使い方を表示する", None],
        ["all", "-a, --all", "すべて出力"],
        ["name", "-n, --name", "使用者名を指定する//<名前>", str],
        ["count", "-c, --count", "数量を指定する//<数(整数)>", int],
        ["date", "-d, --date", "対象日//<年/月/日>", cl.strptime('%Y/%m/%d')],
]

# cl_parse 呼び出し（解析実行）
op = cl.Parse(args, options, debug=True)

# 解析エラー時の処理は自前で行う
if op.is_error:
    print(op.get_errormessage(1), file=sys.stderr)
    print()
    print("オプション一覧", file=sys.stderr)
    cl.tabprint(op.get_optionlist(), file=sys.stderr)
    exit(1)

# help情報の表示も自前
if op.OPT_help.isEnable:       # 使い方を表示する
    print("これは cl_parse のサンプルプログラムです。\n")
    print("オプション一覧")
    cl.tabprint(op.get_optionlist())
    exit()

# 解析結果
if op.OPT_all.isEnable:        # すべて出力
    print("オプション 'all' が指定されました。")

if op.OPT_name.isEnable:       # 使用者名を指定する
    print("オプション 'name' が指定されました。")
    print(f'    {op.OPT_name.value=}')
    print()

if op.OPT_count.isEnable:       # 数量を指定する
    print("オプション 'count' が指定されました。")
    print(f'    {op.OPT_count.value=}')
    print()

if op.OPT_date.isEnable:       # 対象日
    print("オプション 'date' が指定されました。")
    print(f'    {op.OPT_date.value=}')
    print()

```



## **実行例**

```text
> python3 sample01.py -a --name=わたし --date=2022/2/14 -c 12
オプション 'all' が指定されました。
オプション 'name' が指定されました。
    op.OPT_name.value='わたし'

オプション 'count' が指定されました。
    op.OPT_count.value=12

オプション 'date' が指定されました。
    op.OPT_date.value=datetime.datetime(2022, 2, 14, 0, 0)

> 
```



項目          | 型                   | 内容
--------------|----------------------|---------
第１項目      | str（文字列）        | オプション名
第２項目      | str（文字列）        | オプション文字列（複数の場合は , で区切る）
第３項目      | str（文字列）        | オプションのコメント


---


