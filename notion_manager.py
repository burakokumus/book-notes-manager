import requests
import json

class NotionManager:
  def __init__(self, books_db_id, secret_key, notion_version):
    self.books_db_id = books_db_id
    self.notion_secret_key = secret_key
    self.notion_version = notion_version

  def get_all_books(self, page_size = 100):
    """Return all the books in the Notion database.

    Args:
        page_size (int, optional): Maximum number of entries to return. Defaults to 100.

    Returns:
        Dictionary of book_id(string) to book_title(string).
    """
    result = {}
    
    request_url = f"https://api.notion.com/v1/databases/{self.books_db_id}/query"
    request_payload = {"page_size": page_size}
    request_headers = {
        "Accept": "application/json",
        "Notion-Version": f"{self.notion_version}",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.notion_secret_key}"
    }
    
    response = requests.post(request_url, json=request_payload, headers=request_headers)
    
    response_json = json.loads(response.text)
    for book in response_json["results"]:
      book_title = book["properties"]["Title"]["title"][0]["plain_text"]
      book_id = book["id"]
      result[book_id] = book_title
    
    return result

  def get_highlights_and_notes(self, book_id, page_size = 100):
    """Return highlights and notes for a given book from the Notion database.

    Args:
        book_id (string): ID of the book.
        page_size (int, optional): Maximum number of entries to return. Defaults to 100.

    Raises:
        Exception: Notion API Error.

    Returns:
        array, array: Return two arrays of strings for highlights and notes.
    """

    query_url = f"https://api.notion.com/v1/blocks/{book_id}/children?page_size={page_size}"

    query_headers = {
        "Accept": "application/json",
        "Notion-Version": f"{self.notion_version}",
        "Authorization": f"Bearer {self.notion_secret_key}"
    }

    query_response = requests.get(query_url, headers=query_headers)

    highlights = []
    notes = []
    data = json.loads(query_response.text)
    
    if query_response.status_code == 200:
      
      for item in data["results"]:
        if "quote" in item.keys():
          highlight_content = item["quote"]["rich_text"][0]["text"]["content"]
          highlights.append(highlight_content)
        elif "callout" in item.keys():
          note_content = item["callout"]["rich_text"][0]["text"]["content"]
          notes.append(note_content)

      return highlights, notes

    raise Exception(data['message'])
  
  def get_book_id(self, title):
    """Return the ID of the book with the given title if it exists in the database.

    Args:
        title (string): Title of the book.

    Returns:
        string: ID of the book.
    """
    request_url = f"https://api.notion.com/v1/databases/{self.books_db_id}/query"
    request_payload = {
      "page_size": 1,
      "filter": {
        "property": "Title",
        "rich_text": {
          "equals": title
        }
      }
    }
    request_headers = {
        "Accept": "application/json",
        "Notion-Version": f"{self.notion_version}",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.notion_secret_key}"
    }
    
    response = requests.post(request_url, json=request_payload, headers=request_headers)
    
    response_json = json.loads(response.text)
    
    if len(response_json['results']) == 0:
      return None
    
    return response_json['results'][0]['id']

  def delete_book(self, title):
    """Delete the book entry with the given title if it exists in the Notion database.

    Args:
        title (string): Title of the book to be deleted.

    Raises:
        Exception: Notion API Error.

    Returns:
        bool: Success.
    """
    book_id = self.get_book_id(title)
    if not book_id:
      return False
    
    request_url = f"https://api.notion.com/v1/pages/{book_id}"
    request_payload = {
      "archived": True
    }
    request_headers = {
        "Accept": "application/json",
        "Notion-Version": f"{self.notion_version}",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.notion_secret_key}"
    }
    
    response = requests.patch(request_url, json=request_payload, headers=request_headers)
    
    response_json = json.loads(response.text)
    
    if response.status_code == 200:
      return True
    
    raise Exception(response_json['message'])
  
  def insert_book(self, title, author, highlights, notes):
    """Insert a book to the database.

    Args:
        title (string): Book Title.
        author (string): Name of the Author.
        highlights (array[string]): Highlights from the book.
        notes (array[string]): Notes from the book.

    Raises:
        Exception: Notion API Error.

    Returns:
        bool: Success.
    """
    request_url = "https://api.notion.com/v1/pages"
    
    highlights_title = "HIGHLIGHTS"
    notes_title = "NOTES"
    
    highlights_heading_element = {
      "type": "heading_1",
      "heading_1": {
        "rich_text": [{
          "type": "text",
          "text": {
            "content": highlights_title,
            "link": None
          }
        }],
        "color": "yellow",
        "is_toggleable": False
      }
    }
    
    notes_heading_element = {
      "type": "heading_1",
      "heading_1": {
        "rich_text": [{
          "type": "text",
          "text": {
            "content": notes_title,
            "link": None
          }
        }],
        "color": "yellow",
        "is_toggleable": False
      }
    }
    
    page_children = []
    
    # Highlights
    page_children.append(highlights_heading_element)
    
    for highlight in highlights:
      page_children.append({
        "type": "quote",
        "quote": {
          "rich_text": [{
            "type": "text",
            "text": {
              "content": highlight
            }
          }],
          "color": "default"
        }
      })
      
    # Notes
    page_children.append(notes_heading_element)
    
    for note in notes:
      page_children.append({
        "type": "callout",
        "callout": {
          "rich_text": [{
            "type": "text",
            "text": {
              "content": note
            }
          }],
          "icon": {
            "emoji": "💡"
          },
          "color": "default"
        }
      })
    
    request_payload = {
      "children": page_children,
      "parent": {
        "type": "database_id",
        "database_id": self.books_db_id
      },
      "properties": {
        "Title": {
          "title": [
            {
              "type": "text",
              "text": {
                "content": title
              }
            }
          ]
        },
        "Author": {
          "rich_text": [
            {
              "type": "text",
              "text": {
                "content": author
              }
            }
          ]
        }
      }
    }
    
    request_headers = {
      "Accept": "application/json",
      "Notion-Version": f"{self.notion_version}",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {self.notion_secret_key}"  
    }
    
    # In case the book already exists in the database
    self.delete_book(title)
    
    response = requests.post(request_url, json=request_payload, headers=request_headers)
    
    response_json = json.loads(response.text)
    
    if response.status_code == 200:
      return True
    
    raise Exception(response_json['message'])
  