from Scraper.LimitedWebScraper import LimitedWebScraper
import os
from dotenv import load_dotenv
if __name__ == "__main__":

   homepage = "https://www.instructables.com/sitemap"

  # List of blacklisted URLs to exclude
   blacklist = [
        "https://www.instructables.com/",
        "https://www.instructables.com/projects/",
        "https://www.instructables.com/contest/",
        "https://www.instructables.com/teachers/",
        "https://www.instructables.com/contact/",
        "https://www.instagram.com/instructables/",
        "https://www.tiktok.com/@instructables",
        "https://www.autodesk.com/company/legal-notices-trademarks/terms-of-service-autodesk360-web-services/instructables-terms-of-service-june-5-2013",
        "https://www.instructables.com/circuits/",
        "https://www.instructables.com/workshop/",
        "https://www.instructables.com/craft/",
        "https://www.instructables.com/cooking/",
        "https://www.instructables.com/living/",
        "https://www.instructables.com/outside/",
        "https://www.instructables.com/teachers/",
        "https://www.instructables.com/about/",
        "https://www.instructables.com/create/",
        "https://www.instructables.com/sitemap/",
        "https://www.instructables.com/how-to-write-a-great-instructable/",
        'https://www.autodesk.com/company/legal-notices-trademarks/privacy-statement',
        'https://www.autodesk.com/company/legal-notices-trademarks',
        'https://www.autodesk.com'
    ]
   mongo_uri = os.getenv('MONGO_URI')
   main_save_path = "/Users/eyalbenbarouch/Documents/My Stuff/Handyman_LLM_Agent"
# Initialize the main scraper class
   scraper = LimitedWebScraper(homepage=homepage, max_seen_urls_per_topic=1000, blacklist=blacklist, save_content=True,main_save_path=main_save_path,mongo_uri=mongo_uri)

  # Run the full scraping process
   scraper.run()
