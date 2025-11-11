from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# --- Load CSV data ---
df = pd.read_csv('indeed-job-listings-information.csv')

# --- Drop unnecessary columns ---
columns_to_exclude = ['date_posted_parsed', 'domain', 'is_expired', 'timestamp']
response_columns = [col for col in df.columns if col not in columns_to_exclude]

@app.route('/', methods=['GET'])
def show_dataset():
    data = df[response_columns].to_dict(orient='records')
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
