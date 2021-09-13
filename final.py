# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 13:29:15 2021

@author: agsan
"""

import re
import sys
import time
import requests
from pathlib import Path

from bs4 import BeautifulSoup

import selectorlib

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver import FirefoxOptions
from selenium.common.exceptions import WebDriverException

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

import streamlit as st
from streamlit import caching

import math

def get_reviews(link: str):
    
    opts = FirefoxOptions()
    opts.add_argument("--headless")
    
    binary = FirefoxBinary('/app/vendor/firefox/firefox')
    
    driver = webdriver.Firefox(firefox_binary=binary, executable_path=r'/app/vendor/geckodriver/geckodriver', firefox_options=opts)
    driver.get(link)
    
    time.sleep(1)
    driver.find_element_by_xpath("//a[@data-hook='see-all-reviews-link-foot']").click()
    page_source = []
    
    source_1 = driver.page_source
    
    world_selection = BeautifulSoup(source_1, 'lxml')
    total_selection = world_selection.find('div', class_='a-row a-spacing-base a-size-base')
    total_reviews = re.findall(r'\| ([0-9]*)', str(total_selection))
    total = total_reviews[0]
    
    print(total, 'Reviews found.')
    
    while len(page_source) < (math.floor(int(total)/10)+.1):   
        
        try:
            time.sleep(.25)
            page_source.append(driver.page_source)
            driver.find_element_by_class_name('a-last').click()
            
        except WebDriverException:
            continue
        
        if len(page_source) >= (math.floor(int(total)/10)+.1):
            driver.close()
            break
    
    titles = []
    bodies = []
    
    for i in range(len(page_source)):
        
        world_selection = BeautifulSoup(page_source[i], 'lxml')
    
        review_title = world_selection.findAll('a', class_='a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold')
        title_list = re.findall(r'>(.*?)<', str(review_title))
        reviews_titles = [i for i in title_list if i !=', ']
        titles.extend(reviews_titles)
        
        review_title = world_selection.findAll('span', class_='a-size-base review-title a-color-base review-title-content a-text-bold')
        title_list = re.findall(r'>(.*?)<', str(review_title))
        reviews_titles = [i for i in title_list if i !=', ']
        titles.extend(reviews_titles)
    
        review_body = world_selection.findAll('span', class_='a-size-base review-text review-text-content')
        body_list = re.findall(r'>\n  (.*)\n<', str(review_body))
        body_reviews = [i for i in body_list if i !=', ']
        bodies.extend(body_reviews)
        
    filter_object = filter(lambda x: x != "", titles)
    titles = list(filter_object)
    
    filter_object2 = filter(lambda x: x != "Your browser does not support HTML5 video.", bodies)
    bodies = list(filter_object2)
            
    reviewdict = {'Title' : titles, 'Body' : bodies}
                   
    df = pd.DataFrame(data=reviewdict)
    
    return df
    
def positive(i):
    return i >= 0.05

def negative(i):
    return i <= 0.05

def neutral(i):
    return i == 0
    
def sentiment_scores(df):
    
    score = SentimentIntensityAnalyzer()
    
    overall_neg = []
    overall_neu = []
    overall_pos = []
    scores = []
    size = len(df)
    
    for i in df:
        sentiment_dict = score.polarity_scores(i)
        scores.append(sentiment_dict['compound'])
        overall_neg.append(sentiment_dict['neg'])
        overall_neu.append(sentiment_dict['neu'])
        overall_pos.append(sentiment_dict['pos'])
        
    positive_total = sum(positive(i) for i in scores)
    negative_total = sum(negative(i) for i in scores)
    
    return ('We found', size, 'total reviews.\n', 'This product has', positive_total , 
            'positive reviews and,', negative_total , 'negative reviews.',
            'Overall,', sum(overall_pos)/size*100, '% of the review score was positive. \n',
            'Overall,', sum(overall_pos)/size*100, '% of the review score was positive. \n',
            'Overall,', sum(overall_neg)/size*100, '% of the review score was negative. \n',
            'Overall,', sum(overall_neu)/size*100, '% of the review score was neutral. \n'), size, positive_total, negative_total

def stopwords(link: str):
    
    title = re.findall(r'.com/([aA0-zZ9-]*)/', link)
    
    stopwords = title[0].split('-')
    
    return stopwords

def word_cloud(dftext, stopwords_add):
    
    text = " ".join(review for review in dftext)
    stopwords = set(STOPWORDS)
    stopwords.update(stopwords_add)

    wordcloud = WordCloud(stopwords=stopwords, background_color='white').generate(text)


    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot()

st.title('Amazon Review Meter')

user_input = st.text_input("Insert AMAZON.US product link:")

if len(user_input) != 0:
    show_side = st.sidebar.selectbox('Show',('Review Analysis', 'Reviews'))

    if show_side == 'Review Analysis':
    
        df = get_reviews(user_input)
        stopwords_add = stopwords(user_input)
        result, size, pos, nega = sentiment_scores(df['Body'])
        score = (int(pos)/int(size))*100
        img = math.floor(score/20)
        st.image('tacometro_'+str(img)+'.png')
        word_cloud(df.Body, stopwords_add)
    
    if show_side == 'Reviews':
    
        st.write(df)
        
    caching.clear_cache()

