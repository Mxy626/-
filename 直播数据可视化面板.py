import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime

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
        "转粉率": {"合格": 0.002, "优秀": 0.01, "单位": "%"}
    },
    "live_entertainment": {
        "平均停留时长(秒)": {"合格": 120, "优秀": 300, "单位": "s"},
        "弹幕互动率": {"合格": 0.02, "优秀": 0.05, "单位": "%"},
        "付费率": {"合格": 0.01, "优秀": 0.03, "单位": "%"},
        "人均打赏金额": {"合格": 5, "优秀": 20, "单位": "元"},
        "粉丝贡献占比": {"合格": 0.60, "优秀": 0.80, "单位": "%"}
    },
    "live_ecommerce": {
        "商品点击率": {"合格": 0.05, "优秀": 0.10, "单位": "%"},
        "下单转化率": {"合格": 0.03, "优秀": 0.08, "单位": "%"},
        "支付转化率": {"合格": 0.60, "优秀": 0.80, "单位": "%"},
        "客单价": {"合格": 50, "优秀": 150, "单位": "元"},
        "ROI": {"合格": 1.5, "优秀": 3.0, "单位": "倍"},
        "退款率": {"合格": 0.20, "优秀": 0.10, "单位": "%"}
    }
}

# 字段映射
FIELD_MAPPING = {
    "douyin": {
        "video": {
            "video_id": ["视频ID", "item_id", "视频id"],
            "title": ["视频标题", "标题"],
            "publish_time": ["发布时间", "发布日期"],
            "total_views": ["播放次数", "总播放量", "播放量"],
            "valid_views": ["有效播放", "有效播放次数", "有效播放量"],
            "play_5s": ["5秒完播人数", "5秒播放人数", "前5秒完播人数"],
            "play_complete": ["完播人数", "完整播放人数", "全程完播人数"],
            "likes": ["点赞数", "点赞次数", "点赞"],
            "comments": ["评论数", "评论次数", "评论"],
            "shares": ["转发数", "分享数", "转发次数", "分享次数"],
            "favorites": ["收藏数", "收藏次数", "收藏"],
            "new_fans": ["新增粉丝", "新增关注", "新增粉丝数", "关注新增"]
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
            "new_fans": ["新增粉丝", "新增关注"]
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
            "new_fans": ["新增粉丝", "新增关注"]
        }
    },
    "kuaishou": {
        "video": {
            "video_id": ["作品ID", "视频ID", "作品id"],
            "title": ["作品标题", "视频标题", "标题"],
            "publish_time": ["发布时间", "发布日期"],
            "total_views": ["播放次数", "总播放量", "播放量"],
            "valid_views": ["有效播放", "有效播放次数", "有效播放量"],
            "play_5s": ["5秒播放人数", "前5秒完播人数", "5秒完播人数"],
            "play_complete": ["完播人数", "完整播放人数", "全程完播人数"],
            "likes": ["点赞数", "点赞次数", "点赞"],
            "comments": ["评论数", "评论次数", "评论"],
            "shares": ["转发数", "分享数", "转发次数", "分享次数"],
            "favorites": ["收藏数", "收藏次数", "收藏"],
            "new_fans": ["新增粉丝", "新增关注", "新增粉丝数", "关注新增"]
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
            "new_fans": ["新增粉丝", "新增关注"]
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
            "new_fans": ["新增粉丝", "新增关注"]
        }
    }
}

MODE_NAME = {
    "video": "📹 短视频作品数据",
    "live_entertainment": "🎤 娱播打赏数据",
    "live_ecommerce": "🛒 带货电商数据"
}

PLATFORM_NAME = {
    "douyin": "抖音",
    "kuaishou": "快手"
}

# ===================== 核心函数 =====================
@st.cache_data(ttl=3600)
def load_and_clean_data(uploaded_file, platform, mode):
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                df = pd.read_csv(uploaded_file, encoding='gbk')

        mapping = FIELD_MAPPING[platform][mode]
        rename_dict = {}
        missing_fields = []

        for standard_field, possible_names in mapping.items():
            matched = False
            for col in df.columns:
                if col.strip() in possible_names:
                    rename_dict[col] = standard_field
                    matched = True
                    break
            if not matched:
                missing_fields.append(standard_field)

        if missing_fields:
            return None, f"缺少必填字段：{missing_fields}"

        df = df.rename(columns=rename_dict)
        if mode == "video":
            df = df.dropna(subset=['valid_views', 'total_views'])
            df = df[df['valid_views'] > 0]
            time_col = 'publish_time'
        else:
            df = df.dropna(subset=['total_viewers'])
            df = df[df['total_viewers'] > 0]
            time_col = 'start_time'

        if time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df = df.sort_values(time_col).reset_index(drop=True)

        return df, "数据加载成功"
    except Exception as e:
        return None, f"读取失败：{str(e)}"

def calculate_metrics(df, mode):
    df = df.copy()
    if mode == "video":
        df['5秒完播率'] = df['play_5s'] / df['valid_views']
        df['全程完播率'] = df['play_complete'] / df['valid_views']
        df['播放完成度'] = df['play_complete'] / df['total_views']
        df['点赞率'] = df['likes'] / df['valid_views']
        df['评论率'] = df['comments'] / df['valid_views']
        df['转发率'] = df['shares'] / df['valid_views']
        df['收藏率'] = df['favorites'] / df['valid_views']
        df['综合互动率'] = (df['likes'] + df['comments'] + df['shares']) / df['valid_views']
        df['转粉率'] = df['new_fans'] / df['valid_views']

    elif mode == "live_entertainment":
        df['弹幕互动率'] = df['danmu_count'] / df['total_viewers']
        df['付费率'] = df['pay_users'] / df['total_viewers']
        df['人均打赏金额'] = df['total_gift_amount'] / df['total_viewers']
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

    standard = METRIC_STANDARD[mode]
    for metric, config in standard.items():
        if metric in df.columns:
            if metric == "退款率":
                df[f'{metric}_评级'] = df[metric].apply(
                    lambda x: '优秀' if x <= config['优秀'] else '合格' if x <= config['合格'] else '不合格'
                )
            else:
                df[f'{metric}_评级'] = df[metric].apply(
                    lambda x: '优秀' if x >= config['优秀'] else '合格' if x >= config['合格'] else '不合格'
                )
    return df

def get_summary_data(df, mode):
    summary = {}
    if mode == "video":
        total_valid = df['valid_views'].sum()
        summary = {
            "统计视频总数": len(df),
            "累计总播放量": df['total_views'].sum(),
            "累计有效播放量": total_valid,
            "累计新增粉丝": df['new_fans'].sum(),
            "平均5秒完播率": df['play_5s'].sum() / total_valid,
            "平均全程完播率": df['play_complete'].sum() / total_valid,
            "平均点赞率": df['likes'].sum() / total_valid,
            "平均转粉率": df['new_fans'].sum() / total_valid
        }
    elif mode == "live_entertainment":
        total_viewers = df['total_viewers'].sum()
        summary = {
            "统计直播场次": len(df),
            "累计总观看人数": total_viewers,
            "累计打赏总金额": df['total_gift_amount'].sum(),
            "累计新增粉丝": df['new_fans'].sum(),
            "场均平均停留时长": df['avg_stay_seconds'].mean(),
            "场均付费率": df['pay_users'].sum() / total_viewers,
            "场均粉丝贡献占比": df['fans_contribution'].sum() / df['total_gift_amount'].sum()
        }
    elif mode == "live_ecommerce":
        total_viewers = df['total_viewers'].sum()
        summary = {
            "统计直播场次": len(df),
            "累计总观看人数": total_viewers,
            "累计总GMV": df['gmv'].sum(),
            "累计支付订单数": df['pay_count'].sum(),
            "累计新增粉丝": df['new_fans'].sum() if 'new_fans' in df.columns else 0,
            "平均商品点击率": df['product_click'].sum() / total_viewers,
            "平均支付转化率": df['pay_count'].sum() / df['order_count'].sum(),
            "平均客单价": df['gmv'].sum() / df['pay_count'].sum(),
            "平均ROI": df['gmv'].sum() / df['cost_total'].sum(),
            "平均退款率": df['refund_amount'].sum() / df['gmv'].sum()
        }
    return summary

def export_excel(df, summary, mode):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary_df = pd.DataFrame.from_dict(summary, orient='index', columns=['数值'])
        for idx in summary_df.index:
            if '率' in idx and idx != "平均ROI":
                val = summary_df.loc[idx, '数值']
                summary_df.loc[idx, '数值'] = f"{float(val):.2%}"
            elif '时长' in idx:
                val = summary_df.loc[idx, '数值']
                summary_df.loc[idx, '数值'] = f"{float(val):.1f}秒"
            elif '金额' in idx or 'GMV' in idx or '客单价' in idx:
                val = summary_df.loc[idx, '数值']
                summary_df.loc[idx, '数值'] = f"¥{float(val):,.2f}"
        summary_df.to_excel(writer, sheet_name='整体汇总')

        format_df = df.copy()
        percent_cols = [col for col in format_df.columns if '率' in col]
        format_df[percent_cols] = format_df[percent_cols].applymap(lambda x: f"{x:.2%}")
        format_df.to_excel(writer, sheet_name='明细数据', index=False)

        if mode == "video":
            hot_df = format_df[(format_df['全程完播率_评级']!='不合格')&(format_df['转粉率_评级']!='不合格')]
        elif mode == "live_entertainment":
            hot_df = format_df[(format_df['付费率_评级']!='不合格')&(format_df['粉丝贡献占比_评级']!='不合格')]
        else:
            hot_df = format_df[(format_df['ROI_评级']!='不合格')&(format_df['支付转化率_评级']!='不合格')]
        hot_df.to_excel(writer, sheet_name='优质数据明细')
    output.seek(0)
    return output

# ===================== 页面主体 =====================
st.title("📊 直播数据可视化面板")
st.divider()

# 侧边栏
with st.sidebar:
    st.header("⚙️ 面板配置")
    st.divider()
    platform = st.radio("选择平台",options=["douyin","kuaishou"],format_func=lambda x:PLATFORM_NAME[x],index=0)
    mode = st.radio("选择数据模式",options=["video","live_entertainment","live_ecommerce"],format_func=lambda x:MODE_NAME[x],index=0)
    st.divider()
    uploaded_file = st.file_uploader("上传后台Excel/CSV",type=["xlsx","xls","csv"])
    st.divider()
    filter_rating = st.multiselect("按评级筛选",options=["优秀","合格","不合格"],default=["优秀","合格","不合格"])

# 主内容
if uploaded_file is None:
    st.info("👈 左侧上传抖音/快手导出数据，自动生成可视化报表")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.subheader("📹 短视频分析")
        st.write("完播/互动/转粉率自动计算｜爆款识别｜行业对标")
    with c2:
        st.subheader("🎤 娱乐直播分析")
        st.write("停留/付费/打赏/粉丝贡献｜直播质量评估")
    with c3:
        st.subheader("🛒 带货直播分析")
        st.write("点击率/转化率/ROI/GMV/退款率全链路")
else:
    with st.spinner("数据处理中..."):
        df,msg = load_and_clean_data(uploaded_file,platform,mode)
        if df is None:
            st.error(msg)
        else:
            df_calc = calculate_metrics(df,mode)
            summary = get_summary_data(df_calc,mode)
            rating_cols = [c for c in df_calc.columns if "_评级" in c]
            df_filtered = df_calc[df_calc[rating_cols[0]].isin(filter_rating)] if rating_cols else df_calc

            st.success(msg)
            st.divider()
            st.subheader("📈 核心KPI概览")
            standard = METRIC_STANDARD[mode]
            kpi_cols = st.columns(len(summary))
            for i,(kpi_name,kpi_val) in enumerate(summary.items()):
                with kpi_cols[i]:
                    if "率" in kpi_name and kpi_name!="平均ROI":
                        disp = f"{kpi_val:.2%}"
                        key = kpi_name.replace("平均","").replace("场均","")
                        if key in standard:
                            disp2 = "优秀✅" if kpi_val>=standard[key]["优秀"] else "合格⚠️" if kpi_val>=standard[key]["合格"] else "待优化❌"
                        else:
                            disp2 = ""
                    elif "时长" in kpi_name:
                        disp = f"{kpi_val:.1f}s"
                        key = kpi_name.replace("场均","")
                        disp2 = "优秀✅" if kpi_val>=standard[key]["优秀"] else "合格⚠️" if kpi_val>=standard[key]["合格"] else "待优化❌"
                    elif "金额" in kpi_name or "GMV" in kpi_name or "客单价" in kpi_name:
                        disp = f"¥{kpi_val:,.2f}"
                        disp2 = ""
                    else:
                        disp = f"{kpi_val:,}"
                        disp2 = ""
                    st.metric(label=kpi_name,value=disp,delta=disp2)

            st.divider()
            tab1,tab2,tab3,tab4 = st.tabs(["📊趋势分析","📋明细数据","🎯行业对标","📥报表导出"])

            # 趋势
            with tab1:
                time_col = "publish_time" if mode=="video" else "start_time"
                if time_col in df_filtered.columns:
                    opts = [m for m in standard.keys() if m in df_filtered.columns]
                    sel = st.multiselect("选择指标",opts,default=opts[:2])
                    if sel:
                        fig = go.Figure()
                        for m in sel:
                            fig.add_trace(go.Scatter(x=df_filtered[time_col],y=df_filtered[m],mode="lines+markers",name=m))
                            fig.add_hline(y=standard[m]["合格"],line_dash="dash",line_color="gray")
                        fig.update_layout(height=500)
                        st.plotly_chart(fig,use_container_width=True)

            # 明细
            with tab2:
                disp_df = df_filtered.copy()
                for c in disp_df.columns:
                    if "率" in c:
                        disp_df[c] = disp_df[c].apply(lambda x:f"{x:.2%}")
                st.dataframe(disp_df,use_container_width=True,height=600)

            # 对标
            with tab3:
                compare = []
                for m,cfg in standard.items():
                    if f"平均{m}" in summary:
                        val = summary[f"平均{m}"]
                    elif f"场均{m}" in summary:
                        val = summary[f"场均{m}"]
                    else:
                        continue
                    res = "优秀" if val>=cfg["优秀"] else "合格" if val>=cfg["合格"] else "待优化"
                    compare.append({"指标":m,"自身":f"{val:.2%}","合格线":cfg["合格"],"优秀线":cfg["优秀"],"评级":res})
                st.dataframe(pd.DataFrame(compare),use_container_width=True,hide_index=True)

            # 导出
            with tab4:
                st.write("一键导出完整Excel报表")
                excel_file = export_excel(df_calc,summary,mode)
                st.download_button(
                    label="📥 下载Excel报表",
                    data=excel_file,
                    file_name=f"令宇阳_直播数据报表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openpyxl"
                )

# ===================== 底部版权 =====================
st.divider()
st.caption("© 令宇阳 原创 · 直播数据可视化分析系统")