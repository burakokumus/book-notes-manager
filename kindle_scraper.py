from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

class KindleScraper:
  def __init__(self, email, password):
    """Initialize the scraper with the given email and password. Can be extended to also get custom Selenium options."""
    self.email = email
    self.password = password
    self.options = webdriver.ChromeOptions()
    self.options.add_argument("--headless")
    self.driver = webdriver.Chrome(options=self.options)

    return

  def login(self):
    self.driver.get("https://read.amazon.com/kp/notebook")
    
    email_input = self.driver.find_element(By.XPATH, '//*[@id="ap_email"]')
    pass_input = self.driver.find_element(By.XPATH, '//*[@id="ap_password"]')
    email_input.send_keys(self.email)
    pass_input.send_keys(self.password)
    
    pass_input.send_keys(Keys.ENTER)
    
    print("Logging in")
    
    try:
      WebDriverWait(self.driver, timeout=45).until(
        lambda d: d.find_element(By.ID, 'annotations')
      )
      print("Login Successful")
    except Exception:
      raise TimeoutError("Login Timed-out")
    
  def get_books(self):
    """Return all the books in the library"""
    books = self.driver.find_elements(By.XPATH, '//div[contains(@class, \'kp-notebook-library-each-book\')]')
    return books
  
  def get_highlights_and_notes(self):
    """Return an array of dictionaries. Each dictionary represents a book and contains the title, the author, the highlights, and the notes."""
    books = self.get_books()
    
    result = []
    
    for book in books:
      
      title = book.text.splitlines()[0]
      author = book.text.splitlines()[1][4:]
      book_dictionary = {"title": title, "author": author}
      highlights = []
      notes = []
      
      print(f"Retrieving highlights for {title} by {author}")
      
      book.click()
      WebDriverWait(self.driver, timeout=45).until(
        lambda d: d.find_element(By.XPATH, "//span[contains(@id, 'highlight')]")
      )
      
      content_elements = self.driver.find_elements(
        By.XPATH,
        "//span[@id='highlight' or @id='note']"
      )

      for content in content_elements:
        if content.text != "":
          if content.get_attribute("id") == "highlight":
            highlights.append(content.text)
          else:
            notes.append(content.text)

      book_dictionary["highlights"] = highlights
      book_dictionary["notes"] = notes
      
      result.append(book_dictionary)
      
      print(f"Retrieved {len(highlights)} Highlights and {len(notes)} Notes for {title} by {author}\n")
    
    return result