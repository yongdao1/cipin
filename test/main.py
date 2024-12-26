import matplotlib
import streamlit as st
import jieba
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import pandas as pd
import matplotlib.pyplot as plt
from pyecharts import options as opts
from pyecharts.charts import WordCloud as PyeChartsWordCloud
import seaborn as sns
import streamlit.components.v1 as components  # for embedding HTML
from wordcloud import WordCloud
import os

matplotlib.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['MSYH.TTC'] 


# 1. 获取网页内容
def get_text_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 抓取所有标签的文本，包含 <p>, <div>, <span>, <h1>, <h2> 等等
        all_text = ' '.join(
            [element.get_text() for element in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'li', 'a'])])

        return all_text
    except Exception as error:
        print(f"网页获取失败: {error}")
        return ""


# 2. 加载停用词文件
def load_stopwords(file_path):
    """加载停用词文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = {line.strip() for line in file}  # 使用集合去除重复项
    return stopwords


# 3. 清理HTML标签
def clean_html_tags(text):
    return re.sub(r'<.*?>', '', text)


# 4. 清除标点符号和空白字符
def remove_non_chinese(text):
    # 仅保留中文字符、字母和数字
    return re.sub(r'[^\w\u4e00-\u9fa5]+', '', text)


# 5. 进行分词和词频统计，并去除停用词
def calculate_word_frequency(text, stopwords):
    # 使用jieba进行分词，返回生成器
    words = jieba.cut(text)
    words_list = [word for word in words if word not in stopwords]  # 过滤停用词
    word_count = Counter(words_list)  # 进行词频统计
    return word_count


# 6. 生成 PyeCharts 词云
def generate_pyecharts_wordcloud(word_counts):
    filtered_words = [(word, count) for word, count in word_counts.items() if len(word) > 1]  # 去掉单字
    word_data = pd.DataFrame(filtered_words, columns=["word", "count"])

    wordcloud = PyeChartsWordCloud()
    wordcloud.add("", [list(pair) for pair in zip(word_data["word"].tolist(), word_data["count"].tolist())], word_size_range=[20, 100])

    # 设置标题样式
    wordcloud.set_global_opts(
        title_opts=opts.TitleOpts(
            title="词云",
            title_textstyle_opts=opts.TextStyleOpts(
                font_family="Microsoft YaHei",  # 设置中文字体
                font_size=24,  # 字体大小
                font_weight="bold"  # 加粗
            )
        )
    )

    return wordcloud.render_embed()






# 8. 创建词频柱状图
def plot_bar_chart(word_freq_df):
    word_freq_df.plot(kind='bar', x='词语', y='词频', legend=False, figsize=(10, 5))
    plt.xlabel("词语")
    plt.ylabel("词频")
    plt.xticks(rotation=45)
    st.pyplot(plt)


# 9. 绘制词频折线图
def plot_line_chart(word_freq_df):
    word_freq_df.plot(kind='line', x='词语', y='词频', legend=False, figsize=(10, 5))
    plt.xlabel("词语")
    plt.ylabel("词频")
    plt.xticks(rotation=45)
    st.pyplot(plt)


# 10. 绘制词频饼图
def plot_pie_chart(word_freq_df):
    word_freq_df.set_index('词语').plot(kind='pie', y='词频', legend=False, figsize=(8, 8))
    st.pyplot(plt)


# 11. 创建词频散点图
def plot_scatter_chart(word_freq_df):
    word_freq_df.plot(kind='scatter', x='词语', y='词频', figsize=(10, 5))
    plt.xlabel("词语")
    plt.ylabel("词频")
    st.pyplot(plt)


# 12. 生成词频面积图（替代热力图）
def plot_area_chart(word_freq_df):
    try:
        # 按词频排序
        word_freq_df = word_freq_df.sort_values(by="词频", ascending=False)
        plt.figure(figsize=(12, 6))

        # 词语作为 X 轴，词频作为 Y 轴，绘制面积图
        plt.fill_between(word_freq_df['词语'], word_freq_df['词频'], color='skyblue', alpha=0.4)

        # 添加标签和标题
        plt.xlabel('词语')
        plt.ylabel('词频')
        plt.title('词频面积图')
        plt.xticks(rotation=90)
        st.pyplot(plt)
    except Exception as error:
        st.error(f"生成面积图失败: {error}")


# 13. 生成词频热力图
def plot_heatmap(word_freq_df):
    try:
        # 将词频数据转为适合绘制热力图的格式
        heatmap_data = word_freq_df.set_index('词语')['词频'].to_frame().T  # 转换为一行的矩阵

        # 转置矩阵，进行90度翻转
        heatmap_data = heatmap_data.transpose()  # 或者使用 heatmap_data = heatmap_data.T

        # 绘制热力图
        plt.figure(figsize=(10, 8))
        sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", cbar=True, fmt="d")
        st.pyplot(plt)
    except Exception as error:
        st.error(f"生成热力图失败: {error}")


# 主函数
def app():
    st.sidebar.title("图表选择与参数设置")
    url_input = st.text_input("请输入一个网址获取文本内容：")

    chart_option = st.sidebar.selectbox("选择可视化图表", [
        "PyeCharts 词云",
        "词频柱状图",
        "词频折线图",
        "词频饼图",
        "词频散点图",
        "词频面积图",  
        "词频热力图" 
    ])

    min_freq = st.sidebar.slider("设置最小词频", 1, 200, 100)  # 最小词频筛选

    stopwords_file = r"/mount/src/cipin/test/stopwords.txt"  # 停用词文件路径
    stopwords = load_stopwords(stopwords_file)

    if url_input:
        text = get_text_from_url(url_input)
        if text:
            # 清理文本内容
            clean_text = clean_html_tags(text)
            clean_text = remove_non_chinese(clean_text)

            # 分词并统计词频
            word_counts = calculate_word_frequency(clean_text, stopwords)

            # 过滤低频词
            filtered_word_counts = {word: count for word, count in word_counts.items() if count >= min_freq}
            word_freq_df = pd.DataFrame(filtered_word_counts.items(), columns=["词语", "词频"]).sort_values(by="词频", ascending=False)

            # 显示词频前20
            top_20_text = "词频排名前20的词汇：\n"
            for index, row in word_freq_df.head(20).iterrows():
                top_20_text += f"{row['词语']} : {row['词频']}\n"
            st.text(top_20_text)

            # 根据选择的图表类型绘制相应的图表
            if chart_option == "PyeCharts 词云":
                wordcloud_html = generate_pyecharts_wordcloud(filtered_word_counts)
                components.html(wordcloud_html, height=600)
            elif chart_option == "词频柱状图":
                plot_bar_chart(word_freq_df)
            elif chart_option == "词频折线图":
                plot_line_chart(word_freq_df)
            elif chart_option == "词频饼图":
                plot_pie_chart(word_freq_df)
            elif chart_option == "词频散点图":
                plot_scatter_chart(word_freq_df)
            elif chart_option == "词频面积图":
                plot_area_chart(word_freq_df)
            elif chart_option == "词频热力图":
                plot_heatmap(word_freq_df)
        else:
            st.error("获取网页内容失败，无法提取有效文本！")

        # 运行应用
if __name__ == "__main__":
    app()
