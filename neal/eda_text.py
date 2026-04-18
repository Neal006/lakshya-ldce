import pandas as pd

def text_quantitative_eda(file_path):
    df = pd.read_csv(file_path)
    
    # Ensure text column is string
    df['text'] = df['text'].astype(str)
    
    # Calculate lengths
    df['text_len'] = df['text'].apply(len)
    
    max_chars = df['text_len'].max()
    avg_chars = df['text_len'].mean()
    median_chars = df['text_len'].median()
    min_chars = df['text_len'].min()
    total_texts = len(df['text'])

    print("--- Quantitative Analysis: Text Column ---")
    print(f"Total Records: {total_texts}")
    print(f"Maximum Characters: {max_chars}")
    print(f"Average Characters: {avg_chars:.2f}")
    print(f"Median Characters: {median_chars}")
    print(f"Minimum Characters: {min_chars}")

if __name__ == "__main__":
    text_quantitative_eda('data/TS-PS14.csv')
