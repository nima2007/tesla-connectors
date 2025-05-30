# Tesla Connector Search Tool

This project consists of two main Python scripts:

1.  `scrape_tesla_connectors.py`: A web scraper that collects connector data for various Tesla models and Service Originated Programs (SOPs) from the Tesla service website. It saves this data into multiple JSON files, one for each model/program combination (e.g., `connectors_Model3_prog-233.json`).
2.  `app.py`: A Streamlit web application that allows users to select a specific model and SOP, then search and filter through the corresponding connector data.

## Features

### Scraper (`scrape_tesla_connectors.py`)
- Fetches connector details from the Tesla Electrical Reference for specified models and SOPs.
- Parses information such as part numbers, connector type, color, pinouts, and image URLs.
- Saves the scraped data into separate JSON files for each model/SOP combination (e.g., `connectors_Model3_prog-233.json`).

### Search App (`app.py`)
- Provides a user-friendly interface to select a vehicle model and program (SOP).
- Displays build information associated with the selected SOP.
- Allows searching and filtering for connectors within the selected dataset.
- Filtering options include:
    - Total number of cavities.
    - Number of connected cavities.
    - Number of unconnected cavities.
    - Manufacturer / Connector Part Number (combined search, contains match).
    - Tesla Part Number (contains match).
    - Connector body color.
    - Exact count of specific wire colors (up to two different colors) across all cavities.
- Displays results in a paginated, sortable format with connector details and images.

## Setup

### Prerequisites
- Python 3.7+

### Installation

1.  **Clone the repository (or download the files):**
    ```bash
    # If you have git installed
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Scrape Connector Data (Optional if data files like `connectors_Model3_prog-XYZ.json` are already present and up-to-date)

To update or generate the connector data files for all configured models and SOPs, run the scraper:
```bash
python scrape_tesla_connectors.py
```
This script will fetch the latest connector information for each defined model/SOP and save it into individual JSON files (e.g., `connectors_Model3_prog-233.json`). This might take some time depending on your internet connection and the number of connectors across all programs.

**Note:** The `CONNECTOR_LIMIT` variable in `scrape_tesla_connectors.py` can be set to an integer to limit the number of connectors scraped *per program* during testing (e.g., `CONNECTOR_LIMIT = 10`). Set it to `None` to scrape all connectors for all programs.

### 2. Run the Connector Search App

Once you have the connector data files (e.g., `connectors_Model3_prog-13.json`, `connectors_Model3_prog-233.json`, etc.), either by running the scraper or by using those included in the repository, you can start the Streamlit application:
```bash
streamlit run app.py
```
This will open the search tool in your web browser.

## Project Structure
```
.
├── .gitignore          # Specifies intentionally untracked files for Git
├── app.py              # The Streamlit web application
├── connectors_MODEL_PROG-ID.json # Data files (e.g., connectors_Model3_prog-233.json)
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── scrape_tesla_connectors.py # Script to scrape connector data
```

## Contributing
Feel free to fork the project, make improvements, and submit pull requests.
