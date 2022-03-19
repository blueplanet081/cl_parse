# -----------------------------------------------------
# エラーメッセージのテンプレート
# -----------------------------------------------------
emsg = {
    "N00": "no error",
    "E01": "{eno}: FileNotFoundError at {arg}",
    "E11": "{eno}: argument required for option {arg}",
    "E12": "{eno}: illegal argument specified for option {arg}",
    "E13": "{eno}: unnecessary argument specified for option {arg}",
    "E14": "{eno}: illegal option {arg}",
    "E21": "{eno}: argument required for option {opt} in {arg}",
    "E22": "{eno}: illegal argument specified for option {opt} in {arg}",
    "E23": "{eno}: illegal option {opt} in {arg}",
    "E31": "{eno}: exclusive option between ({ext0}) and ({ext1})",
    "E31x": "oputions ext0 and ext1 are mutually exclusive",
    "E99": "{eno}: unknown error opt={opt}, arg={arg}, ext0={ext0}, ext1={ext1}",
}