#!/bin/sh
# AG News (Zhang, Zhao & LeCun 2015), CSV copy hosted on GitHub. ~31 MB.
mkdir -p data
curl -L -o data/train.csv https://raw.githubusercontent.com/mhjabreel/CharCnn_Keras/master/data/ag_news_csv/train.csv
curl -L -o data/test.csv  https://raw.githubusercontent.com/mhjabreel/CharCnn_Keras/master/data/ag_news_csv/test.csv
