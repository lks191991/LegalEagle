#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_db_methods import ChatHistoryOperations

def test_chat_history():
    print("Testing chat history API...")
    
    # Test get_admin_chat_history
    result = ChatHistoryOperations.get_admin_chat_history()
    print(f"Chat history result: {result}")
    
    # Test get_chat_usage_stats
    stats = ChatHistoryOperations.get_chat_usage_stats()
    print(f"Chat stats result: {stats}")

if __name__ == "__main__":
    test_chat_history()