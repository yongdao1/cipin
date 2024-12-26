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
from matplotlib import font_manager

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体

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
    wordcloud.set_global_opts(title_opts=opts.TitleOpts(title="词云"))

    # 展示词云
    wordcloud.render_notebook()

# 7. 生成 WordCloud 图像
def generate_wordcloud_image(word_counts):
    filtered_word_counts = {word: count for word, count in word_counts.items() if len(word) > 1}
    
    # 获取系统默认字体路径
    font_path = '/usr/share/fonts/truetype/msttcorefonts/SimHei.ttf'  # Linux 系统常见路径（根据你的环境进行调整）
    # 如果是在 Windows 系统下，尝试使用以下路径
    # font_path = 'C:/Windows/Fonts/msyh.ttc'  # 适用于 Windows 系统
    
    # 如果使用云环境（如 Streamlit），你可以替换为上传到应用中的字体文件路径

    wc = WordCloud(font_path=font_path, width=800, height=400).generate_from_frequencies(filtered_word_counts)
    
    # 显示词云图像
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis('off')
    st.pyplot(plt)

# 主函数（Streamlit）
def app():
    st.title('网页内容分析与词云生成')

    url = st.text_input('请输入URL', 'https://example.com')
    if url:
        # 获取网页内容
        text = get_text_from_url(url)
        
        # 清理文本并去除停用词
        stopwords = load_stopwords('stopwords.txt')
        cleaned_text = clean_html_tags(text)
        cleaned_text = remove_non_chinese(cleaned_text)
        
        # 计算词频
        word_counts = calculate_word_frequency(cleaned_text, stopwords)
        
        # 显示词云图像
        generate_wordcloud_image(word_counts)
        # 生成PyeCharts词云
        generate_pyecharts_wordcloud(word_counts)

if __name__ == "__main__":
    app()
