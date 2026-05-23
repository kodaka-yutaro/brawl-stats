import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

st.set_page_config(page_title="シンプルガチバ統計", layout="wide")

MODE_JA = {
    "gemGrab": "エメラルドハント",
    "brawlBall": "ブロストライカー",
    "heist": "強奪",
    "bounty": "賞金稼ぎ",
    "hotZone": "ホットゾーン",
    "knockout": "ノックアウト",
}

MAP_JA = {
    "Hard Rock Mine": "ごつごつ坑道",
    "Double Swoosh": "ダブルレール",
    "Undermine": "アンダーマイン",
    "Gem Fort": "エメラルドの要塞",
    "Center Stage": "中央コート",
    "Pinball Dreams": "ピンボールドリーム",
    "Sneaky Fields": "静かな広場",
    "Triple Dribble": "トリプル・ドリブル",
    "Hot Potato": "ホットポテト",
    "Safe Zone": "安全地帯",
    "Kaboom Canyon": "どんぱち谷",
    "Bridge Too Far": "橋の彼方",
    "Shooting Star": "流れ星",
    "Hideout": "隠れ家",
    "Dry Season": "乾燥地帯",
    "Layer Cake": "ミルフィーユ",
    "Dueling Beetles": "ビートルバトル",
    "Open Business": "オープンビジネス",
    "Ring of Fire": "炎のリング",
    "Parallel Plays": "パラレルワールド",
    "Out in the Open": "オープンフィールド",
    "Belle's Rock": "ベルの岩",
    "Flaring Phoenix": "燃える不死鳥",
    "New Horizons": "新たなる地平",
    "Goldarm Gulch": "ゴールドアームの渓谷",
    "Flowing Springs": "泥みなき泉",
}

RANK_JA = {
    10: "ダイヤ1",
    11: "ダイヤ2",
    12: "ダイヤ3",
    13: "エリート1",
    14: "エリート2",
    15: "エリート3",
    16: "レジェンド1",
    17: "レジェンド2",
    18: "レジェンド3",
    19: "マスター1",
    20: "マスター2",
    21: "マスター3",
}

RANK_NAMES = [RANK_JA[k] for k in sorted(RANK_JA.keys())]
RANK_EN = {v: k for k, v in RANK_JA.items()}
MODE_EN = {v: k for k, v in MODE_JA.items()}
MAP_EN = {v: k for k, v in MAP_JA.items()}

@st.cache_data
def load_data():
    return pd.read_csv("stats.csv")

@st.cache_data
def load_brawler_map():
    with open("brawlers.json") as f:
        return json.load(f)

def get_image_url(name, brawler_map):
    bid = brawler_map.get(name)
    if bid:
        return f"https://cdn.brawlify.com/brawlers/borders/{bid}.png"
    return None

def get_mode_map_dict(df):
    result = {}
    for _, row in df[["mode", "map"]].drop_duplicates().iterrows():
        m = row["mode"]
        p = row["map"]
        if m not in MODE_JA or p not in MAP_JA:
            continue
        m_ja = MODE_JA[m]
        p_ja = MAP_JA[p]
        if m_ja not in result:
            result[m_ja] = []
        if p_ja not in result[m_ja]:
            result[m_ja].append(p_ja)
    return result

def get_last_updated():
    try:
        mtime = os.path.getmtime("stats.csv")
        return datetime.fromtimestamp(mtime).strftime("%Y/%m/%d %H:%M")
    except:
        return "不明"

# --- メイン ---
df = load_data()
brawler_map = load_brawler_map()
mode_map_dict = get_mode_map_dict(df)

# 全データ数・最終更新
total_all = df["total"].sum() // 6
last_updated = get_last_updated()

# タイトル + 全データ情報
col_title, col_info = st.columns([3, 1])
with col_title:
    st.title("🎮 シンプルガチバ統計")
with col_info:
    st.metric("全データ数", f"{total_all:,} 試合")
    st.caption(f"最終更新：{last_updated}")

with st.sidebar:
    st.header("🔧 設定")

    st.markdown("**ランク帯**")
    rank_min_ja = st.selectbox("下限", RANK_NAMES, index=0)
    rank_min_idx = RANK_NAMES.index(rank_min_ja)
    rank_max_ja = st.selectbox("上限", RANK_NAMES[rank_min_idx:], index=len(RANK_NAMES[rank_min_idx:]) - 1)

    rank_min = RANK_EN[rank_min_ja]
    rank_max = RANK_EN[rank_max_ja]

    mode_ja = st.selectbox("ゲームモード", sorted(mode_map_dict.keys()))
    map_ja = st.selectbox("マップ", mode_map_dict[mode_ja])
    min_games = st.number_input("最低試合数", value=10, step=5, min_value=0)
    sort_by = st.radio("ソート順", ["勝率", "使用率"])

if st.button("🔍 ランキングを見る", type="primary"):
    mode_en = MODE_EN[mode_ja]
    map_en = MAP_EN[map_ja]

    filtered = df[
        (df["mode"] == mode_en) &
        (df["map"] == map_en) &
        (df["rank"] >= rank_min) &
        (df["rank"] <= rank_max)
    ]

    aggregated = filtered.groupby("brawler").agg(
        wins=("wins", "sum"),
        total=("total", "sum")
    ).reset_index()

    total_appearances = aggregated["total"].sum()
    match_count = total_appearances // 6

    aggregated["勝率"] = (aggregated["wins"] / aggregated["total"] * 100).round(1)
    aggregated["使用率"] = (aggregated["total"] / total_appearances * 100).round(1)
    aggregated["試合数"] = aggregated["total"]

    aggregated = aggregated[aggregated["試合数"] >= min_games]

    if aggregated.empty:
        st.warning("該当するデータが見つかりませんでした。条件を緩めてみてください。")
    else:
        # モード・マップ・データ数を表示
        col_mode, col_map, col_count = st.columns([1, 1, 1])
        with col_mode:
            st.metric("モード", mode_ja)
        with col_map:
            st.metric("マップ", map_ja)
        with col_count:
            st.metric("データ数", f"{match_count:,} 試合")

        aggregated = aggregated.sort_values(sort_by, ascending=False).reset_index(drop=True)
        st.success(f"{len(aggregated)} 体のキャラがランクインしました")

        cols_per_row = 10
        for i in range(0, len(aggregated), cols_per_row):
            chunk = aggregated.iloc[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, (_, row) in enumerate(chunk.iterrows()):
                with cols[j]:
                    url = get_image_url(row["brawler"], brawler_map)
                    if url:
                        st.image(url, width=60)
                    rank = i + j + 1
                    st.markdown(f"<p style='font-size:11px;text-align:center'><b>#{rank} {row['brawler']}</b></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size:11px;text-align:center'>勝率 {row['勝率']}%</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size:11px;text-align:center'>使用率 {row['使用率']}%</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size:11px;text-align:center'>{row['試合数']}試合</p>", unsafe_allow_html=True)
