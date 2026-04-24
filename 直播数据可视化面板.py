import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
from typing import Optional

# ===================== 页面基础配置 =====================
st.set_page_config(
    page_title="直播数据可视化面板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== 全局行业指标标准 =====================
METRIC_STANDARD = {
    "video": {
        "5秒完播率": {"合格": 0.30, "优秀": 0.50, "单位": "%"},
        "全程完播率": {"合格": 0.20, "优秀": 0.35, "单位": "%"},
        "点赞率": {"合格": 0.03, "优秀": 0.05, "单位": "%"},
        "评论率": {"合格": 0.005, "优秀": 0.01, "单位": "%"},
        "转发率": {"合格": 0.003, "优秀": 0.008, "单位": "%"},
        "收藏率": {"合格": 0.005, "优秀": 0.02, "单位": "%"},
        "转粉率": {"合格": 0.002, "优秀": 0.01, "单位": "%"},
    },
    "live_entertainment": {
        "平均停留时长(秒)": {"合格": 120, "优秀": 300, "单位": "s"},
        "弹幕互动率": {"合格": 0.02, "优秀": 0.05, "单位": "%"},
        "付费率": {"合格": 0.01, "优秀": 0.03, "单位": "%"},
        "人均打赏金额": {"合格": 5, "优秀": 20, "单位": "元"},
        "粉丝贡献占比": {"合格": 0.60, "优秀": 0.80, "单位": "%"},
    },
    "live_ecommerce": {
        "商品点击率": {"合格": 0.05, "优秀": 0.10, "单位": "%"},
        "下单转化率": {"合格": 0.03, "优秀": 0.08, "单位": "%"},
        "支付转化率": {"合格": 0.60, "优秀": 0.80, "单位": "%"},
        "客单价": {"合格": 50, "优秀": 150, "单位": "元"},
        "ROI": {"合格": 1.5, "优秀": 3.0, "单位": "倍"},
        "退款率": {"合格": 0.20, "优秀": 0.10, "单位": "%"},
    },
}

# 通用字段映射（抖音/快手字段相同，合并为一份）
FIELD_MAPPING = {
    "video": {
        "video_id": ["视频ID", "item_id", "视频id", "作品ID", "作品id"],
        "title": ["视频标题", "标题", "作品标题"],
        "publish_time": ["发布时间", "发布日期"],
        "total_views": ["播放次数", "总播放量", "播放量"],
        "valid_views": ["有效播放", "有效播放次数", "有效播放量"],
        "play_5s": ["5秒完播人数", "5秒播放人数", "前5秒完播人数", "5秒播放人数"],
        "play_complete": ["完播人数", "完整播放人数", "全程完播人数"],
        "likes": ["点赞数", "点赞次数", "点赞"],
        "comments": ["评论数", "评论次数", "评论"],
        "shares": ["转发数", "分享数", "转发次数", "分享次数"],
        "favorites": ["收藏数", "收藏次数", "收藏"],
        "new_fans": ["新增粉丝", "新增关注", "新增粉丝数", "关注新增"],
    },
    "live_entertainment": {
        "live_id": ["直播ID", "场次ID"],
        "start_time": ["开播时间", "直播时间"],
        "total_viewers": ["观看人数", "累计观看人数"],
        "avg_stay_seconds": ["平均停留时长", "人均停留时长(秒)"],
        "danmu_count": ["弹幕数", "评论数"],
        "pay_users": ["付费人数", "打赏用户数"],
        "total_gift_amount": ["打赏金额", "礼物收入"],
        "fans_contribution": ["粉丝打赏金额", "粉丝贡献"],
        "new_fans": ["新增粉丝", "新增关注"],
    },
    "live_ecommerce": {
        "live_id": ["直播ID", "场次ID"],
        "start_time": ["开播时间", "直播时间"],
        "total_viewers": ["观看人数", "累计观看人数"],
        "product_click": ["商品点击数", "商品点击人数"],
        "order_count": ["下单人数", "下单量"],
        "pay_count": ["支付人数", "支付订单数"],
        "gmv": ["GMV", "销售额", "成交金额"],
        "refund_amount": ["退款金额", "退款GMV"],
        "cost_total": ["投放成本", "推广花费", "总成本"],
        "fans_pay_count": ["粉丝支付人数", "粉丝订单数"],
        "new_fans": ["新增粉丝", "新增关注"],
    },
}

MODE_NAME = {
    "video": "📹 短视频作品数据",
    "live_entertainment": "🎤 娱播打赏数据",
    "live_ecommerce": "🛒 带货电商数据",
}

PLATFORM_NAME = {
    "douyin": "抖音",
    "kuaishou": "快手",
}

FILTER_COLUMNS = {
    "video": ["全程完播率_评级", "转粉率_评级"],
    "live_entertainment": ["付费率_评级", "粉丝贡献占比_评级"],
    "live_ecommerce": ["ROI_评级", "支付转化率_评级"],
}

# ===================== 核心函数 =====================
@st.cache_data(ttl=3600)
def load_and_clean_data(uploaded_file, platform: str, mode: str) -> tuple:
    """加载并清洗数据，自动匹配字段名"""
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            for enc in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                try:
                    df = pd.read_csv(uploaded_file, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return None, "CSV 文件编码不支持，请保存为 UTF-8 或 GBK 格式"

        mapping = FIELD_MAPPING[mode]
        rename_dict, missing_fields = {}, []

        for standard_field, possible_names in mapping.items():
            for col in df.columns:
                if col.strip() in possible_names:
                    rename_dict[col] = standard_field
                    break
            else:
                missing_fields.append(standard_field)

        if missing_fields:
            return None, f"缺少必填字段：{missing_fields}"

        df = df.rename(columns=rename_dict)

        time_col = 'publish_time' if mode == "video" else 'start_time'
        drop_col = 'valid_views' if mode == "video" else 'total_viewers'
        
        df = df.dropna(subset=[drop_col])
        df = df[df[drop_col] > 0]

        if time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df = df.sort_values(time_col).reset_index(drop=True)

        return df, "数据加载成功"

    except Exception as e:
        return None, f"读取失败：{str(e)}"

def _is_higher_better(metric: str) -> bool:
    """判断指标是否越高越好（退款率越低越好）"""
    return metric != "退款率"

def calculate_metrics(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """计算所有派生指标及评级"""
    df = df.copy()
    cfg = METRIC_STANDARD[mode]

    if mode == "video":
        v = df['valid_views']
        df['5秒完播率'] = df['play_5s'] / v
        df['全程完播率'] = df['play_complete'] / v
        df['播放完成度'] = df['play_complete'] / df['total_views']
        df['点赞率'] = df['likes'] / v
        df['评论率'] = df['comments'] / v
        df['转发率'] = df['shares'] / v
        df['收藏率'] = df['favorites'] / v
        df['综合互动率'] = (df['likes'] + df['comments'] + df['shares']) / v
        df['转粉率'] = df['new_fans'] / v

    elif mode == "live_entertainment":
        v = df['total_viewers']
        df['弹幕互动率'] = df['danmu_count'] / v
        df['付费率'] = df['pay_users'] / v
        df['人均打赏金额'] = df['total_gift_amount'] / v
        df['粉丝贡献占比'] = df['fans_contribution'] / df['total_gift_amount']
        df['客单付费金额'] = df['total_gift_amount'] / df['pay_users']

    elif mode == "live_ecommerce":
        df['商品点击率'] = df['product_click'] / df['total_viewers']
        df['下单转化率'] = df['order_count'] / df['product_click']
        df['支付转化率'] = df['pay_count'] / df['order_count']
        df['客单价'] = df['gmv'] / df['pay_count']
        df['退款率'] = df['refund_amount'] / df['gmv']
        df['ROI'] = df['gmv'] / df['cost_total']
        df['粉丝支付占比'] = df['fans_pay_count'] / df['pay_count']

    # 批量计算评级
    for metric, standard in cfg.items():
        if metric not in df.columns:
            continue
        col = df[metric]
        if _is_higher_better(metric):
            df[f'{metric}_评级'] = col.map(
                lambda x: '优秀' if x >= standard['优秀'] else '合格' if x >= standard['合格'] else '不合格'
            )
        else:
            df[f'{metric}_评级'] = col.map(
                lambda x: '优秀' if x <= standard['优秀'] else '合格' if x <= standard['合格'] else '不合格'
            )

    return df

def get_summary_data(df: pd.DataFrame, mode: str) -> dict:
    """生成汇总指标"""
    cfg = METRIC_STANDARD[mode]

    if mode == "video":
        total_valid = df['valid_views'].sum()
        return {
            "统计视频总数": len(df),
            "累计总播放量": df['total_views'].sum(),
            "累计有效播放量": total_valid,
            "累计新增粉丝": df['new_fans'].sum(),
            "平均5秒完播率": df['play_5s'].sum() / total_valid,
            "平均全程完播率": df['play_complete'].sum() / total_valid,
            "平均点赞率": df['likes'].sum() / total_valid,
            "平均转粉率": df['new_fans'].sum() / total_valid,
        }

    elif mode == "live_entertainment":
        total = df['total_viewers'].sum()
        total_gift = df['total_gift_amount'].sum()

...(truncated)...