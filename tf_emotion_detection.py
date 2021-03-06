# -*- coding: utf-8 -*-
"""TF_emotion_detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jUODxKOpcwrtO4Y4gHvkSlyCwU3mlBq1

# Text Emotion classifier with Tensorflow 2
"""

!nvidia-smi

"""## Download GloVe word embeddings
We will use it to create the embedding layer so we will not have to train it in the model
"""

!wget http://nlp.stanford.edu/data/glove.6B.zip

!unzip glove*.zip

!rm -rf glove.6B.50d.txt
!rm -rf glove.6B.200d.txt
!rm -rf glove.6B.300d.txt

"""## Download the dataset"""

!wget https://www.dropbox.com/s/607ptdakxuh5i4s/merged_training.pkl

import pickle

## helper function
def load_from_pickle(directory):
    return pickle.load(open(directory,"rb"))

data = load_from_pickle(directory="merged_training.pkl")

## using a sample
emotions = [ "sadness", "joy", "love", "anger", "fear", "surprise"]
data= data[data["emotions"].isin(emotions)]

data.info()

data.describe()

# is there any nulls

data.isna().sum()

# count of nulls
data.isnull().sum()

data.head()



data.iloc[0]

data.emotions.value_counts().plot.bar()

MAX_NB_WORDS = 100000    # max no. of words for tokenizer
MAX_SEQUENCE_LENGTH = 170 # max length of each entry (sentence), including padding
VALIDATION_SPLIT = 0.2   # data for validation (not used in training)
EMBEDDING_DIM = 100      # embedding dimensions for word vectors (word2vec/GloVe)

train = data

#labels = emotions
y = train['emotions'].values
comments_train = train['text']
comments_train = list(comments_train)

y

len(comments_train)

max_text = (max(comments_train, key=len))

len(max_text.split())

def num_words(sentence):
  words = sentence.split()
  return len(words)

total_avg_words = sum( map(num_words, comments_train) ) / len(comments_train)
total_avg_words

MAX_SEQUENCE_LENGTH = 50

"""## Text pre-proccessing"""

import re
from tqdm import tqdm_notebook

import nltk
nltk.download('stopwords')

from nltk.corpus import stopwords

def clean_text(text, remove_stopwords = True):
    output = ""
    text = str(text).replace("\n", "")
    text = re.sub(r'[^\w\s]','',text).lower()
    if remove_stopwords:
        text = text.split(" ")
        for word in text:
            if word not in stopwords.words("english"):
                output = output + " " + word
    else:
        output = text
    return str(output.strip())[1:-3].replace("  ", " ")

texts = [] 

for line in tqdm_notebook(comments_train, total=159571): 
    texts.append(clean_text(line))

len(texts)

print('Sample data:', texts[1], y[1])

"""## Tokenize the texts"""

from tensorflow.keras.preprocessing.text import Tokenizer

tokenizer = Tokenizer(num_words=MAX_NB_WORDS)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
word_index = tokenizer.word_index
print('Vocabulary size:', len(word_index))

import json
with open('word_index.json', 'w') as f:
    json.dump(word_index, f)
with open('index_word.json', 'w') as f2:
    json.dump(tokenizer.index_word, f2)

from tensorflow.keras.preprocessing.sequence import pad_sequences
data = pad_sequences(sequences, padding = 'post', maxlen = MAX_SEQUENCE_LENGTH)
print('Shape of data tensor:', data.shape)
print('Shape of label tensor:', y.shape)

import numpy as np

indices = np.arange(data.shape[0])
np.random.shuffle(indices)
data = data[indices]
labels = y[indices]

data[5]

labels[5]

"""## One-hot encoding labels"""

from sklearn import preprocessing
lb = preprocessing.LabelBinarizer()
lb.fit(labels)

lb.classes_

labels = lb.transform(labels)

labels[5]

num_validation_samples = int(VALIDATION_SPLIT*data.shape[0])
x_train = data[: -num_validation_samples]
y_train = labels[: -num_validation_samples]
x_val = data[-num_validation_samples: ]
y_val = labels[-num_validation_samples: ]
print('Number of entries in each category:')
print('training: ', y_train.sum(axis=0))
print('validation: ', y_val.sum(axis=0))

x_train.shape

y_train.shape

x_val.shape

y_val.shape

"""## Create test set"""

x_val = x_val[: -40000]
y_val = y_val[: -40000]
x_test = x_val[-40000: ]
y_test = y_val[-40000: ]

print('Tokenized sentences: \n', data[10])
print('One hot label: \n', labels[10])

"""## Create the embedding matrix for our model"""

embeddings_index = {}
f = open('/content/glove.6B.100d.txt')
print('Loading GloVe from:', '/content/glove.6B.100d.txt','...', end='')
for line in f:
    values = line.split()
    word = values[0]
    embeddings_index[word] = np.asarray(values[1:], dtype='float32')
f.close()
print("Done.\n Proceeding with Embedding Matrix...", end="")

embedding_matrix = np.random.random((len(word_index) + 1, EMBEDDING_DIM))
for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector
print(" Completed!")

embedding_matrix.shape

"""## Create the model (function API)"""

from tensorflow.keras import regularizers, initializers, optimizers, callbacks
from tensorflow.keras.layers import *
from tensorflow.keras.models import Model

MAX_SEQUENCE_LENGTH

sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedding_layer = Embedding(len(word_index) + 1,
                           EMBEDDING_DIM,
                           weights = [embedding_matrix],
                           input_length = MAX_SEQUENCE_LENGTH,
                           trainable=False,
                           name = 'embeddings')
embedded_sequences = embedding_layer(sequence_input)
x = LSTM(60, return_sequences=True,name='lstm_layer')(embedded_sequences)
x = GlobalMaxPool1D()(x)
x = Dropout(0.1)(x)
x = Dense(50, activation="relu")(x)
x = Dropout(0.1)(x)
preds = Dense(6, activation="softmax")(x)

model = Model(sequence_input, preds)
model.compile(loss = 'categorical_crossentropy',
             optimizer='adam',
             metrics = ['accuracy'])

import tensorflow as tf
tf.keras.utils.plot_model(model)

print('Training progress:')
history = model.fit(x_train, y_train, epochs = 10, batch_size=128, validation_data=(x_val, y_val))

import matplotlib.pyplot as plt

loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss)+1)
plt.plot(epochs, loss, label='Training loss')
plt.plot(epochs, val_loss, label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show();

accuracy = history.history['accuracy']
val_accuracy = history.history['val_accuracy']
plt.plot(epochs, accuracy, label='Training accuracy')
plt.plot(epochs, val_accuracy, label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epochs')
plt.legend()
plt.show();

print("Accuracy in the test set:")
model.evaluate(x_test, y_test)[1]

"""## Test the model"""

samples = ['i feel like, i do not know...', 'love you woman', 'that is so funny', 'mamma, i just killed a man', 'i want to ride my bicycle', 'im alone i feel awful', 'i beleive that i am much more sensitive to oth...']

cleaned_samples = []
for sentence in samples:
  print(sentence)
  cleaned = clean_text(sentence)
  print(cleaned)
  cleaned_samples.append(cleaned)

tokenized_seq = tokenizer.texts_to_sequences(cleaned_samples)
padded_seq =  pad_sequences(tokenized_seq, padding = 'post', maxlen = MAX_SEQUENCE_LENGTH)

int2label = {
    0: 'anger',
    1: 'fear',
    2: 'joy',
    3: 'love',
    4: 'sadness',
    5: 'surprise'
}

predictions = model.predict(padded_seq)

for i, prediction in enumerate(predictions):
  print(samples[i] +" => " +int2label[(np.argmax(prediction))])