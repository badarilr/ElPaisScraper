
## Overview
This project is a Python-based automation solution designed for cross-browser testing using Selenium and BrowserStack. It performs the following tasks:

1. **Visit El País Website:** Ensures the website is displayed in Spanish.
2. **Scrape Opinion Section:** Fetches the first five articles, their titles, and content. Downloads cover images if available.
3. **Translate Article Titles:** Uses an API to translate article titles from Spanish to English.
4. **Analyze Translated Titles:** Identifies repeated words across translated titles and provides their count.
5. **Cross-Browser Testing:** Executes tests in parallel on different desktop and mobile browsers using BrowserStack.

### Features
- **Automated Web Scraping:** Extracts article data and content dynamically.
- **Image Handling:** Downloads cover images of articles when available.
- **Translation Support:** Integrates with a translation API to process Spanish article titles.
- **Parallel Execution:** Tests are run across 5 browser configurations simultaneously for efficiency.
- **Cross-Browser Compatibility:** Ensures functionality on both desktop and mobile platforms.

### Tools and Technologies
- **Programming Language:** Python
- **Browser Automation:** Selenium WebDriver
- **Cross-Browser Testing:** BrowserStack
- **Editor:** VS Code

## Notes
1. Ensure the virtual environment is set up.
2. Configure BrowserStack credentials and RapidAPI keys accordingly:
   - `BrowserStack USERNAME = "your_browserstack_username"`
   - `BrowserStack ACCESS_KEY = "your_browserstack_access_key"`
   - `RAPIDAPI_KEY = "your_rapidapi_key"`


## Running Tests
* Run a sample test:
  - To run these tests on Broswerstack running the following code via Terminal.
    ```
    browserstack-sdk ./ElPaisScraper.py
    ```

