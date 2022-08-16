
import glob
import pandas as pd
import re

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

#\を/に置換したリストを作る
pass_list = sorted(glob.glob('fig/raw/*.jpg', ), key=natural_keys)
pass_list_exc=[]
for file in pass_list:
    # print(file)
    # 置換
    repl=file.replace("\\","/")
    repl = repl.replace("fig/raw/", "")
    repl = repl.replace(".jpg", "")
    # print(repl)
    #　リストに追加
    pass_list_exc.append(repl)


#画像リストをCSVに書き出し
df = pd.DataFrame(pass_list_exc)
df.to_csv('img_list.csv')