
## パーサー（Parse）呼び出し形式

<br>

### 呼び出し例
ps = cl.Parse(args, options, exclusive=exclusive, cancelable=True, debug=True, emessage_header="@stem")

<br>

### 定義
```py
class Parse:
    def __init__(self,
                 args: List[str],                   # 解析するコマンドライン
                 options: List[List[Any]],          # オプション情報
                 exclusive: Union[List[List[str]], List[str]] = [],     # 排他オプションリスト
                 cancelable: bool = False,          # オプションキャンセル可能モード
                 smode: Smode = Smode.NONE,         # 解析モード
                 winexpand: bool = True,            # Windowsで、ワイルドカードを展開するかどうか
                 file_expand: bool = False,         # コマンド引数の @<filename> を展開するかどうか
                 emessage_header: str = "@name",    # エラーメッセージの頭に付けるコマンド名
                 comment_sp: str = '//',            # オプションコメントのセパレータ
                 debug: bool = False,               # デバッグ機能を有効にする
                 option_name_prefix: str = "OPT_",  # オプション属性を生成する時のprefix
                 option_string_prefix: str = "-",   # オプションの前に付ける - とか --
                 ) -> None:
```
<br>

### 引数の一覧
引数名     | 引数の型      | 省略時           | 内容
-----------|---------------|------------------|------------------------------
args       |List[str]      |省略不可          |解析するコマンドラインの文字列リスト
options    |List[List[Any]]|省略不可          |オプション情報
exclusive  |Union[List[List[str]], List[str]] |空リスト|排他オプションリスト
cancelable |bool           |False             |オプションキャンセル可能モードを有効にする
smode      |*\<cl_parse>.* Smode  |*\<cl_parse>.* Smode.NONE        |解析モードを指定する
winexpand  |bool           |True              |Windowsで、ワイルドカードを展開するかどうか
file_expand  |bool         |False             |コマンド引数の @\<filename> を展開するかどうか
emessage_header|str        |"@name"           |エラーメッセージの頭に付けるコマンド名を指定する
comment_sp |str            |'//'              |オプションコメントのセパレータ
debug      |bool           |False             |デバッグ機能を有効にする（--- で機能一覧）
option_name_prefix  |str   |"OPT_"            |オプション属性を生成する時のprefix
option_string_prefix|str   |"-"               |オプションの前に付ける - とか -- を設定する

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
         - *\<cl_parse>.* Smode.NONE （モードなし）  
         　args 内の全オプション、コマンド引数を解析する。
         - *\<cl_parse>.* Smode.ONEPAIR （１組モード）  
         　オプションとコマンド引数、１組で解析を終了する。それ以降のコマンドラインは無視される。
         - *\<cl_parse>.* Smode.OPTFIRST （オプション先モード）  
         　一度コマンド引数が指定されると、その後のオプション指定は無視される。
         - *\<cl_parse>.* Smode.ARGFIRST （コマンド引数先モード）  
         　一度オプションが指定されると、その後のコマンド引数は無視される。
      * 無視された残りのコマンドラインは *\<Parse\>.* **remain** に格納されるので、必要であればもう一度 parse することもできる。
      * 省略時は、*\<cl_parse>.* Smode.NONE（モードなし） 
   - winexpand
      * True なら、Windows環境で動作時、コマンドライン中のワイルドカードを展開する。
      * 省略時は True。（展開する）
   - file_expand
      * True なら、コマンドライン中の @*\<filename\>* を展開する。（ファイル中の文字列をコマンドライン内に展開する）
      * 省略時は Flase。（展開しない）
   - emessage_header
      * コマンドライン解析エラー時の、エラーメッセージの頭に付けるコマンド名を指定する。
      * "@name" を指定した場合、拡張子を含めたコマンド名を付ける。  
        　ex) sample01.py E12: illegal argument for option --date=2022-3-1
      * "@stem" を指定した場合、拡張子を除いたコマンド名を付ける。  
        　ex) sample01 E12: illegal argument for option --date=2022-3-1
      * それ以外の文字列を指定した場合、文字列そのものを付ける。何も付けたくない場合は空文字列を指定する。  
        　ex) 入力エラーだ！ E12: illegal argument for option --date=2022-3-1  
        　　（emessage_header="入力エラーだ！" を指定時）
      * 省略時は "@name"。（拡張子を含めたコマンド名を付ける）
      * メッセージ中のエラー番号が不要とか、メッセージそのものがヘン、とか言う場合は、エラーメッセージそのものを編集、または上書きしてください。
   - comment_sp
      * オプション情報の「オプションのコメント」で、オプションのコメントとオプション引数のコメントの間のセパレータ文字列を指定する。
      * 省略時は "//" が指定される。  
        　ex) "表示サイズを指定する//<縦x横>"  
        　　->　"表示サイズを指定する" がオプションのコメント、 "<縦x横>" がオプション引数のコメント。
   - debug
      * デバッグ機能を有効（True）にするかどうかを指定する。
      * 省略時は無効（False）
      * 本機能が有効で、cl_parse.py モジュールと同じディレクトリに cl_parse_debugmodule.py モジュールが存在すると、デバッグ用の3ハイフン（---）オプションが有効になる。（--- で指定方法が表示されます）
   - option_name_prefix
      * オプション属性を生成するためのプリフィックス文字列を指定する。
      * 省略時は "OPT_" が指定される。
      * 例えば、オプション名 "all" に対して、OPT_all という名前の属性が生成される。
      * 生成された属性名が、Pythonの変数名として成立する必要がある。（先頭が数字はダメとか）
   - option_string_prefix
      * コマンドライン上でオプションとして認識されるためのプリフィックス文字を指定する。
      * 省略時は "-" が指定され、-x が１文字オプション、--xxxxx がロング名オプションとして認識される。
      * 例えば、プリフィックスはどうしても "/" を使いたい、と言う時に使えるけど、実際に使ってみたら気持ち悪かった。(\*_*)
