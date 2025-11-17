from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import json
from datetime import datetime
import atexit
import signal
import sys
import os

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

# THÊM: Export data to JSON file
@app.route('/api/export-data')
def export_data():
    try:
        conn = sqlite3.connect('plane_analytics.db')
        c = conn.cursor()
        
        # Lấy tất cả data
        c.execute('''
            SELECT id, start_time, end_time, score, coins_collected, ufos_shot, 
                   bullets_fired, death_reason, game_duration, pipes_passed
            FROM game_sessions
        ''')
        
        games = []
        for row in c.fetchall():
            games.append({
                'id': row[0],
                'startTime': row[1],
                'endTime': row[2],
                'score': row[3],
                'coinsCollected': row[4],
                'ufosShot': row[5],
                'bulletsFired': row[6],
                'deathReason': row[7],
                'gameDuration': row[8],
                'pipesPassed': row[9]
            })
        
        conn.close()
        
        # Tạo thư mục data nếu chưa tồn tại
        os.makedirs('static/data', exist_ok=True)
        
        # Export to JSON file
        with open('static/data/analytics.json', 'w', encoding='utf-8') as f:
            json.dump({
                'games': games,
                'last_updated': datetime.now().isoformat(),
                'total_games': len(games)
            }, f, indent=2)
        
        return jsonify({'status': 'success', 'exported_games': len(games)})
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# THÊM: Generate complete stats data for static usage
def generate_complete_stats():
    try:
        conn = sqlite3.connect('plane_analytics.db')
        c = conn.cursor()
        
        # Basic stats
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
        
        # Recent games
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
        
        # Score distribution
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
        
        # All games for scatter plots
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
        
        # Bullets stats
        c.execute('SELECT MAX(bullets_fired), AVG(bullets_fired) FROM game_sessions')
        bullet_stats = c.fetchone()
        max_bullets = bullet_stats[0] or 0
        avg_bullets = round(bullet_stats[1] or 0, 1)
        
        conn.close()
        
        return {
            'total_games': total_games,
            'avg_score': avg_score,
            'max_score': max_score,
            'avg_duration': avg_duration,
            'avg_bullets': avg_bullets,
            'max_bullets': max_bullets,
            'death_reasons': death_reasons,
            'recent_games': recent_games,
            'score_distribution': score_distribution,
            'all_games': all_games
        }
        
    except Exception as e:
        print(f"Error generating stats: {e}")
        return {}

# THÊM: Export complete stats to JSON
@app.route('/api/export-stats')
def export_stats():
    try:
        stats_data = generate_complete_stats()
        
        # Tạo thư mục data nếu chưa tồn tại
        os.makedirs('static/data', exist_ok=True)
        
        # Export stats to JSON file
        with open('static/data/stats.json', 'w', encoding='utf-8') as f:
            json.dump({
                **stats_data,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
        
        return jsonify({'status': 'success', 'message': 'Stats exported successfully'})
        
    except Exception as e:
        print(f"Error exporting stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# THÊM: Generate static HTML dashboard
@app.route('/api/generate-dashboard')
def generate_dashboard():
    try:
        # Get current stats
        stats_data = generate_complete_stats()
        
        # Tạo thư mục static nếu chưa tồn tại
        os.makedirs('static', exist_ok=True)
        
        # HTML template với data nhúng sẵn
        html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flappy Plane Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}

        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card h3 {{
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            opacity: 0.9;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}

        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        .chart-box {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            height: 400px;
            position: relative;
        }}

        .chart-box h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.4em;
        }}

        .chart-container {{
            height: 300px;
            position: relative;
        }}

        .scatter-charts {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        .recent-games {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}

        .recent-games h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.4em;
        }}

        .game-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .game-table th {{
            background: #34495e;
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: bold;
            border: none;
        }}

        .game-table td {{
            padding: 12px 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}

        .game-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .game-table tr:hover {{
            background: #e9ecef;
        }}

        .info-banner {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}

        @media (max-width: 768px) {{
            .charts-container, .scatter-charts {{
                grid-template-columns: 1fr;
            }}
            
            .stat-card .value {{
                font-size: 2em;
            }}
            
            .chart-box {{
                height: 350px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Flappy Plane Analytics</h1>
            <p>Static Dashboard - Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <div class="info-banner">
            <strong>📊 Static Dashboard</strong> - This dashboard shows analytics data exported at {datetime.now().strftime("%H:%M:%S on %Y-%m-%d")}. 
            For real-time data, run the Flask analytics server.
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Games Played</h3>
                <div class="value">{stats_data.get('total_games', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Average Score</h3>
                <div class="value">{stats_data.get('avg_score', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Highest Score</h3>
                <div class="value">{stats_data.get('max_score', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Duration (s)</h3>
                <div class="value">{stats_data.get('avg_duration', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Bullets Fired</h3>
                <div class="value">{stats_data.get('avg_bullets', 0)}</div>
            </div>
        </div>

        <div class="charts-container">
            <div class="chart-box">
                <h2>Death Reasons Distribution</h2>
                <div class="chart-container">
                    <canvas id="deathChart"></canvas>
                </div>
            </div>
            
            <div class="chart-box">
                <h2>Score Distribution</h2>
                <div class="chart-container">
                    <canvas id="scoreChart"></canvas>
                </div>
            </div>
        </div>

        <div class="scatter-charts">
            <div class="chart-box">
                <h2>Score vs Bullets Fired</h2>
                <div class="chart-container">
                    <canvas id="scoreBulletsChart"></canvas>
                </div>
            </div>
            
            <div class="chart-box">
                <h2>UFOs Shot vs Coins Collected</h2>
                <div class="chart-container">
                    <canvas id="ufoCoinChart"></canvas>
                </div>
            </div>
        </div>

        <div class="recent-games">
            <h2>Recent Game Sessions</h2>
            <table class="game-table">
                <thead>
                    <tr>
                        <th>Score</th>
                        <th>Coins</th>
                        <th>UFOs Shot</th>
                        <th>Bullets Fired</th>
                        <th>Duration (s)</th>
                        <th>Death Reason</th>
                    </tr>
                </thead>
                <tbody id="recentGamesBody">
                    {"".join(f'''
                    <tr>
                        <td style="font-weight: bold; color: #2c3e50;">{game['score']}</td>
                        <td>{game['coins']}</td>
                        <td>{game['ufos']}</td>
                        <td>{game['bullets']}</td>
                        <td>{game['duration']}</td>
                        <td>{(game['death_reason'] or 'unknown').replace('_', ' ')}</td>
                    </tr>
                    ''' for game in stats_data.get('recent_games', []))}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Embedded data from Flask server
        const statsData = {json.dumps(stats_data)};
        
        // Initialize charts with embedded data
        document.addEventListener('DOMContentLoaded', function() {{
            createDeathReasonsChart(statsData.death_reasons || {{}});
            createScoreHistogram(statsData.score_distribution || {{}});
            createScatterPlots(statsData.all_games || []);
        }});

        // Chart functions (same as your original JavaScript)
        function createDeathReasonsChart(deathReasons) {{
            const ctx = document.getElementById('deathChart').getContext('2d');
            const chartColors = {{
                pipe: '#e74c3c',
                ufo_collision: '#9b59b6',
                enemy_bullet: '#3498db',
                ground: '#f39c12',
                ceiling: '#1abc9c',
                unknown: '#95a5a6'
            }};

            const labels = Object.keys(deathReasons).map(reason => 
                reason.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())
            );
            const data = Object.values(deathReasons);
            const backgroundColors = Object.keys(deathReasons).map(reason => chartColors[reason] || chartColors.unknown);

            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: data,
                        backgroundColor: backgroundColors,
                        borderColor: 'white',
                        borderWidth: 2,
                        hoverOffset: 10
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'right',
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${{label}}: ${{value}} (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }},
                    cutout: '60%'
                }}
            }});
        }}

        function createScoreHistogram(scoreBuckets) {{
            const ctx = document.getElementById('scoreChart').getContext('2d');
            
            const sortedEntries = Object.entries(scoreBuckets).sort((a, b) => {{
                const getBucketValue = (bucket) => {{
                    if (bucket === '50+') return 999;
                    if (bucket.includes('-')) {{
                        return parseInt(bucket.split('-')[0]);
                    }}
                    return parseInt(bucket);
                }};
                return getBucketValue(a[0]) - getBucketValue(b[0]);
            }});

            const sortedLabels = sortedEntries.map(entry => entry[0]);
            const sortedData = sortedEntries.map(entry => entry[1]);

            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: sortedLabels,
                    datasets: [{{
                        label: 'Number of Games',
                        data: sortedData,
                        backgroundColor: 'rgba(102, 126, 234, 0.7)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1,
                        borderRadius: 5,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Number of Games' }} }},
                        x: {{ title: {{ display: true, text: 'Score Range' }} }}
                    }}
                }}
            }});
        }}

        function createScatterPlots(games) {{
            // Score vs Bullets
            const scoreBulletsCtx = document.getElementById('scoreBulletsChart').getContext('2d');
            const scoreBulletsData = games.map(game => ({{ x: game.bullets || 0, y: game.score || 0 }}));
            
            new Chart(scoreBulletsCtx, {{
                type: 'scatter',
                data: {{
                    datasets: [{{
                        label: 'Games',
                        data: scoreBulletsData,
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                        pointRadius: 6,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Bullets Fired' }} }},
                        y: {{ title: {{ display: true, text: 'Score' }} }}
                    }}
                }}
            }});

            // UFOs vs Coins
            const ufoCoinCtx = document.getElementById('ufoCoinChart').getContext('2d');
            const ufoCoinData = games.map(game => ({{ x: game.coins || 0, y: game.ufos || 0 }}));
            
            new Chart(ufoCoinCtx, {{
                type: 'scatter',
                data: {{
                    datasets: [{{
                        label: 'Games',
                        data: ufoCoinData,
                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                        pointRadius: 6,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Coins Collected' }} }},
                        y: {{ title: {{ display: true, text: 'UFOs Shot' }} }}
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>
        '''
        
        # Save static HTML
        with open('static/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({
            'status': 'success', 
            'message': 'Static dashboard generated',
            'file': 'static/dashboard.html'
        })
        
    except Exception as e:
        print(f"Error generating dashboard: {e}")
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

# THÊM: Route để xem static dashboard
@app.route('/')
def serve_dashboard():
    return app.send_static_file('dashboard.html')

if __name__ == '__main__':
    init_db()
    print("🚀 Plane Analytics Server starting on http://localhost:5000")
    print("💾 Data will be saved to plane_analytics.db")
    print("📊 New endpoints available:")
    print("   - /api/export-data     - Export raw data to JSON")
    print("   - /api/export-stats    - Export statistics to JSON") 
    print("   - /api/generate-dashboard - Generate static HTML dashboard")
    print("   - /                    - View static dashboard")
    print("⚠️  Press Ctrl+C to stop server - data will be preserved")
    app.run(debug=True, port=5000, host='0.0.0.0')