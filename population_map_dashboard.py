import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import requests
from io import BytesIO
import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
import base64

# 英語表記に切り替えるためのコード追加
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# 地域名を英語に変更するマッピング
region_mapping = {
    '北海道': 'Hokkaido',
    '東北': 'Tohoku',
    '関東': 'Kanto',
    '中部': 'Chubu',
    '近畿': 'Kinki',
    '中国': 'Chugoku',
    '四国': 'Shikoku',
    '九州': 'Kyushu',
    '沖縄': 'Okinawa'
}

# アプリケーションタイトル設定
st.title('日本の都道府県別人口統計マップ')
st.write('人口データを地図上で視覚的に確認できるダッシュボードです')

# サイドバー設定
st.sidebar.header('表示オプション')

# 年代選択（サンプルデータ用、実際のAPIでは年が選択できるようにする）
year = st.sidebar.selectbox('年を選択', [2015, 2016, 2017, 2018, 2019, 2020, 2021])

# 表示モード選択
display_mode = st.sidebar.radio(
    "表示モード",
    ['人口総数', '人口密度', '年齢層別人口']
)

# 年齢層選択（年齢層別モード用）
if display_mode == '年齢層別人口':
    age_group = st.sidebar.selectbox(
        '年齢層を選択',
        ['0-14歳', '15-64歳', '65歳以上']
    )

# データキャッシュ用デコレータ
@st.cache_data(ttl=3600)
def load_japan_map_data():
    """日本の地図データ（GeoJSON）を読み込む関数"""
    try:
        # 国土地理院などが提供する日本の県境GeoJSONデータをダウンロード
        url = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
        response = requests.get(url)
        return json.loads(response.content)
    except Exception as e:
        st.error(f"地図データの読み込みに失敗しました: {e}")
        return None

@st.cache_data(ttl=3600)
def load_prefecture_data():
    """都道府県マスタデータを読み込む関数"""
    # 都道府県コードとその基本情報
    pref_data = {
        '01': {'name': '北海道', 'area': 83424, 'region': '北海道'},
        '02': {'name': '青森県', 'area': 9646, 'region': '東北'},
        '03': {'name': '岩手県', 'area': 15275, 'region': '東北'},
        '04': {'name': '宮城県', 'area': 7282, 'region': '東北'},
        '05': {'name': '秋田県', 'area': 11638, 'region': '東北'},
        '06': {'name': '山形県', 'area': 9323, 'region': '東北'},
        '07': {'name': '福島県', 'area': 13784, 'region': '東北'},
        '08': {'name': '茨城県', 'area': 6097, 'region': '関東'},
        '09': {'name': '栃木県', 'area': 6408, 'region': '関東'},
        '10': {'name': '群馬県', 'area': 6362, 'region': '関東'},
        '11': {'name': '埼玉県', 'area': 3798, 'region': '関東'},
        '12': {'name': '千葉県', 'area': 5157, 'region': '関東'},
        '13': {'name': '東京都', 'area': 2194, 'region': '関東'},
        '14': {'name': '神奈川県', 'area': 2416, 'region': '関東'},
        '15': {'name': '新潟県', 'area': 12584, 'region': '中部'},
        '16': {'name': '富山県', 'area': 4248, 'region': '中部'},
        '17': {'name': '石川県', 'area': 4186, 'region': '中部'},
        '18': {'name': '福井県', 'area': 4190, 'region': '中部'},
        '19': {'name': '山梨県', 'area': 4465, 'region': '中部'},
        '20': {'name': '長野県', 'area': 13562, 'region': '中部'},
        '21': {'name': '岐阜県', 'area': 10621, 'region': '中部'},
        '22': {'name': '静岡県', 'area': 7777, 'region': '中部'},
        '23': {'name': '愛知県', 'area': 5172, 'region': '中部'},
        '24': {'name': '三重県', 'area': 5774, 'region': '近畿'},
        '25': {'name': '滋賀県', 'area': 4017, 'region': '近畿'},
        '26': {'name': '京都府', 'area': 4612, 'region': '近畿'},
        '27': {'name': '大阪府', 'area': 1905, 'region': '近畿'},
        '28': {'name': '兵庫県', 'area': 8401, 'region': '近畿'},
        '29': {'name': '奈良県', 'area': 3691, 'region': '近畿'},
        '30': {'name': '和歌山県', 'area': 4725, 'region': '近畿'},
        '31': {'name': '鳥取県', 'area': 3507, 'region': '中国'},
        '32': {'name': '島根県', 'area': 6708, 'region': '中国'},
        '33': {'name': '岡山県', 'area': 7114, 'region': '中国'},
        '34': {'name': '広島県', 'area': 8479, 'region': '中国'},
        '35': {'name': '山口県', 'area': 6112, 'region': '中国'},
        '36': {'name': '徳島県', 'area': 4147, 'region': '四国'},
        '37': {'name': '香川県', 'area': 1876, 'region': '四国'},
        '38': {'name': '愛媛県', 'area': 5676, 'region': '四国'},
        '39': {'name': '高知県', 'area': 7104, 'region': '四国'},
        '40': {'name': '福岡県', 'area': 4986, 'region': '九州'},
        '41': {'name': '佐賀県', 'area': 2441, 'region': '九州'},
        '42': {'name': '長崎県', 'area': 4130, 'region': '九州'},
        '43': {'name': '熊本県', 'area': 7409, 'region': '九州'},
        '44': {'name': '大分県', 'area': 6341, 'region': '九州'},
        '45': {'name': '宮崎県', 'area': 7735, 'region': '九州'},
        '46': {'name': '鹿児島県', 'area': 9187, 'region': '九州'},
        '47': {'name': '沖縄県', 'area': 2281, 'region': '沖縄'},
    }
    return pref_data

@st.cache_data(ttl=3600)
def fetch_population_data(year):
    """指定した年の人口データを取得する関数"""
    # APIからデータを取得する代わりに、今回はサンプルデータを生成
    pref_data = load_prefecture_data()
    
    # 実際のデータ比率に近い形でサンプル人口を生成
    population_data = {
        '01': {'total': 5250000, '0-14': 550000, '15-64': 3100000, '65+': 1600000},  # 北海道
        '13': {'total': 14000000, '0-14': 1600000, '15-64': 9000000, '65+': 3400000},  # 東京
        '23': {'total': 7550000, '0-14': 1050000, '15-64': 4800000, '65+': 1700000},  # 愛知
        '27': {'total': 8800000, '0-14': 1150000, '15-64': 5500000, '65+': 2150000},  # 大阪
    }
    
    # その他の都道府県にもサンプルデータを割り当て
    import random
    random.seed(year)  # 同じ年なら同じデータを生成
    
    population_df = []
    for pref_code, info in pref_data.items():
        # まだデータがなければサンプルデータを生成
        if pref_code not in population_data:
            area = info['area']
            # 面積と地域特性でおおよその人口を推定
            base = random.uniform(0.8, 1.2)
            if info['region'] in ['関東', '近畿', '中部']:
                base_population = min(3000000 + area * 50 * base, 8000000)
            else:
                base_population = min(800000 + area * 20 * base, 2500000)
                
            total = int(base_population)
            children = int(total * random.uniform(0.1, 0.15))
            elderly = int(total * random.uniform(0.2, 0.35))
            working = total - children - elderly
            
            population_data[pref_code] = {
                'total': total,
                '0-14': children,
                '15-64': working,
                '65+': elderly
            }
            
        # データフレーム用のデータ準備    
        data = {
            'pref_code': pref_code,
            'prefecture': info['name'],
            'region': info['region'],
            'area': info['area'],
            'total_population': population_data[pref_code]['total'],
            'population_0_14': population_data[pref_code]['0-14'],
            'population_15_64': population_data[pref_code]['15-64'],
            'population_65plus': population_data[pref_code]['65+'],
            'density': population_data[pref_code]['total'] / info['area'],
            'year': year
        }
        population_df.append(data)
        
    # 年度ごとに少しずつ変化を加える（2015年基準）
    year_diff = year - 2015
    for data in population_df:
        change_factor = 1.0 + (year_diff * random.uniform(-0.01, 0.02))
        data['total_population'] = int(data['total_population'] * change_factor)
        data['population_0_14'] = int(data['population_0_14'] * max(0.95, change_factor * 0.97))
        data['population_65plus'] = int(data['population_65plus'] * min(1.1, change_factor * 1.03))
        data['population_15_64'] = data['total_population'] - data['population_0_14'] - data['population_65plus']
        data['density'] = data['total_population'] / data['area']
        
    return pd.DataFrame(population_df)

# コロプレス図関数の修正版

def create_choropleth_map(geo_data, data, column, title, colormap='YlOrRd'):
    """コロプレス図（色分け地図）を作成する関数"""
    # 地図の初期設定
    m = folium.Map(
        location=[36.2048, 138.2529],  # 日本の中心あたりに設定
        zoom_start=5,
        tiles='cartodbpositron'
    )
    
    # コロプレス図作成
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        name='choropleth',
        data=data,
        columns=['pref_code', column],
        key_on='feature.properties.id',
        fill_color=colormap,
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name=title,
        highlight=True,
        bins=8,  # 階級区分の数
    ).add_to(m)
    
    # ここ重要！！！なんか複雑な処理するより、シンプルにツールチップ一つだけでいいわ！
    # データをさらに紐付けとかせずに、基本的なホバー情報だけ表示する
    folium.features.GeoJsonTooltip(
        fields=['nam_ja'],
        aliases=['都道府県:'],
        localize=True,
        sticky=True
    ).add_to(choropleth.geojson)
    
    return m

# 地図データとサンプルデータを読み込み
with st.spinner('データ読み込み中...'):
    geo_data = load_japan_map_data()
    prefecture_data = load_prefecture_data()
    population_df = fetch_population_data(year)

    if geo_data is None:
        st.error("地図データの読み込みに失敗しました。")
        st.stop()

# 表示するデータ列とタイトルを決定
if display_mode == '人口総数':
    column = 'total_population'
    title = f'{year}年 都道府県別人口総数'
    map_title = '総人口（人）'
elif display_mode == '人口密度':
    column = 'density'
    title = f'{year}年 都道府県別人口密度'
    map_title = '人口密度（人/km²）'
else:  # 年齢層別人口
    if age_group == '0-14歳':
        column = 'population_0_14'
        title = f'{year}年 都道府県別年少人口（0-14歳）'
    elif age_group == '15-64歳':
        column = 'population_15_64'
        title = f'{year}年 都道府県別生産年齢人口（15-64歳）'
    else:  # '65歳以上'
        column = 'population_65plus'
        title = f'{year}年 都道府県別高齢者人口（65歳以上）'
    map_title = '人口（人）'

# 地図表示
st.subheader(title)
map_fig = create_choropleth_map(geo_data, population_df, column, map_title)
st_folium(map_fig, width=700, height=500)

# データテーブル表示（トップ5と詳細表示オプション）
st.subheader("データテーブル")

if display_mode == '人口密度':
    sorted_df = population_df.sort_values(by=column, ascending=False)
    with st.expander("人口密度上位5都道府県"):
        top5 = sorted_df.head(5)
        formatted_top5 = top5.copy()
        formatted_top5['density'] = formatted_top5['density'].apply(lambda x: f"{x:.1f}")
        formatted_top5['total_population'] = formatted_top5['total_population'].apply(lambda x: f"{int(x):,}")
        st.table(formatted_top5[['prefecture', 'density', 'total_population']])
else:
    sorted_df = population_df.sort_values(by=column, ascending=False)
    with st.expander(f"{map_title}上位5都道府県"):
        top5 = sorted_df.head(5)
        formatted_top5 = top5.copy()
        for col in ['total_population', 'population_0_14', 'population_15_64', 'population_65plus']:
            formatted_top5[col] = formatted_top5[col].apply(lambda x: f"{int(x):,}")
        
        # ここ！カラム名が重複してるから修正！
        if column == 'total_population':
            # 重複を避けるため、一つの列だけ表示
            st.table(formatted_top5[['prefecture', 'total_population']])
        else:
            # 重複しない場合は元のまま
            st.table(formatted_top5[['prefecture', column, 'total_population']])

# 詳細データ表示オプション
with st.expander("全都道府県データ表示"):
    # 表示列を決定
    display_cols = ['prefecture', 'region', 'total_population', 'density']
    if display_mode == '年齢層別人口':
        display_cols.append(column)
    
    # データをテーブル表示
    formatted_df = population_df.copy()
    formatted_df['density'] = formatted_df['density'].apply(lambda x: f"{x:.1f}")
    for col in ['total_population', 'population_0_14', 'population_15_64', 'population_65plus']:
        formatted_df[col] = formatted_df[col].apply(lambda x: f"{int(x):,}")
    
    st.dataframe(
        formatted_df[display_cols].sort_values(by='prefecture'),
        use_container_width=True
    )

# グラフ分析
st.subheader("データ分析")

# 地域別集計
with st.expander("地域別人口分布"):
    region_data = population_df.groupby('region').agg({
        'total_population': 'sum',
        'population_0_14': 'sum',
        'population_15_64': 'sum',
        'population_65plus': 'sum'
    }).reset_index()
    
    # 英語の地域名に変換
    region_data['region_en'] = region_data['region'].map(region_mapping)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(region_data))
    width = 0.25
    
    ax.bar(x - width, region_data['population_0_14'] / 10000, width, label='0-14 y.o.')
    ax.bar(x, region_data['population_15_64'] / 10000, width, label='15-64 y.o.')
    ax.bar(x + width, region_data['population_65plus'] / 10000, width, label='65+ y.o.')
    
    ax.set_ylabel('Population (10,000 people)')
    ax.set_title('Population Distribution by Region')
    ax.set_xticks(x)
    ax.set_xticklabels(region_data['region_en'])  # 英語の地域名を使用
    ax.legend()
    
    st.pyplot(fig)

# ダウンロード機能
st.subheader("データダウンロード")

def create_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="population_data_{year}.csv">人口データCSVをダウンロード</a>'
    return href

st.markdown(create_download_link(population_df), unsafe_allow_html=True)

# フッター
st.markdown("---")
st.markdown("データソース: サンプルデータ（実運用時はe-Stat APIから取得）")
st.markdown("© 2025 Demo Applications")