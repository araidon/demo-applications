import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import calendar
import traceback
from bs4 import BeautifulSoup
import re
from datetime import datetime

def get_historical_temperature(year, month, location_info, debug=False, precipitation=False):
    """指定した年月の指定地域の気温データを取得する関数。雨や雪の情報も取得可能。"""
    
    # データを格納するリスト
    temp_data = []
    
    try:
        # 気象庁の過去データAPI - 選択した地域のデータを取得
        base_url = f'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no={location_info["prec_no"]}&block_no={location_info["block_no"]}&year={year}&month={month:02d}&day=1&view='
        
        if debug:
            st.write(f"取得URL: {base_url}")
        
        # リクエスト送信
        with st.spinner('気象データをダウンロード中...'):
            response = requests.get(base_url)
            response.encoding = 'utf-8'
        
        # BeautifulSoupでHTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 日別データの表を探す
        table = soup.select_one('table.data2_s')
        
        if table is None:
            st.error("データ表が見つかりませんでした")
            return None
            
        # 表の行を取得 (クラス名をより柔軟に)
        rows = table.find_all('tr')
        
        # 列のインデックス初期値（デバッグのために保持）
        max_temp_idx = 7  # デフォルト値
        min_temp_idx = 8  # デフォルト値
        weather_day_idx = 19  # デフォルト値（デバッグ出力から昼の天気は19番目とわかった）
        weather_night_idx = 20  # デフォルト値（夜の天気は20番目）
        
        # テーブル構造を分析: 最初に2段組のヘッダーを分析
        header_rows = [row for row in rows if 'header' in row.get('class', [])]
        
        if len(header_rows) >= 2:  # 2段組ヘッダーの場合
            # 1段目のヘッダー
            first_headers = [cell.text.strip() for cell in header_rows[0].find_all(['th', 'td'])]
            # 2段目のヘッダー
            second_headers = [cell.text.strip() for cell in header_rows[1].find_all(['th', 'td'])]
            
            if debug:
                with st.expander("ヘッダー情報"):
                    st.write("1段目ヘッダー:")
                    for i, h in enumerate(first_headers):
                        st.write(f"[{i}] {h}")
                    st.write("\n2段目ヘッダー:")
                    for i, h in enumerate(second_headers):
                        st.write(f"[{i}] {h}")
            
            # 列を特定（気温(℃)の列の下にある最高/最低）
            temp_col_idx = -1
            for i, header in enumerate(first_headers):
                if '気温' in header and '℃' in header:
                    temp_col_idx = i
                    break
            
            # 天気概況の列も特定
            weather_col_idx = -1
            for i, header in enumerate(first_headers):
                if '天気概況' in header:
                    weather_col_idx = i
                    break
            
            if temp_col_idx >= 0 and len(second_headers) > temp_col_idx:
                # 温度カラムの下にある各項目を走査
                offset = 0
                for i in range(temp_col_idx, min(temp_col_idx + 10, len(second_headers))):
                    if '最高' in second_headers[i]:
                        max_temp_idx = i
                    if '最低' in second_headers[i]:
                        min_temp_idx = i
                    offset = i
            
            if weather_col_idx >= 0:
                # 天気概況カラムの下にある項目を走査
                for i in range(weather_col_idx, len(second_headers)):
                    if '昼' in second_headers[i]:
                        weather_day_idx = i
                    if '夜' in second_headers[i]:
                        weather_night_idx = i
        
        if debug:
            st.write(f"検出した列インデックス: 最高気温={max_temp_idx}, 最低気温={min_temp_idx}, 昼の天気={weather_day_idx}, 夜の天気={weather_night_idx}")
            
        # プログレスバー用意
        progress_bar = st.progress(0)
        total_rows = len([r for r in rows if 'mtx' in str(r.get('class', []))])
        processed_rows = 0
        
        # 日ごとのデータを取得（データ行だけ処理）
        for row in rows:
            if 'mtx' not in str(row.get('class', [])):  # データ行だけを処理
                continue
                
            cells = row.find_all('td')
            if not cells or len(cells) < 5:  # 少なくともいくつかのセルがあること
                continue
                
            try:
                # 日付を取得
                day_text = cells[0].text.strip()
                day_match = re.search(r'(\d+)', day_text)
                if not day_match:
                    continue
                    
                day = int(day_match.group(1))
                
                # 最高気温/最低気温の取得（インデックスが範囲内かチェック）
                max_temp = None
                min_temp = None
                
                if len(cells) > max_temp_idx:
                    max_temp_str = cells[max_temp_idx].text.strip()
                    # 欠損値チェックを強化
                    if max_temp_str and max_temp_str not in ['//', '--', '']:
                        try:
                            max_temp = float(max_temp_str)
                        except ValueError:
                            if debug:
                                st.write(f"最高気温の変換エラー: '{max_temp_str}'")
                
                if len(cells) > min_temp_idx:
                    min_temp_str = cells[min_temp_idx].text.strip()
                    # 欠損値チェックを強化
                    if min_temp_str and min_temp_str not in ['//', '--', '']:
                        try:
                            min_temp = float(min_temp_str)
                        except ValueError:
                            if debug:
                                st.write(f"最低気温の変換エラー: '{min_temp_str}'")
                
                # どちらも欠損値ならスキップ
                if max_temp is None and min_temp is None:
                    if debug:
                        st.write(f"{day}日のデータ: 気温データなし")
                    continue
                
                # 天気情報の取得
                precip_type = None
                if precipitation:
                    day_weather = ""
                    night_weather = ""
                    
                    if len(cells) > weather_day_idx:
                        day_weather = cells[weather_day_idx].text.strip()
                    if len(cells) > weather_night_idx:
                        night_weather = cells[weather_night_idx].text.strip()
                    
                    # デバッグ出力
                    if debug and (day == 1 or day % 10 == 0):  # 最初と10日ごとに表示
                        st.write(f"日付: {day}日, 昼の天気: '{day_weather}', 夜の天気: '{night_weather}'")
                    
                    # 雨や雪の判定（雪があれば優先、なければ雨をチェック）
                    weather_text = day_weather + night_weather
                    if '雪' in weather_text or 'みぞれ' in weather_text:
                        precip_type = 'snow'
                    elif '雨' in weather_text:
                        precip_type = 'rain'
                        
                # データを追加
                data_dict = {
                    'date': f'{year}-{month:02d}-{day:02d}',
                    'max_temp': max_temp,
                    'min_temp': min_temp
                }
                
                if precipitation:
                    data_dict['precipitation'] = precip_type
                    
                temp_data.append(data_dict)
                
                # プログレスバー更新
                processed_rows += 1
                progress_bar.progress(processed_rows / total_rows)
                
                if debug and day == 1:  # 最初の日だけ全セルの内容を表示
                    with st.expander(f"{day}日のデータ詳細"):
                        for i, cell in enumerate(cells):
                            st.write(f"セル[{i}]: '{cell.text.strip()}'")
                
            except Exception as e:
                if debug:
                    st.write(f"エラー発生 (日付 {day if 'day' in locals() else '不明'}日): {str(e)}")
                continue
        
        # データフレーム化
        df = pd.DataFrame(temp_data)
        if len(df) > 0:
            df['date'] = pd.to_datetime(df['date'])
            st.success(f"{year}年{month}月の気温データ取得完了！ {len(df)}件のデータ")
            return df
        else:
            st.error("データが見つかりませんでした")
            return None
            
    except Exception as e:
        st.error(f"エラー発生: {str(e)}")
        if debug:
            st.code(traceback.format_exc())
        return None

def plot_temperature(df, year, month, show_precipitation=False):
    """最高気温と最低気温の推移をプロットする関数。雨や雪の日も表示可能。"""
    if df is None or len(df) == 0:
        st.error("プロット用データがありません")
        return
        
    # プロットの設定
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 英語表記用の月名マッピング
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                  7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    
    # x軸用のデータ作成（日付の日の部分のみ）
    days = [d.day for d in df['date']]
    
    # 最高気温と最低気温の推移をプロット
    ax.plot(days, df['max_temp'], 'o-', linewidth=2, color='#FF4B4B', label='Max Temp')
    ax.plot(days, df['min_temp'], 'o-', linewidth=2, color='#4B6CFF', label='Min Temp')
    
    # 雨や雪の表示（show_precipitationがTrueの場合）
    if show_precipitation and 'precipitation' in df.columns:
        # 雨の日にマーカー表示
        rain_days = df[df['precipitation'] == 'rain']['date'].dt.day
        if not rain_days.empty:
            # 雨の日は最高気温+2度の位置に雨マーカーを表示
            rain_temps = df[df['precipitation'] == 'rain']['max_temp'] + 2.0
            ax.scatter(rain_days, rain_temps, marker='v', color='blue', s=150, alpha=0.7, label='Rain')
            
        # 雪の日にマーカー表示
        snow_days = df[df['precipitation'] == 'snow']['date'].dt.day
        if not snow_days.empty:
            # 雪の日は最高気温+3度の位置に雪マーカーを表示
            snow_temps = df[df['precipitation'] == 'snow']['max_temp'] + 3.5
            ax.scatter(snow_days, snow_temps, marker='*', color='skyblue', s=200, alpha=0.8, label='Snow')
            
        # マーカーを繋ぐ縦線（点線）で表示
        for day in rain_days:
            max_temp = df[df['date'].dt.day == day]['max_temp'].values[0]
            ax.vlines(day, max_temp, max_temp + 2.0, linestyles=':', color='blue', alpha=0.5)
            
        for day in snow_days:
            max_temp = df[df['date'].dt.day == day]['max_temp'].values[0]
            ax.vlines(day, max_temp, max_temp + 3.5, linestyles=':', color='skyblue', alpha=0.5)
    
    # y軸の範囲を-10度〜40度に設定
    ax.set_ylim(bottom=-10, top=40)
    
    # y軸の目盛りを5度ごとに設定
    ax.set_yticks(range(-10, 41, 5))
    
    # x軸の設定 - 1日ごとに目盛りを入れる
    ax.set_xticks(days)
    
    # グリッドを追加 (5度ごとに補助線)
    ax.grid(True, axis='y', linestyle='-', alpha=0.7)  # y軸グリッド
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)  # x軸グリッド（薄く）
    
    # 0度の線を強調表示
    ax.axhline(y=0, color='k', linestyle='-', linewidth=1.5, alpha=0.8)
    
    # プロットの詳細設定
    ax.set_title(f'{location_info["name"]} Temperature: {month_names[month]} {year}', fontsize=16)
    ax.set_xlabel('Day', fontsize=12)
    ax.set_ylabel('Temperature (℃)', fontsize=12)
    ax.legend(loc='best')
    fig.tight_layout()
    
    return fig

# 地域選択用の辞書を追加
locations = {
    "東京": {"prec_no": 44, "block_no": 47662, "name": "Tokyo"},
    "大阪": {"prec_no": 62, "block_no": 47772, "name": "Osaka"},
    "北海道(札幌)": {"prec_no": 14, "block_no": 47412, "name": "Sapporo"},
    "福岡": {"prec_no": 82, "block_no": 47807, "name": "Fukuoka"}
}

st.title('気温データビジュアライザー🌡️')
st.write('気象庁のデータから各地の気温グラフを生成します✨')

# サイドバーで地域と年月を選択
location_key = st.sidebar.selectbox(
    "地域を選択",
    list(locations.keys()),
    index=0
)

# 選択した地域の情報を取得
location_info = locations[location_key]

# 年の選択
years = list(range(datetime.now().year, 1949, -1))
year = st.sidebar.selectbox(
    "年を選択", 
    years,
    index=0
)
# ----- 月の選択肢 -----
month_names_ja = {1: "1月", 2: "2月", 3: "3月", 4: "4月", 5: "5月", 6: "6月", 
                7: "7月", 8: "8月", 9: "9月", 10: "10月", 11: "11月", 12: "12月"}
month = st.sidebar.selectbox("月を選択", list(month_names_ja.keys()), 
                                  format_func=lambda x: month_names_ja[x],
                                  index=datetime.now().month - 1)
show_precipitation = st.sidebar.checkbox("雨・雪の日を表示", value=True)

# アクションボタンをサイドバーに移動
if st.sidebar.button("データ取得＆グラフ表示"):
    # プログレスバーを表示するプレースホルダー
    progress_placeholder = st.sidebar.empty()
    
    with st.spinner('気象データをダウンロード中...'):
        df = get_historical_temperature(year, month, location_info, precipitation=show_precipitation)
    
    # データ表示
    if df is not None and not df.empty:
        # グラフを先に表示（順序入れ替え）
        st.subheader("🌡️ 気温グラフ")
        fig = plot_temperature(df, year, month, show_precipitation)
        st.pyplot(fig)
        
        # データフレーム表示
        st.subheader("📊 取得データ")
        st.dataframe(df)
        
        # データのCSVダウンロード機能
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f'{location_key}_temp_{year}_{month}.csv',
            mime='text/csv',
        )
    else:
        st.error("データを取得できませんでした。別の年月を試してください。")

# フッター
st.markdown("---")
st.markdown("### 💡 使い方")
st.markdown("""
1. サイドバーで年と月を選択
2. 「雨・雪の日を表示」にチェックを入れると天気情報も表示
3. 「データ取得＆グラフ表示」ボタンをクリック
4. グラフと詳細データを確認
""")

st.sidebar.markdown("---")
