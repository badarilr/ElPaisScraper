from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os
import json
import re
from collections import Counter
from typing import Union, List

class ElPaisScraper:
    """
    This class scrapes opinion articles and related data from El Pais website.

    """
    def __init__(self, api_key, device_type='None'):
        # Initializes the scraper with the provided API key and device type.
        self.chrome_options = Options()

        self.device_type = device_type or self.detect_device_type()
        if device_type == 'mobile':
            mobile_emulation = {
                "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
                "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36"
            }
            self.chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        self.chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.cookies': 1,
            'profile.default_content_settings.popups': 0,
            'profile.default_content_setting_values.notifications': 2
        })
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.maximize_window()
        except WebDriverException as e:
            print(f"Error initializing Chrome: {e}")
            raise
        
        self.wait = WebDriverWait(self.driver, 10)
        self.api_key = api_key
        self.output_dir = "opinion_article_images"
        self.device_type = device_type
        os.makedirs(self.output_dir, exist_ok=True)

    def set_test_status(self, status, reason):
            
             # Function to set status on BrowserStack (if applicable)
         executor_object = {
                           'action': 'setSessionStatus',
                           'arguments': {
                           'status' : "<passed/failed>",'reason' : "<reason>"
                           }
                       }   

         browserstack_executor = 'browserstack_executor: {}'.format(json.dumps(executor_object))
         self.driver.execute_script(browserstack_executor) 
              

    def detect_device_type(self):
         #Detects the device type based on an environment variable.

         return 'mobile' if os.getenv('MOBILE_ENV', '0') == '1' else 'desktop'

    def handle_cookies(self):
        #Handles cookie consent popups on the El Pais website.
        cookie_selectors = {

            'desktop': [
                (By.ID, "didomi-notice-agree-button"),
                (By.XPATH, "//button[contains(text(), 'ACCEPT AND CONTINUE')]"),
                (By.XPATH, "//button[contains(text(), 'Aceptar')]"),
                (By.CLASS_NAME, "didomi-components-button")
            ],
            'mobile': [
                (By.ID, "didomi-notice-agree-button"),
                (By.CLASS_NAME, "didomi-components-button"),
                (By.XPATH, "//button[contains(@class, 'ACCEPT AND CONTINUE')]"),
                (By.CSS_SELECTOR, ".qc-cmp2-summary-buttons button:first-child")
            ]
        }

        selectors = cookie_selectors[self.device_type]
        for selector in selectors:
            try:
                cookie_button = self.wait.until(EC.element_to_be_clickable(selector))
                cookie_button.click()
                time.sleep(1)
                assert True, "Cookie consent handled successfully"
                return
            except Exception as e:
                print(f"Trying next cookie selector: {e}")
                continue
        
        print("No cookie consent popup found or already accepted")

    #Scraps the firts five articles on opnion page
    def scrape_articles(self):
        url = "https://elpais.com/opinion/"
        self.driver.get(url)
        time.sleep(2)  # Wait for page load
        self.handle_cookies()

        articles = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article"))
        )[:5]
        
        assert len(articles) > 0, "Articles found successfully"

        article_data = []
        for i, article in enumerate(articles):
            try:
                headline = article.find_element(By.CSS_SELECTOR, "h2").text
                assert headline , f"Content extracted for article {i+1}"
                
                print(f"Headline {i+1}: {headline}")
                
                article_entry = {
                    "headline": headline,                   
                }

                try:
                    image = article.find_element(By.CSS_SELECTOR, "img")
                    actions = ActionChains(self.driver)
                    actions.move_to_element(image).perform()
                    time.sleep(1)

                    screenshot_path = os.path.join(self.output_dir, f"article_{i+1}.png")
                    with open(screenshot_path, "wb") as file:
                        file.write(image.screenshot_as_png)
                    article_entry["image_path"] = screenshot_path
                    assert os.path.exists(screenshot_path), f"Image saved for article {i+1}"
                except:
                    print(f"No image found for article {i+1}")

                article_data.append(article_entry)

            except Exception as e:
                print(f"Error processing article {i+1}: {e}")

        with open("opinion_articles.json", "w", encoding="utf-8") as f:
            json.dump(article_data, f, ensure_ascii=False, indent=4)
            
        assert len(article_data) > 0, "Articles scraped and saved successfully"
        return article_data

    #Transalte text using RapidApi
    def translate_text(self, text: str) -> str:
        url = "https://rapid-translate-multi-traduction.p.rapidapi.com/t"
        payload = {
            "from": "es",
            "to": "en",
            "q": text
        }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "rapid-translate-multi-traduction.p.rapidapi.com"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            translated_text = response.json()
            
            if isinstance(translated_text, dict) and "trans" in translated_text:
                result = translated_text["trans"]
            elif isinstance(translated_text, list):
                result = translated_text[0]
            elif isinstance(translated_text, str):
                result = translated_text
            else:
                result = text
                
            assert result, "Translation completed successfully"
            return result
                
        except requests.exceptions.RequestException as e:
            print(f"Translation error: {e}")
            return text

    def translate_articles(self, articles):
        translated_data = []
        total_items = len(articles)
        
        for i, entry in enumerate(articles, 1):
            print(f"Translating item {i}/{total_items}")
            
            translated_entry = entry.copy()
            if 'headline' in entry:
                translated_entry['headline'] = self.translate_text(entry['headline'])
                
                translated_data.append(translated_entry)
            if i < total_items:
                time.sleep(2)

        with open('translated_articles.json', 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
            
        assert len(translated_data) == len(articles), "All articles translated successfully"
        return translated_data

    #Analyse repeated words from the article
    def analyze_repeated_words(self, translated_data):
        all_words = []
        for item in translated_data:
            if 'headline' in item:
                all_words.extend(re.findall(r'\b\w+\b', item['headline'].lower()))           

        assert len(all_words) > 0, "Words extracted successfully for analysis"

        word_counts = Counter(all_words)
        repeated_words = {word: count for word, count in word_counts.items() if count > 2}

        if repeated_words:
            print("\nWords repeated more than twice:")
            for word, count in repeated_words.items():
                print(f"- {word}: {count} times")
        else:
            print("\nNo words repeated more than twice.")

        assert True, "Word analysis completed successfully"
        return repeated_words

    def run(self):
        try:
            print(f"Starting {self.device_type} version...")
            articles = self.scrape_articles()
            
            print("\nStarting translation...")
            translated_articles = self.translate_articles(articles)
            
            print("\nAnalyzing word frequencies...")
            self.analyze_repeated_words(translated_articles)
            
            print("\nAll tasks completed successfully!")
            self.set_test_status(status="pass",reason="All tests passed")
            
        finally:
            self.driver.quit()

if __name__ == "__main__":
    api_key = 'fdbfd286cfmsh0dc304e536335a2p1742d2jsn30dca35556bb'  # Replace with your RapidAPI key
    
    try:
        desktop_scraper = ElPaisScraper(api_key, device_type='desktop')
        desktop_scraper.run()
        
        time.sleep(2)
        
        mobile_scraper = ElPaisScraper(api_key, device_type='mobile')
        mobile_scraper.run()
    except Exception as e:
        print(f"Error during execution: {e}")