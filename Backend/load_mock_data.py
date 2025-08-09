#!/usr/bin/env python3
"""
Script to load mock FAQ data into ChromaDB
Run this script to populate the ChromaDB collection with sample IT helpdesk FAQs
"""

from services.chroma_service import chroma_service
import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    """Load mock FAQ data into ChromaDB"""
    print("Loading mock FAQ data into ChromaDB...")

    try:
        # Check current collection stats
        stats = chroma_service.get_collection_stats()
        print(f"Current collection status: {stats}")

        # Load mock data
        success = chroma_service.load_mock_data()

        if success:
            # Show updated stats
            updated_stats = chroma_service.get_collection_stats()
            print(f"Updated collection status: {updated_stats}")
            print("✅ Mock data loaded successfully!")

            # Test search functionality
            print("\n🔍 Testing search functionality...")
            test_query = "password reset"
            results = chroma_service.search_faqs(test_query, n_results=3)

            print(f"Search results for '{test_query}':")
            for i, result in enumerate(results, 1):
                print(
                    f"{i}. {result['title']} (Score: {result['similarity_score']:.3f})")

        else:
            print("❌ Failed to load mock data")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
