import streamlit as st
import streamlit.components.v1 as components
import requests
import jieba
from collections import Counter
from pyecharts.charts import WordCloud, Bar, Line, Pie, Scatter, Radar, Funnel
from pyecharts import options as opts
import re
from bs4 import BeautifulSoup
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. 获取网页内容
def get_text_from_url(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        all_text = ' '.join([element.get_text() for element in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'li', 'a'])])
        return all_text
    except Exception as error:
        st.error(f"网页获取失败: {error}")
        return ""

# 2. 加载停用词文件
def load_stopwords(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = {line.strip() for line in file}
    return stopwords

# 3. 清理HTML标签
def clean_html_tags(text):
    return re.sub(r'<.*?>', '', text)

# 4. 清除标点符号和空白字符
def remove_non_chinese(text):
    return re.sub(r'[^\w\u4e00-\u9fa5]+', '', text)

# 5. 进行分词和词频统计，并去除停用词
def calculate_word_frequency(text, stopwords):
    words = jieba.cut(text)
    words_list = [word for word in words if word not in stopwords]
    word_count = Counter(words_list)
    return word_count

# 6. 生成 PyeCharts 词云
def generate_pyecharts_wordcloud(word_counts):
    filtered_words = [(word, count) for word, count in word_counts.items() if len(word) > 1]
    wordcloud = WordCloud()
    wordcloud.add("", filtered_words, word_size_range=[20, 100])
    wordcloud.set_global_opts(title_opts=opts.TitleOpts(title="词云"))
    return wordcloud.render_embed()

# 7. 使用 ECharts 绘制柱状图
def plot_bar_chart(word_freq_df):
    bar = Bar()
    bar.add_xaxis(word_freq_df['词语'].tolist())
    bar.add_yaxis("词频", word_freq_df['词频'].tolist())
    bar.set_global_opts(title_opts=opts.TitleOpts(title="词频柱状图"))
    return bar.render_embed()

# 8. 使用 seaborn 绘制面积图（distplot）
def plot_area_chart(word_freq_df):
    plt.figure(figsize=(10, 6))
    sns.distplot(word_freq_df['词频'], hist=True, kde=True, bins=30, color='blue')
    plt.title('词频分布（面积图）')
    plt.xlabel('词频')
    plt.ylabel('频率')
    st.pyplot(plt)

# 9. 绘制直方图
def plot_histogram(word_freq_df):
    plt.figure(figsize=(10, 6))
    plt.hist(word_freq_df['词频'], bins=30, color='green', edgecolor='black')
    plt.title('词频分布（直方图）')
    plt.xlabel('词频')
    plt.ylabel('频率')
    st.pyplot(plt)

# 10. 绘制词频饼图
def plot_pie_chart(word_freq_df):
    pie = Pie()
    pie.add("", [list(z) for z in zip(word_freq_df['词语'].tolist(), word_freq_df['词频'].tolist())])
    pie.set_global_opts(title_opts=opts.TitleOpts(title="词频饼图"))
    return pie.render_embed()

# 11. 创建词频散点图
def plot_scatter_chart(word_freq_df):
    scatter = Scatter()
    scatter.add_xaxis(word_freq_df['词语'].tolist())
    scatter.add_yaxis("词频", word_freq_df['词频'].tolist())
    scatter.set_global_opts(title_opts=opts.TitleOpts(title="词频散点图"))
    return scatter.render_embed()

# 12. 创建词频雷达图
def plot_radar_chart(word_freq_df):
    radar = Radar()
    if len(word_freq_df) >= 3:
        indices = word_freq_df.head(3)['词语'].tolist()
        values = word_freq_df.head(3)['词频'].tolist()
        schema = [
            opts.RadarIndicatorItem(name=i, max_=word_freq_df['词频'].max()) for i in indices
        ]
        radar.add_schema(schema=schema)
        radar.add("", [values])
        radar.set_global_opts(title_opts=opts.TitleOpts(title="词频雷达图"))
        return radar.render_embed()
    else:
        return "数据不足以生成雷达图"

# 13. 创建词频漏斗图
def plot_funnel_chart(word_freq_df):
    funnel = Funnel()
    if len(word_freq_df) >= 5:
        items = [list(z) for z in zip(word_freq_df.head(5)['词语'].tolist(), word_freq_df.head(5)['词频'].tolist())]
        funnel.add("", items)
        funnel.set_global_opts(title_opts=opts.TitleOpts(title="词频漏斗图"))
        return funnel.render_embed()
    else:
        return "数据不足以生成漏斗图"

# 主函数
def app():
    st.sidebar.title("图表选择与参数设置")
    url_input = st.text_input("请输入一个网址获取文本内容：")
    chart_type = st.sidebar.selectbox(
            '选择图表类型',
            ['词云', '柱状图', '面积图', '直方图', '饼图', '散点图', '雷达图', '漏斗图']
        )
    min_freq = st.sidebar.slider("设置最小词频", 1, 200, 100)
    stopwords_file = "/mount/src/cipin/test/stopwords.txt"  # 停用词文件路径
    stopwords = load_stopwords(stopwords_file)

    if url_input:
        text = get_text_from_url(url_input)
        if text:
            clean_text = clean_html_tags(text)
            clean_text = remove_non_chinese(clean_text)
            word_counts = calculate_word_frequency(clean_text, stopwords)
            filtered_word_counts = {word: count for word, count in word_counts.items() if count >= min_freq}
            word_freq_df = pd.DataFrame(filtered_word_counts.items(), columns=["词语", "词频"]).sort_values(by="词频", ascending=False)

            top_20_text = "词频排名前20的词汇：\n"
            for index, row in word_freq_df.head(20).iterrows():
                top_20_text += f"{row['词语']} : {row['词频']}\n"
            st.text(top_20_text)

            # 根据用户选择的图表类型生成图表
            if chart_type == '词云':
                chart = generate_pyecharts_wordcloud(word_counts)
            elif chart_type == '柱状图':
                chart = plot_bar_chart(word_freq_df)
            elif chart_type == '面积图':
                plot_area_chart(word_freq_df)
                return  # 直接返回，避免渲染不必要的 ECharts 图表
            elif chart_type == '直方图':
                plot_histogram(word_freq_df)
                return  # 直接返回，避免渲染不必要的 ECharts 图表
            elif chart_type == '饼图':
                chart = plot_pie_chart(word_freq_df)
            elif chart_type == '散点图':
                chart = plot_scatter_chart(word_freq_df)
            elif chart_type == '雷达图':
                chart = plot_radar_chart(word_freq_df)
            elif chart_type == '漏斗图':
                chart = plot_funnel_chart(word_freq_df)
            
            # 显示选定的图表
            if chart_type not in ['面积图', '直方图']:  # 避免重复渲染
                components.html(chart, height=600)
        else:
            st.error("未能从该网址获取到有效的文本内容，请检查网址是否有效。")

if __name__ == "__main__":
    app()
