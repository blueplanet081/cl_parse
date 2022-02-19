
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
      * 排他リスト(同時に指定してはいけないオプションのリスト）を指定する。
      * 「任意の数の排他のオプション名のリスト」、またはそのリストが複数あれば、リストのリストで指定する。
      * 省略時は空リスト。（排他のオプションはない）
   - cancelable
      * コマンドライン上で、一度指定したオプションをキャンセルする機能を有効（True）にするかどうかを指定する。
      * 省略時は、無効（False）。
      * キャンセル機能は例えば、aliasで設定されているオプションの組の一部を、実行時にキャンセルする時などに使用する。  
      　ex) ```command -alf -f- param```　で、一度設定したオプション ```-f``` のみを後からキャンセルする。
   - smode
      * パーサーがコマンドラインを解析するモードを指定する。  
      解析モードは次のものがある。
         - Smode.NONE （モードなし）  
         　args 内の全オプション、コマンド引数を解析する。
         - Smode.ONEPAIR （１組モード）  
         　オプションとコマンド引数、１組で解析を終了する。それ以降のコマンドラインは無視される。
         - Smode.OPTFIRST （オプション先モード）  
         　一度コマンド引数が指定されると、その後のオプション指定は無視される。
         - Smode.ARGFIRST （コマンド引数先モード）
         　一度オプションが指定されると、その後のコマンド引数は無視される。
      * 無視された残りのコマンドラインは *\<option\>.* **remain** に格納されるので、必要であればもう一度 parse することもできる。
      * 省略時は、Smode.NONE（モードなし） 
   - winexpand
      * True なら、Windows環境で動作時、コマンドライン中のワイルドカードを展開する。
      * 省略時は True。（展開する）
   - file_expand
      * True なら、コマンドライン中の @*\<filename\>* を展開する。（ファイル中の文字列をコマンドライン内に展開する）
      * 省略時は Flase。（展開しない）
   - emessage_header
      * コマンドライン解析エラー時の、エラーメッセージの頭に付けるコマンド名を指定する。
      * "@name" を指定した場合、拡張子を含めたコマンド名を付ける。
      * "@stem" を指定した場合、拡張子を除いたコマンド名を付ける。
      * それ以外の文字列を指定した場合、文字列そのものを付ける。何も付けたくない場合は空文字列を指定する。
      * 省略時は "@name"。（拡張子を含めたコマンド名を付ける）
   - comment_sp
      * オプション情報の「オプションのコメント」で、オプションのコメントとオプション引数のコメントの間のセパレータ文字列を指定する。
      * 省略時は "//" が指定される。
   - debug
      * デバッグ機能を有効（True）にするかどうかを指定する。
      * 省略時は無効（False）
      * 本機能が有効で、cl_parse.py モジュールと同じディレクトリに cl_parse_debugmodule.py モジュールが存在すると、デバッグ用の3ハイフン（---）オプションが有効になる。（--- で指定方法が表示されます）
   - option_name_prefix
   - option_string_prefix