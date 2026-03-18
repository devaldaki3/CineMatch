import pandas as pd
import numpy as np
import ast

def process_new_dataset(file_path):
    print("Loading dataset...")
    df = pd.read_csv(file_path)
    
    # Remove entries with missing titles to maintain data integrity
    print(f"Removing {df['title'].isnull().sum()} records with missing titles...")
    df = df.dropna(subset=['title'])
    
    # Cap dataset size to optimize matrix operations and prevent memory allocation issues
    # Selecting the top 50,000 most actively rated movies
    if len(df) > 50000:
        print(f"Optimizing dataset size ({len(df)} rows). Selecting top 50,000 entries by vote count...")
        df = df.sort_values(by='vote_count', ascending=False).head(50000)
    
    # Standardize missing values in categorical fields
    features = ['cast', 'director', 'genres']
    for feature in features:
        df[feature] = df[feature].fillna('unknown')
        
    # Utility functions for parsing text attributes
    def get_actor(x, index):
        try:
            # Extract individual actor names based on the expected delimiter
            actors = str(x).split(',')
            if len(actors) > index:
                return actors[index].strip()
            return 'unknown'
        except:
            return 'unknown'

    def get_director(x):
        try:
            return str(x).split(',')[0].strip()
        except:
            return 'unknown'
            
    def clean_genres(x):
        try:
            # Normalize genre formatting to be space-separated
            return str(x).replace(',', ' ').strip()
        except:
            return 'unknown'

    # Construct the finalized dataframe with required features
    print("Extracting key components: Director, Actors, Genres...")
    new_df = pd.DataFrame()
    new_df['director_name'] = df['director'].apply(get_director)
    new_df['actor_1_name'] = df['cast'].apply(lambda x: get_actor(x, 0))
    new_df['actor_2_name'] = df['cast'].apply(lambda x: get_actor(x, 1))
    new_df['actor_3_name'] = df['cast'].apply(lambda x: get_actor(x, 2))
    new_df['genres'] = df['genres'].apply(clean_genres)
    new_df['movie_title'] = df['title'].str.lower()
    
    # Generate a unified feature string for the similarity computation
    print("Preparing combined feature matrix...")
    new_df['comb'] = (new_df['actor_1_name'] + ' ' + 
                      new_df['actor_2_name'] + ' ' + 
                      new_df['actor_3_name'] + ' ' + 
                      new_df['director_name'] + ' ' + 
                      new_df['genres'])
    
    # Export the processed dataset
    # Optional: overwrite the existing main_data.csv
    # new_df.to_csv('Artifacts/main_data.csv', index=False)
    
    new_df.to_csv('Artifacts/new_main_data.csv', index=False)
    
    print("\n✅ Data processing completed successfully. Exported to 'Artifacts/new_main_data.csv'")
    print(f"Final dataset dimensions: {new_df.shape}")
    print("Data preview:\n", new_df.head(2))

if __name__ == "__main__":
    process_new_dataset('Artifacts/Data/TMDB_all_movies.csv')
