# AI Product Scouter

AI-powered product scouter to find underpriced items on marketplaces (e.g., Mercari).

## Setup

1.  **Environment Setup**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

3.  **Configuration**
    Copy `.env.example` to `.env` and fill in your API keys.
    ```bash
    cp .env.example .env
    ```

## Running the Prototype

To test the basic scraping functionality (Mercari):

```bash
python scraper_prototype.py
```

## Project Structure

- `scraper_prototype.py`: Basic script to test Playwright scraping.
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables (API Keys, DB URLs).
# ai-product-scouter
