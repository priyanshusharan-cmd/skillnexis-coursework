"""Week 1 preprocessing example. Replace SAMPLE_ROWS with the official Titanic CSV."""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
SAMPLE_ROWS=[{'Age':22,'Fare':7.25,'Sex':'male','Embarked':'S','Survived':0},{'Age':38,'Fare':71.28,'Sex':'female','Embarked':'C','Survived':1},{'Age':None,'Fare':8.05,'Sex':'female','Embarked':'S','Survived':1},{'Age':35,'Fare':53.1,'Sex':'male','Embarked':None,'Survived':0}]
df=pd.DataFrame(SAMPLE_ROWS)
df['Age']=df['Age'].fillna(df['Age'].median());df['Embarked']=df['Embarked'].fillna(df['Embarked'].mode()[0])
encoded=pd.get_dummies(df,columns=['Sex','Embarked'],dtype=int)
print('info:');encoded.info();print('\nstats:\n',encoded.describe(include='all'))
train,test=train_test_split(encoded,test_size=.25,random_state=42,stratify=encoded['Survived'])
encoded.to_csv('cleaned_sample.csv',index=False)
print(f'Wrote illustrative sample only ({len(train)} train, {len(test)} test rows). For the actual project use Kaggle Titanic train.csv and update source data.')
