# SEC_DataAnalysis
Tweets sentiment analysis web application that collects tweets for Saudi Electricity Company, cleans them, applies several analyses including sentiment analysis, and presents them in interactive graphs.

### Requirements
- pandas=1.2.1
- numpy=1.19.2
- nltk=3.5
- joblib=1.0.0
- django==3.2.4
- twint 
- pyarabic==0.6.10
- scikit-learn==0.24.2
- ar-wordcloud==0.0.4

### Installation
1. clone SEC_DataAnalysis repository
```python
git clone https://github.com/ah918/SEC_DataAnalysis.git
```
2. install requirements
```python
cd SEC_DataAnalysis
pip install -r requirements.txt
```
3. setup django project
```python
# create SQLite databse, run migrations
python manage.py migrate

# run Django dev server
python manage.py runserver
```
4. development server starts by default at http://127.0.0.1:8000/
