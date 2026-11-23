
from nltk.sentiment import SentimentIntensityAnalyzer


# Initialize the sentiment analyzer
analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text):

    # Calculate sentiment scores
    scores = analyzer.polarity_scores(text)

    # Extract compound score
    compound_score = scores["compound"]

    # Classify sentiment
    if compound_score >= 0.05:
        sentiment = "Positive"

    elif compound_score <= -0.05:
        sentiment = "Negative"

    else:
        sentiment = "Neutral"

    # Return results
    return {
        "sentiment": sentiment,
        "positive": round(scores["pos"] * 100, 2),
        "negative": round(scores["neg"] * 100, 2),
        "neutral": round(scores["neu"] * 100, 2),
        "compound": round(compound_score, 3)
    }
