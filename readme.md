# README

本リポジトリは、Streamlitフレームワークを活用して作成した各種デモアプリケーションを保存・共有するための場所です。実験的な機能や便利なツールを随時追加していきます。

## 目的

本リポジトリは、Streamlitを使用した様々なデモアプリケーションを気軽に保存・管理することを目的としています。データ可視化、アルゴリズム表現、ツール開発など、多様なアイデアを実装する実験場として活用します。

## 環境セットアップ

```bash
pip install streamlit pandas matplotlib numpy beautifulsoup4 requests folium geopandas streamlit-folium
```

## 使い方
1. リポジトリをクローンまたはダウンロードします。
2. 必要なライブラリをインストールします。
3. 各アプリケーションのPythonファイルを実行します。
4. ブラウザで表示されたURLにアクセスします。

## 作成したデモアプリ

### 気温データビジュアライザー (weather_streamlit.py)

気象庁のオープンデータを活用した気温データ可視化アプリケーションです。

**特徴:**
- 複数地域（東京、大阪、札幌、福岡）の気温データ表示
- 最高気温・最低気温の時系列グラフ表示
- 雨・雪のマーカー表示機能
- 柔軟な年月選択
- データのCSVエクスポート

```bash
streamlit run weather_streamlit.py
```

### フラクタルアニメーション (animation_demo.py)

複素数平面上のジュリア集合を動的に表示するビジュアルデモです。

**特徴:**
- 詳細度（イテレーション数）の調整機能
- 分離パラメータによるフラクタル形状の調整
- 100フレームのスムーズなアニメーション
- リアルタイム進捗表示

```bash
streamlit run animation_demo.py
```

### 人口統計地図ビジュアライザー (population_map_dashboard.py)

日本の都道府県別人口統計データを地図上にインタラクティブに可視化するアプリケーションです。GitHub Copilotのサポートを受けながら約1時間で開発しました。

**特徴:**
- 都道府県別の人口密度をヒートマップ表示
- 年齢層別（0-14歳、15-64歳、65歳以上）の人口分布視覚化
- 地域ごとの人口比較グラフ
- 年別の人口変動表示（2015年～2021年）
- トップ5都道府県のデータテーブル表示

```bash
streamlit run population_map_dashboard.py
```
