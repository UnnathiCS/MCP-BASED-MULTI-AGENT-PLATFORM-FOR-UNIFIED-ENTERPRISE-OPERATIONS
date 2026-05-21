from datetime import datetime, timedelta
from typing import Dict, List

from app.database.connection import get_tickets_conn


def _extract_date(iso_string: str):
    if not iso_string:
        return None
    try:
        return iso_string.split('T')[0]
    except:
        return iso_string[:10] if len(iso_string) >= 10 else iso_string


def get_ticket_statistics(days: int = 30) -> Dict:
    try:
        conn = get_tickets_conn()
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        c.execute('SELECT COUNT(*) FROM tickets WHERE date >= ?', (cutoff,))
        total_tickets = (c.fetchone() or [0])[0]

        c.execute('''SELECT intent, COUNT(*) FROM tickets
            WHERE date >= ? AND intent IS NOT NULL AND intent != '' GROUP BY intent''', (cutoff,))
        intent_counts = dict(c.fetchall() or [])

        c.execute('''SELECT
                CASE WHEN intent = 'SPAM' THEN 'Spam'
                     WHEN response IS NOT NULL AND response != '' THEN 'Processed'
                     ELSE 'Pending' END as status, COUNT(*)
            FROM tickets WHERE date >= ? GROUP BY status''', (cutoff,))
        status_counts = dict(c.fetchall() or [])

        c.execute('SELECT date, COUNT(*) FROM tickets WHERE date >= ? ORDER BY date', (cutoff,))
        daily_volume = {}
        for date_str, count in (c.fetchall() or []):
            day = _extract_date(date_str)
            if day:
                daily_volume[day] = daily_volume.get(day, 0) + count

        c.execute('''SELECT sender, COUNT(*) as count FROM tickets
            WHERE date >= ? AND sender IS NOT NULL
            GROUP BY sender ORDER BY count DESC LIMIT 10''', (cutoff,))
        top_senders = [{'email': r[0] or 'Unknown', 'count': r[1]} for r in (c.fetchall() or [])]

        total_with_intent = sum(intent_counts.values())
        intent_distribution = {
            intent: round(count / total_with_intent * 100, 2) if total_with_intent > 0 else 0
            for intent, count in intent_counts.items()
        }
        conn.close()
        return {'total_tickets': total_tickets, 'intent_counts': intent_counts,
                'status_counts': status_counts, 'daily_volume': daily_volume,
                'avg_response_time': "N/A", 'top_senders': top_senders,
                'intent_distribution': intent_distribution, 'period_days': days}
    except Exception as e:
        return {'total_tickets': 0, 'intent_counts': {}, 'status_counts': {},
                'daily_volume': {}, 'avg_response_time': "N/A", 'top_senders': [],
                'intent_distribution': {}, 'period_days': days, 'error': str(e)}


def get_recent_tickets(limit: int = 10) -> List[Dict]:
    try:
        conn = get_tickets_conn()
        c = conn.cursor()
        c.execute('''SELECT ticket_id, subject, sender, date, intent, assigned_agent, response
            FROM tickets ORDER BY date DESC LIMIT ?''', (limit,))
        columns = ['ticket_id', 'subject', 'sender', 'date', 'intent', 'assigned_agent', 'response']
        tickets = [dict(zip(columns, row)) for row in (c.fetchall() or [])]
        conn.close()
        return tickets
    except Exception:
        return []


def get_performance_metrics(days: int = 30) -> Dict:
    try:
        conn = get_tickets_conn()
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('''SELECT COUNT(*) as total,
                SUM(CASE WHEN response IS NOT NULL AND response != '' THEN 1 ELSE 0 END) as processed
            FROM tickets WHERE date >= ?''', (cutoff,))
        result = c.fetchone()
        total = result[0] if result else 0
        processed = result[1] if result else 0
        processing_rate = round(processed / total * 100, 2) if total > 0 else 0
        c.execute("SELECT COUNT(*) FROM tickets WHERE date >= ? AND intent = 'SPAM'", (cutoff,))
        spam_count = (c.fetchone() or [0])[0]
        spam_rate = round(spam_count / total * 100, 2) if total > 0 else 0
        conn.close()
        return {'processing_rate': processing_rate, 'spam_rate': spam_rate,
                'total_processed': processed, 'total_tickets': total, 'spam_count': spam_count}
    except Exception as e:
        return {'processing_rate': 0, 'spam_rate': 0, 'total_processed': 0,
                'total_tickets': 0, 'spam_count': 0, 'error': str(e)}


def get_trends(days: int = 30) -> Dict:
    try:
        conn = get_tickets_conn()
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('SELECT date, intent, response FROM tickets WHERE date >= ? ORDER BY date', (cutoff,))
        daily_data = {}
        for date_str, intent, response in (c.fetchall() or []):
            day = _extract_date(date_str)
            if not day:
                continue
            if day not in daily_data:
                daily_data[day] = {'total': 0, 'spam': 0, 'processed': 0}
            daily_data[day]['total'] += 1
            if intent == 'SPAM':
                daily_data[day]['spam'] += 1
            if response and response.strip():
                daily_data[day]['processed'] += 1
        conn.close()
        return {'daily_trends': [
            {'date': day, **data} for day, data in sorted(daily_data.items())
        ]}
    except Exception as e:
        return {'daily_trends': [], 'error': str(e)}
