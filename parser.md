
## パーサー（Parse）呼び出し形式

<br>

### 呼び出し例
op = Parse(args, options, exclusive=exclusive, cancelable=True, debug=True, emessage_header="@stem")

<br>

### 定義
```py
class Parse:
    def __init__(self,
                 args: List[str],                   # 解析するコマンドライン
                 options: List[List[Any]],
                 exclusive: Union[List[List[str]], List[str]] = [],     # 排他リスト
                 cancelable: bool = False,          # オプションキャンセル可能モード
                 smode: Smode = Smode.NONE,         # 解析モード
                 winexpand: bool = True,            # Windowsで、ワイルドカードを展開するかどうか
                 file_expand: bool = False,         # コマンド引数の @<filename> を展開するかどうか
                 emessage_header: str = "@name",    # エラーメッセージの頭に付けるプログラム名
                 comment_sp: str = '//',            # オプションコメントのセパレータ
                 debug: bool = False,               # デバッグ指定（--@ で結果一覧出力）
                 option_name_prefix: str = "OPT_",  # 自プログラム内でオプションを指定する時のprefix
                 option_string_prefix: str = "-",   # オプションの前に付ける - とか --
                 ) -> None:
```
<br>

### 引数の一覧
引数名     | 引数の型      | 省略時           | 内容
-----------|---------------|------------------|------------------------------
args       |List[str]      |省略不可          |解析するコマンドライン
options    |List[List[Any]]|省略不可          |オプション情報
exclusive  |Union[List[List[str]], List[str]] |空リスト|排他リスト
cancelable |bool           |False             |オプションキャンセル可能モード
smode      |Smode          |Smode.NONE        |解析モード
winexpand  |bool           |True              |Windowsで、ワイルドカードを展開するかどうか
file_expand  |bool         |False             |コマンド引数の @<filename> を展開するかどうか
emessage_header|str        |"@name"           |エラーメッセージの頭に付けるプログラム名
comment_sp |str            |'//'              |オプションコメントのセパレータ
debug      |bool           |False             |デバッグ指定（--@ で結果一覧出力）
option_name_prefix  |str   |"OPT_"            |自プログラム内でオプションを指定する時のprefix
option_string_prefix|str   |"-"               |オプションの前に付ける - とか --

<br>

### 引数の説明

  - args
    * 解析するコマンドラインが格納されている、文字列リストを指定する。
    * sys.argv を渡すと、先頭のプログラム名もコマンド引数として解釈する。不都合であれば、sys.argv[1:] を指定してください。
  - options
    * オプション情報を格納したリストを指定する。
    * オプション情報の格納方法、内容の説明は別途。
  - exclusive
    * 