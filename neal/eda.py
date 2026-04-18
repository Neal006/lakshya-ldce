import pandas as pd

def qualitative_eda(file_path):
    df = pd.read_csv(file_path)

    # Unique Categories
    categories = df['category'].unique().tolist()
    
    # Unique Priorities
    priorities = df['priority'].unique().tolist()
    max_sentiment = df['sentiment'].max()
    min_sentiment = df['sentiment'].min()
    print(max_sentiment, min_sentiment)
    # Qualitative Sentiment Mapping
    # def map_sentiment(val):
    #     if val > 0.05:
    #         return 'Positive'
    #     elif val < -0.05:
    #         return 'Negative'
    #     else:
    #         return 'Neutral'

    # df['sentiment_label'] = df['sentiment'].apply(map_sentiment)
    # sentiments = df['sentiment_label'].unique().tolist()

    print("--- Qualitative Analysis ---")
    print(f"Categories: {categories}")
    print(f"Priorities: {priorities}")
    # print(f"Sentiments: {sentiments}")

if __name__ == "__main__":
    qualitative_eda('data/TS-PS14.csv')
