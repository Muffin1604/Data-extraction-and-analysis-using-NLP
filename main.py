#Importing libraries and packages
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from textblob import TextBlob
import nltk
from nltk.corpus import cmudict, stopwords
from nltk.tokenize import word_tokenize
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('cmudict')

#function for the web scraping logic
def scrape_website(url):
    try:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.find('h1', class_='entry-title').text
            article = soup.find('div', class_='td-post-content tagdiv-type').text
            relevant_data= title + article
            return relevant_data
        except:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.find('h1', class_='tdb-title-text').text
            article = soup.find_all('div', class_='tdb-block-inner td-fix-index')
            article_text = article[14].get_text()
            rel = title + article_text
            return rel
    except:
        return''

#function for the data analysis
def analyze_text(article_text):
    stop_words = set(stopwords.words('english'))

    words = word_tokenize(article_text)

    filtered_words = [word for word in words if word.lower() not in stop_words]

    sentences = nltk.sent_tokenize(article_text)

    if sentences:
        avg_sentence_length = sum(len(word_tokenize(sentence)) for sentence in sentences) / len(sentences)
    else:
        avg_sentence_length = 0

    if filtered_words:
        avg_word_length = sum(len(word) for word in filtered_words) / len(filtered_words)
    else:
        avg_word_length = 0

    cmu_dict = cmudict.dict()

    def syllable_count(word):
        return sum([len(list(y for y in x if y[-1].isdigit())) for x in cmu_dict.get(word.lower(), [[]])])

    personal_pronouns = sum(1 for word in filtered_words if word.lower() in ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'])

    complex_word_count = 0

    if filtered_words:
        complex_word_count = sum(1 for word in filtered_words if syllable_count(word) > 2)
        percentage_complex_words = (complex_word_count / len(filtered_words)) * 100
    else:
        percentage_complex_words = 0

    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)

    blob = TextBlob(article_text)
    positive_score = blob.sentiment.polarity
    negative_score = -blob.sentiment.polarity 
    polarity_score = blob.sentiment.polarity
    subjectivity_score = blob.sentiment.subjectivity

    avg_words_per_sentence = len(filtered_words) / len(sentences) if sentences else 0
    word_count = len(filtered_words)
    syllables_per_word = sum(syllable_count(word) for word in filtered_words) / word_count if word_count != 0 else 0

    return [positive_score, negative_score, polarity_score, subjectivity_score,
            avg_sentence_length, percentage_complex_words, fog_index,
            avg_words_per_sentence, complex_word_count, word_count,
            syllables_per_word, personal_pronouns, avg_word_length]

# Data Extraction
input_file = 'Input.xlsx'
df = pd.read_excel(input_file)
for index, row in df.iterrows():
    url_id = row['URL_ID']
    html_content = row['URL']
    article_text = scrape_website(html_content)
    output_file = f'{url_id}.txt'
    with open(output_file, 'w',encoding='utf-8') as file:
        file.write(article_text)

# saving the computed variables in output data structure file 
output_structure_file = 'Output Data Structure.xlsx'
output_df = pd.read_excel(output_structure_file)
computed_variables_list = []
text_files = [file for file in os.listdir() if file.endswith('.txt')]

for text_file in text_files:
    url_id = os.path.splitext(text_file)[0] 

    with open(text_file, 'r', encoding='utf-8') as file:
        article_text = file.read()

    variables = analyze_text(article_text)

    computed_variables_list.append([url_id] + variables)


computed_variables_df = pd.DataFrame(computed_variables_list, columns=['URL_ID', 'POSITIVE SCORE', 'NEGATIVE SCORE', 'POLARITY SCORE',
                                                                       'SUBJECTIVITY SCORE', 'AVG SENTENCE LENGTH',
                                                                       'PERCENTAGE OF COMPLEX WORDS', 'FOG INDEX',
                                                                       'AVG NUMBER OF WORDS PER SENTENCE', 'COMPLEX WORD COUNT',
                                                                       'WORD COUNT', 'SYLLABLE PER WORD', 'PERSONAL PRONOUNS',
                                                                       'AVG WORD LENGTH'])

result_df = pd.merge(output_df, computed_variables_df, on='URL_ID')
result_output_file = 'Output Data Structure.xlsx'
result_df.to_excel(result_output_file, index=False)
print("program completed successfully")