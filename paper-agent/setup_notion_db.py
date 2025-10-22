"""
Notion Database Setup Script

This script helps you create and configure the Notion database
with the correct schema for the arXiv paper agent.
"""

import os
from notion_client import Client
from dotenv import load_dotenv

def setup_notion_database():
    """Setup the Notion database with correct schema."""
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not api_key or not database_id:
        print("❌ Please set NOTION_API_KEY and NOTION_DATABASE_ID in your .env file")
        return False
    
    try:
        client = Client(auth=api_key)
        
        # Get current database info
        db_info = client.databases.retrieve(database_id=database_id)
        print(f"✅ Connected to database: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
        
        # Define the correct properties
        properties = {
            "Title": {"title": {}},
            "Authors": {"rich_text": {}},
            "Abstract": {"rich_text": {}},
            "ArXiv ID": {"rich_text": {}},
            "Published Date": {"date": {}},
            "Categories": {"multi_select": {"options": []}},
            "ArXiv URL": {"url": {}},
            "Tags": {"multi_select": {"options": []}},
            "Relevance Score": {"number": {"format": "number"}},
            "Key Insights": {"rich_text": {}},
            "Methodology": {"rich_text": {}},
            "Limitations": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "New", "color": "blue"},
                        {"name": "Reviewed", "color": "green"},
                        {"name": "Rejected", "color": "red"}
                    ]
                }
            }
        }
        
        # Update the database with correct properties
        print("🔄 Updating database schema...")
        client.databases.update(
            database_id=database_id,
            properties=properties
        )
        
        print("✅ Database schema updated successfully!")
        print("\n📋 Database Properties:")
        for prop_name, prop_config in properties.items():
            prop_type = list(prop_config.keys())[0]
            print(f"  - {prop_name}: {prop_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def test_database():
    """Test the database by adding a sample paper."""
    
    load_dotenv()
    
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not api_key or not database_id:
        print("❌ Please set NOTION_API_KEY and NOTION_DATABASE_ID in your .env file")
        return False
    
    try:
        client = Client(auth=api_key)
        
        # Create a test page
        test_page = {
            "Title": {"title": [{"text": {"content": "Test Paper"}}]},
            "Authors": {"rich_text": [{"text": {"content": "Test Author"}}]},
            "Abstract": {"rich_text": [{"text": {"content": "This is a test paper for setup verification."}}]},
            "ArXiv ID": {"rich_text": [{"text": {"content": "test.1234.5678"}}]},
            "Published Date": {"date": {"start": "2024-01-01"}},
            "Categories": {"multi_select": [{"name": "cs.AI"}]},
            "ArXiv URL": {"url": "https://arxiv.org/abs/test.1234.5678"},
            "Tags": {"multi_select": [{"name": "Test"}]},
            "Relevance Score": {"number": 5.0},
            "Key Insights": {"rich_text": [{"text": {"content": "Test insight"}}]},
            "Methodology": {"rich_text": [{"text": {"content": "Test methodology"}}]},
            "Limitations": {"rich_text": [{"text": {"content": "Test limitation"}}]},
            "Status": {"select": {"name": "New"}}
        }
        
        print("🧪 Testing database with sample paper...")
        response = client.pages.create(
            parent={"database_id": database_id},
            properties=test_page
        )
        
        print(f"✅ Test page created successfully! Page ID: {response['id']}")
        
        # Clean up test page
        print("🧹 Cleaning up test page...")
        client.pages.update(
            page_id=response['id'],
            archived=True
        )
        print("✅ Test page archived")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Notion database for arXiv Paper Agent...")
    print("=" * 60)
    
    # Setup database schema
    if setup_notion_database():
        print("\n🧪 Testing database...")
        if test_database():
            print("\n🎉 Database setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Your Notion database is now ready")
            print("2. Run: python main.py --mode manual --days 7")
            print("3. Check your Notion database for the papers")
        else:
            print("\n⚠️ Database schema updated but test failed")
    else:
        print("\n❌ Database setup failed")

if __name__ == "__main__":
    main()
