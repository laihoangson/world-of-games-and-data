from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import json
from datetime import datetime
import atexit
import signal
import sys

app = Flask(__name__)
CORS(app)  # Cho phép cross-origin requests

# Database setup
def init_db():
    conn = sqlite3.connect('plane_analytics.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            id TEXT PRIMARY KEY,
            start_time TEXT,
            end_time TEXT,
            score INTEGER,
            coins_collected INTEGER,
            ufos_shot INTEGER,
            bullets_fired INTEGER,
            death_reason TEXT,
            game_duration INTEGER,
            pipes_passed INTEGER,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# THÊM: Hàm xử lý tắt server
def shutdown_handler(signum=None, frame=None):
    print("\n🛑 Server is shutting down gracefully...")
    print("💾 Analytics data has been saved to plane_analytics.db")
    sys.exit(0)

# Đăng ký handlers cho tắt server
atexit.register(shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

@app.route('/api/game-analytics', methods=['POST', 'OPTIONS'])
def receive_analytics():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        print("Received analytics data:", data)  # Debug log
        
        # Kiểm tra nếu là mảng (nhiều analytics)
        if isinstance(data, list):
            return process_batch_analytics(data)
        else:
            return process_single_analytics(data)
        
    except Exception as e:
        print(f"Error storing analytics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# THÊM: Xử lý batch analytics
def process_batch_analytics(analytics_list):
    try:
        conn = sqlite3.connect('plane_analytics.db')
        c = conn.cursor()
        
        success_count = 0
        for data in analytics_list:
            try:
                c.execute('''
                    INSERT OR REPLACE INTO game_sessions 
                    (id, start_time, end_time, score, coins_collected, ufos_shot, bullets_fired, death_reason, game_duration, pipes_passed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('gameId'),
                    data.get('startTime'),
                    data.get('endTime'),
                    data.get('score'),
                    data.get('coinsCollected'),
                    data.get('ufosShot'),
                    data.get('bulletsFired'),
                    data.get('deathReason'),
                    data.get('gameDuration'),
                    data.get('pipesPassed')
                ))
                success_count += 1
            except Exception as e:
                print(f"Error processing game {data.get('gameId')}: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': f'Processed {success_count}/{len(analytics_list)} analytics'
        }), 200
        
    except Exception as e:
        print(f"Error storing batch analytics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# THÊM: Xử lý single analytics
def process_single_analytics(data):
    try:
        conn = sqlite3.connect('plane_analytics.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO game_sessions 
            (id, start_time, end_time, score, coins_collected, ufos_shot, bullets_fired, death_reason, game_duration, pipes_passed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('gameId'),
            data.get('startTime'),
            data.get('endTime'),
            data.get('score'),
            data.get('coinsCollected'),
            data.get('ufosShot'),
            data.get('bulletsFired'),
            data.get('deathReason'),
            data.get('gameDuration'),
            data.get('pipesPassed')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Error storing analytics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# THÊM: Endpoint để client đồng bộ dữ liệu local
@app.route('/api/sync-analytics', methods=['POST', 'OPTIONS'])
def sync_analytics():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        local_games = data.get('games', [])
        
        print(f"Syncing {len(local_games)} local games to server")
        
        return process_batch_analytics(local_games)
        
    except Exception as e:
        print(f"Error syncing analytics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/plane-stats')
def get_plane_stats():
    try:
        conn = sqlite3.connect('plane_analytics.db')
        c = conn.cursor()
        
        # Basic stats - thêm avg_bullets
        c.execute('SELECT COUNT(*), AVG(score), MAX(score), AVG(game_duration), AVG(bullets_fired) FROM game_sessions')
        result = c.fetchone()
        total_games = result[0] if result[0] else 0
        avg_score = round(result[1] or 0, 1)
        max_score = result[2] or 0
        avg_duration = round(result[3] or 0, 1)
        avg_bullets = round(result[4] or 0, 1)
        
        # Death reasons
        c.execute('SELECT death_reason, COUNT(*) FROM game_sessions WHERE death_reason IS NOT NULL GROUP BY death_reason')
        death_reasons = dict(c.fetchall())
        
        # Recent games - thêm bullets_fired
        c.execute('''
            SELECT score, coins_collected, ufos_shot, bullets_fired, game_duration, death_reason 
            FROM game_sessions 
            ORDER BY end_time DESC 
            LIMIT 10
        ''')
        recent_games = [
            {
                'score': row[0],
                'coins': row[1],
                'ufos': row[2],
                'bullets': row[3],
                'duration': row[4],
                'death_reason': row[5]
            }
            for row in c.fetchall()
        ]
        
        # Score distribution với buckets mới
        c.execute('SELECT score FROM game_sessions')
        scores = [row[0] for row in c.fetchall()]

        score_distribution = {
            '0-4': 0,
            '5-9': 0,
            '10-14': 0,
            '15-19': 0,
            '20-24': 0,
            '25-29': 0,
            '30-34': 0,
            '35-39': 0,
            '40-44': 0,
            '45-49': 0,
            '50+': 0
        }

        # Count scores in each bucket
        for score in scores:
            if score >= 50:
                score_distribution['50+'] += 1
            elif score >= 45:
                score_distribution['45-49'] += 1
            elif score >= 40:
                score_distribution['40-44'] += 1
            elif score >= 35:
                score_distribution['35-39'] += 1
            elif score >= 30:
                score_distribution['30-34'] += 1
            elif score >= 25:
                score_distribution['25-29'] += 1
            elif score >= 20:
                score_distribution['20-24'] += 1
            elif score >= 15:
                score_distribution['15-19'] += 1
            elif score >= 10:
                score_distribution['10-14'] += 1
            elif score >= 5:
                score_distribution['5-9'] += 1
            else:
                score_distribution['0-4'] += 1
        
        # Lấy tất cả games cho scatter plots - thêm bullets_fired
        c.execute('''
            SELECT score, coins_collected, ufos_shot, bullets_fired, game_duration
            FROM game_sessions
        ''')
        all_games = [
            {
                'score': row[0],
                'coins': row[1],
                'ufos': row[2],
                'bullets': row[3],
                'duration': row[4]
            }
            for row in c.fetchall()
        ]
        
        # Thêm stats về bullets
        c.execute('SELECT MAX(bullets_fired), AVG(bullets_fired) FROM game_sessions')
        bullet_stats = c.fetchone()
        max_bullets = bullet_stats[0] or 0
        avg_bullets = round(bullet_stats[1] or 0, 1)
        
        conn.close()
        
        return jsonify({
            'total_games': total_games,
            'avg_score': avg_score,
            'max_score': max_score,
            'avg_duration': avg_duration,
            'avg_bullets': avg_bullets,
            'max_bullets': max_bullets,
            'death_reasons': death_reasons,
            'recent_games': recent_games,
            'score_distribution': score_distribution,
            'all_games': all_games  # Thêm dữ liệu cho scatter plots
        })
        
    except Exception as e:
        print(f"Error retrieving stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'plane-analytics'})

if __name__ == '__main__':
    init_db()
    print("🚀 Plane Analytics Server starting on http://localhost:5000")
    print("💾 Data will be saved to plane_analytics.db")
    print("⚠️  Press Ctrl+C to stop server - data will be preserved")
    app.run(debug=True, port=5000, host='0.0.0.0')