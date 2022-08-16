#葉をフチをエッジ検出し、繋げたあとにそれぞれ外接矩形に画像を切り出す
#切り抜いた画像名にはimg_list.csvに記入した処理区と葉の番号を適用

import glob
import cv2
import numpy as np
from pathlib import Path
import pandas as pd
import re

#画像の処理区をimg_list.csvから取得する
csv_input = pd.read_csv("img_list.csv",skiprows=0)
fig_list=csv_input.iloc[:,2].tolist()

#葉の面積を入れる用リスト
Area_list = []

#pass_listの順番が1～になるようにするためにつかう
def atoi(text):
    return int(text) if text.isdigit() else text
def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

#\を/に置換したリストを作る
pass_list = sorted(glob.glob('fig/raw/*.jpg', ), key=natural_keys)
pass_list_exc=[]
for file in pass_list:
    # 置換
    repl=file.replace("\\","/")
    #　リストに追加
    pass_list_exc.append(repl)

#img_list.csvのどの処理区名を適用するかに使う
treat_num = 0

#rawフォルダの画像を1枚ずつ処理する
for list in pass_list_exc:

    #元の画像名をlistNoに設定する
    listNo = list.replace("fig/raw/","")
    listNo = listNo.replace(".jpg","")

    # 白黒で画像読み込み
    gray_img = cv2.imread(list, 0)

    # sigmaColor: 色についての標準偏差。これが大きいと、画素値の差が大きくても大きな重みが採用される
    biFill1 = 10
    # sigmaSpace: 距離についての標準偏差。これが大きいと、画素間の距離が広くても大きな重みが採用される。
    biFill2 = 10
    # バイテラルフィルターでエッジを残しながら平滑化
    img_bi = cv2.bilateralFilter(gray_img, 9, biFill1, biFill2)

    # Cannyの引数定義
    # 検出されたエッジの友達(閾値以下)をどれだけ許すかライン　0なら全員OK
    threshold1 = 10
    # エッジを検出する閾値
    threshold2 = 5
    # 葉のエッジを検出する
    edge_img = cv2.Canny(img_bi, threshold1, threshold2)

    # 大きさ用の凡例を塗りつぶして消す
    cv2.rectangle(edge_img, (0, 0), (900, 1800), (0, 0, 0), thickness=-1)

    # クロージング処理　検出したエッジをつなげる
    # 膨張，縮小を10回ずつ
    kernel = np.ones((3, 3), np.uint8)
    edge_img = cv2.morphologyEx(edge_img, cv2.MORPH_CLOSE, kernel, iterations=5)

    # エッジを繋げて作った輪郭を検出する
    img_con = edge_img.copy()
    contours, hierarchy = cv2.findContours(img_con, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 全ての輪郭を書き込んで出力
    img_bw = img_con.copy()
    # 白で書き込む,最後の－１でfillする
    cv2.drawContours(img_bw, contours, -1, (255, 255, 255), -1)

    # オープニング処理　ノイズを除去
    img_bw = cv2.morphologyEx(img_bw, cv2.MORPH_OPEN, kernel, iterations=5)

    # 保存するディレクトリを作成する。
    check_dir = Path("fig/check")
    check_dir.mkdir(exist_ok=True)

    # 「白黒の元画像」と「輪郭を検出した画像」を結合させた画像を保存
    # うまく輪郭を検出できていない部分があるか確認する
    check_save_path = check_dir / f"{listNo}.jpg"
    cropped = cv2.bitwise_not(img_bw)
    imgs = cv2.hconcat([gray_img, cropped])
    cv2.imwrite(str(check_save_path), imgs)

    # 輪郭の検出
    contours, hierarchy = cv2.findContours(img_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #葉の1枚1枚を区別して命名するのにつかう
    leaf_num=0

    # 外接矩形を１つずつ保存
    for i in range(len(contours)):

        # 小さい輪郭は無視する。
        if cv2.contourArea(contours[i]) < 50000:
            continue

        leaf_num=leaf_num+1
        im_rectangle = img_bw.copy()

        # 外接矩形の座標を保存 (左上のxy座標，幅，高さ)　
        x, y, w, h = cv2.boundingRect(contours[i])
        # 塗りつぶしてある葉の面積を取得する
        leaf_area = cv2.contourArea(contours[i])

        #葉のNoと面積表示 122679.5は左上の大きさ用凡例の数値
        #凡例の大きさの数値は適時調節する
        legend_size = 122679.5
        #凡例の実際の大きさ（25cm^2）
        legend_cm2 = 25
        #凡例を使って実際の葉の大きさを計算する（cm^2、整数に値を丸める）
        leaf_cm2 = round((leaf_area / legend_size) * legend_cm2, 0)

        #コンソールに処理中のファイル名を出力
        print(f"{fig_list[treat_num]}_{leaf_num}")
        print("leaf_area : ", leaf_cm2)
        #葉の面積をArea_listに入れていく
        Area_list.append(leaf_cm2)

        # 外接矩形に切り抜く
        crop_img = im_rectangle[y:y + h, x:x + w]

        # 保存するディレクトリを作成する。
        output_dir = Path("fig/output")
        output_dir.mkdir(exist_ok=True)

        # 外接矩形に切り抜いた葉の画像を保存する
        save_path = output_dir / f"{fig_list[treat_num]}_{leaf_num}.jpg"
        cropped = cv2.bitwise_not(crop_img)
        cv2.imwrite(str(save_path), cropped)

    #次の処理区名に移動するのに使う
    treat_num = treat_num + 1

#葉面積をCSVに書き出し (cm^2)
df = pd.DataFrame(Area_list)
df.to_csv('fig/output_leaves_area.csv')