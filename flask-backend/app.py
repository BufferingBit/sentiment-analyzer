from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from keybert import KeyBERT
import nltk
import torch

nltk.download('vader_lexicon')

app = Flask(__name__)
CORS(app)

vader = SentimentIntensityAnalyzer()
kw_model = KeyBERT()

@app.route('/analyze', methods=['POST'])
def analyze():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    data = request.json
    review = data.get('review', '')

    # Sentiment
    scores = vader.polarity_scores(review)
    compound = scores['compound']
    sentiment = (
        "positive" if compound >= 0.05 else
        "negative" if compound <= -0.05 else
        "neutral"
    )

    # Keywords
    keywords = kw_model.extract_keywords(review, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
    keywords_list = [kw for kw, _ in keywords]

    return jsonify({
        'sentiment': sentiment,
        'score': compound,
        'keywords': keywords_list
    })

if __name__ == '__main__':
    app.run(port=5000)
