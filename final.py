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
from selenium.common.exceptions import SessionNotCreatedException

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
    
    if '/dp/' not in link:
        new_link = re.sub(r'.com/(.p)?/', '.com/product-reviews/', link)
    else:
        new_link = link.replace('dp', 'product-reviews')    
        re_link = re.findall(r'(.*)ref', new_link[0])
        try:
            final_link = re_link[0]+'ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews'
        except IndexError:
            final_link = re.sub(r'(\?.*)', '/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews', new_link)

    driver.get(final_link)
    
    page_source = []
    
    source_1 = driver.page_source 
    
    world_selection = BeautifulSoup(source_1, 'lxml')
    total_selection = world_selection.find('div', class_='a-row a-spacing-base a-size-base')
    total_reviews = re.findall(r'(?:\|) (.*)', str(total_selection))
    reviews_numbers = re.sub(r'[^\d\.]', '', total_reviews[0])
    total = reviews_numbers 
    
    while len(page_source) < (math.floor(int(total)/10)+.1):   
        
        try:
            time.sleep(.2)
            page_source.append(driver.page_source)
            driver.find_element_by_class_name('a-last').click()
            
        except WebDriverException:
            driver.quit()
            break
            
        except SessionNotCreatedException:
            driver.quit()
            break
        
        if len(page_source) >= (math.floor(int(total)/10)+.1):
            driver.quit()
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
    
    if len(bodies) == len(titles):
        
        reviewdict = {'Title' : titles, 'Body' : bodies}
        
    elif len(bodies) < len(titles):
        
        null_n = len(titles) - len(bodies)
        nulls = ['null' for i in range(null_n)]
        bodies.extend(nulls)
        reviewdict = {'Title' : titles, 'Body' : bodies}
        
    elif len(bodies) > len(titles):
        
        null_n = len(bodies) - len(titles)
        nulls = ['null' for i in range(null_n)]
        titles.extend(nulls)
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
    
    title = re.findall(r'.com/(.*)/', link)
    
    stopwords = title[0].split('-')
    
    return stopwords

def word_cloud(dftext, stopwords_add):
    
    text = " ".join(review for review in dftext)
    stopwords = set(STOPWORDS)
    stopwords_add.append('br')
    stopwords_add.append('Amazon')
    stopwords_add.append('Basics')
    stopwords.update(stopwords_add)
    
    wordcloud = WordCloud(stopwords=stopwords, background_color='white').generate(text)


    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot()

title_placeholder = st.empty()
st.set_option('deprecation.showPyplotGlobalUse', False)
st.image('titleamazon.png')
show_side_lan = st.sidebar.selectbox('Language/Lenguaje', ('English','Español'))


if show_side_lan == 'English':
    
    st.write('Made by Agustín Sánchez')
    st.write("This is a Python app that extracts text reviews from Amazon.com to analyze and create a meter that shows the overall sentiment (positive or negative) of the product's reviews.")
    st.write('To use it simply insert an Amazon.com (ONLY WORKS WITH LINKS FROM AMAZON US) product link in the bar below.')
    st.caption('Disclaimer: Due to Streamlit & Heroku limitations you might encounter that the app only extracted a fraction of the reviews.')

    user_input = st.text_input("Insert product link:")

    if len(user_input) != 0:
        
        show_side = st.sidebar.selectbox('Show',('Review Analysis', 'Reviews Database'))
        df = get_reviews(user_input)

        if show_side == 'Review Analysis':
        
            stopwords_add = stopwords(user_input)
            result, size, pos, nega = sentiment_scores(df['Body'])
            st.write('We found', pos, 'positive reviews and', nega, 'negative reviews.')
            score = (int(pos)/int(size))*100
            img = math.floor(score/20)
            st.image('tacometro_'+str(img)+'.png')
            st.subheader('These are the most common words found within the reviews.')
            word_cloud(df.Body, stopwords_add)
    
        if show_side == 'Reviews Database':
        
            st.write('This is a dataframe of all the reviews extracted from your link.')
            st.write(df)
        
        caching.clear_cache()
    
if show_side_lan == 'Español':
    
    st.write('Hecho por Agustín Sánchez')
    st.write("Esta es una aplicacion de Python que extrae reseñas de texto desde Amazon.com para analizarlas y crear un medidor que muestra el sentimiento general (positivo o negativo) de las reseñas del producto.")
    st.write('Para usarlo simplemente inserta un link de un producto de Amazon.com (SOLO FUNCIONA CON LINKS DE AMAZON US) en la barra inferior.')
    st.caption('Disclaimer: Debido a las limitaciones de Streamlit y Heroku es posible que la aplicacion extraiga solo una cantidad limitada de las reseñas del producto.')

    user_input = st.text_input("Inserta el link del producto:")

    if len(user_input) != 0:
        show_side = st.sidebar.selectbox('Show',('Review Analysis', 'Reviews Database'))
        df = get_reviews(user_input)

        if show_side == 'Review Analysis':
        
            stopwords_add = stopwords(user_input)
            result, size, pos, nega = sentiment_scores(df['Body'])
            st.write('Encontramos', pos, 'reseñas positivas y', nega, 'reseñas negativas.')
            score = (int(pos)/int(size))*100
            img = math.floor(score/20)
            st.image('tacometro_'+str(img)+'.png')
            st.subheader('Estas fueron las palabras mas comunes encontradas dentro de las reseñas.')
            word_cloud(df.Body, stopwords_add)
    
        if show_side == 'Reviews Database':
        
            st.write('Esta es una tabla de todas las reseñas extraidas.')
            st.write(df)
        
        caching.clear_cache()
