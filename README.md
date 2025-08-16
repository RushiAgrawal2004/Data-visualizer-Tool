# Data Visualizer Tool

A Python-based data visualization tool that allows users to upload datasets (CSV, Excel, JSON, etc.) and generate interactive visualizations quickly and easily.

## Features
- Upload datasets (CSV, Excel, JSON).
- Automatic detection of columns and data types.
- Generate charts and plots with ease.
- Simple and intuitive interface.
- Backend built with **Flask**.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/Data-visualizer-Tool.git
   cd Data-visualizer-Tool
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Mac/Linux
   venv\Scripts\activate    # On Windows
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Flask server with:
```bash
python server.py
```

Then open your browser and go to:
```
http://127.0.0.1:8000/
```

## Project Structure
```
Data-visualizer-Tool/
│── server.py          # Main application file
│── requirements.txt   # List of dependencies
│── static/            # Static assets (CSS, JS)
│── templates/         # HTML templates
│── data/              # Example datasets
│── README.md          # Project documentation
```

## Tech Stack
- Python
- Flask
- Pandas
- Altair / Plotly / Matplotlib (for visualization)

## Contributing
Contributions are welcome! Feel free to fork this repo and submit a pull request.
