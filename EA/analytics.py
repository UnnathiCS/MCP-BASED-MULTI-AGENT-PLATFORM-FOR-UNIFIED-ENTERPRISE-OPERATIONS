"""
Analytics and insights module for dashboard.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

def _get_db_connection():
    """Get database connection with error handling."""
    if not os.path.exists('tickets.db'):
        # Return empty results if DB doesn't exist
        return None
    return sqlite3.connect('tickets.db')

def _extract_date_from_iso(iso_string: str) -> str:
    """Extract date part from ISO format string."""
    if not iso_string:
        return None
    try:
        # ISO format: 2024-01-15T10:30:00.123456
        return iso_string.split('T')[0]
    except:
        return iso_string[:10] if len(iso_string) >= 10 else iso_string

def get_ticket_statistics(days: int = 30) -> Dict:
    """
    Get ticket statistics for the dashboard.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary with statistics
    """
    try:
        conn = _get_db_connection()
        if not conn:
            return {
                'total_tickets': 0,
                'intent_counts': {},
                'status_counts': {},
                'daily_volume': {},
                'avg_response_time': "N/A",
                'top_senders': [],
                'intent_distribution': {},
                'period_days': days
            }
        
        c = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Total tickets
        c.execute('SELECT COUNT(*) FROM tickets WHERE date >= ?', (cutoff_date,))
        result = c.fetchone()
        total_tickets = result[0] if result else 0
        
        # Tickets by intent
        c.execute('''
            SELECT intent, COUNT(*) 
            FROM tickets 
            WHERE date >= ? AND intent IS NOT NULL AND intent != ''
            GROUP BY intent
        ''', (cutoff_date,))
        intent_counts = dict(c.fetchall() or [])
        
        # Tickets by status (spam vs processed)
        c.execute('''
            SELECT 
                CASE 
                    WHEN intent = 'SPAM' THEN 'Spam'
                    WHEN response IS NOT NULL AND response != '' THEN 'Processed'
                    ELSE 'Pending'
                END as status,
                COUNT(*) 
            FROM tickets 
            WHERE date >= ?
            GROUP BY status
        ''', (cutoff_date,))
        status_counts = dict(c.fetchall() or [])
        
        # Daily ticket volume - handle date extraction manually
        c.execute('''
            SELECT date, COUNT(*) 
            FROM tickets 
            WHERE date >= ?
            ORDER BY date
        ''', (cutoff_date,))
        daily_data = c.fetchall() or []
        daily_volume = {}
        for date_str, count in daily_data:
            day = _extract_date_from_iso(date_str) if date_str else None
            if day:
                daily_volume[day] = daily_volume.get(day, 0) + count
        
        # Top senders
        c.execute('''
            SELECT sender, COUNT(*) as count
            FROM tickets
            WHERE date >= ? AND sender IS NOT NULL
            GROUP BY sender
            ORDER BY count DESC
            LIMIT 10
        ''', (cutoff_date,))
        top_senders = [{'email': row[0] or 'Unknown', 'count': row[1]} for row in (c.fetchall() or [])]
        
        # Intent distribution
        total_with_intent = sum(intent_counts.values())
        intent_distribution = {
            intent: round((count / total_with_intent * 100), 2) if total_with_intent > 0 else 0
            for intent, count in intent_counts.items()
        }
        
        conn.close()
        
        return {
            'total_tickets': total_tickets,
            'intent_counts': intent_counts,
            'status_counts': status_counts,
            'daily_volume': daily_volume,
            'avg_response_time': "N/A",
            'top_senders': top_senders,
            'intent_distribution': intent_distribution,
            'period_days': days
        }
    except Exception as e:
        print(f"Error in get_ticket_statistics: {e}")
        return {
            'total_tickets': 0,
            'intent_counts': {},
            'status_counts': {},
            'daily_volume': {},
            'avg_response_time': "N/A",
            'top_senders': [],
            'intent_distribution': {},
            'period_days': days,
            'error': str(e)
        }

def get_recent_tickets(limit: int = 10) -> List[Dict]:
    """
    Get recent tickets for dashboard.
    
    Args:
        limit: Maximum number of tickets to return
    
    Returns:
        List of ticket dictionaries
    """
    try:
        conn = _get_db_connection()
        if not conn:
            return []
        
        c = conn.cursor()
        
        # Include response field to determine status
        c.execute('''
            SELECT ticket_id, subject, sender, date, intent, assigned_agent, response
            FROM tickets
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))
        
        columns = ['ticket_id', 'subject', 'sender', 'date', 'intent', 'assigned_agent', 'response']
        rows = c.fetchall() or []
        tickets = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return tickets
    except Exception as e:
        print(f"Error in get_recent_tickets: {e}")
        return []

def get_performance_metrics(days: int = 30) -> Dict:
    """
    Get performance metrics.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        conn = _get_db_connection()
        if not conn:
            return {
                'processing_rate': 0,
                'spam_rate': 0,
                'total_processed': 0,
                'total_tickets': 0,
                'spam_count': 0
            }
        
        c = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Processing rate
        c.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN response IS NOT NULL AND response != '' THEN 1 ELSE 0 END) as processed
            FROM tickets
            WHERE date >= ?
        ''', (cutoff_date,))
        result = c.fetchone()
        total = result[0] if result else 0
        processed = result[1] if result else 0
        processing_rate = round((processed / total * 100), 2) if total > 0 else 0
        
        # Spam rate
        c.execute('''
            SELECT COUNT(*) 
            FROM tickets 
            WHERE date >= ? AND intent = 'SPAM'
        ''', (cutoff_date,))
        spam_result = c.fetchone()
        spam_count = spam_result[0] if spam_result else 0
        spam_rate = round((spam_count / total * 100), 2) if total > 0 else 0
        
        conn.close()
        
        return {
            'processing_rate': processing_rate,
            'spam_rate': spam_rate,
            'total_processed': processed,
            'total_tickets': total,
            'spam_count': spam_count
        }
    except Exception as e:
        print(f"Error in get_performance_metrics: {e}")
        return {
            'processing_rate': 0,
            'spam_rate': 0,
            'total_processed': 0,
            'total_tickets': 0,
            'spam_count': 0,
            'error': str(e)
        }

def get_trends(days: int = 30) -> Dict:
    """
    Get trend data for charts.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary with trend data
    """
    try:
        conn = _get_db_connection()
        if not conn:
            return {'daily_trends': []}
        
        c = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Daily trends - get all tickets and group by date manually
        c.execute('''
            SELECT 
                date,
                intent,
                response
            FROM tickets
            WHERE date >= ?
            ORDER BY date
        ''', (cutoff_date,))
        
        rows = c.fetchall() or []
        
        # Group by date
        daily_data = {}
        for row in rows:
            date_str, intent, response = row
            day = _extract_date_from_iso(date_str) if date_str else None
            if not day:
                continue
                
            if day not in daily_data:
                daily_data[day] = {'total': 0, 'spam': 0, 'processed': 0}
            
            daily_data[day]['total'] += 1
            if intent == 'SPAM':
                daily_data[day]['spam'] += 1
            if response and response.strip():
                daily_data[day]['processed'] += 1
        
        # Convert to list format
        trends = [
            {
                'date': day,
                'total': data['total'],
                'spam': data['spam'],
                'processed': data['processed']
            }
            for day, data in sorted(daily_data.items())
        ]
        
        conn.close()
        return {'daily_trends': trends}
    except Exception as e:
        print(f"Error in get_trends: {e}")
        return {'daily_trends': [], 'error': str(e)}

