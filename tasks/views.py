import os
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.conf import settings

def run_simulation():
    MAX_REQUESTS_PER_MIN = int(os.environ.get('MAX_REQUESTS_PER_MIN', 200))
    MAX_CONCURRENT_CONNECTIONS = int(os.environ.get('MAX_CONCURRENT_CONNECTIONS', 1000))

    attack_stats = []
    simulation_minutes = 30
    current_connections = 0
    active_connections_list = []

    for minute in range(1, simulation_minutes + 1):
        ip_requests_this_minute = {}

        if minute % 5 == 0:
            requests_this_minute = random.randint(1500, 3000)
        else:
            requests_this_minute = random.randint(500, 1500)

        for _ in range(requests_this_minute):
            ip = f"192.168.1.{random.randint(1, 100)}"

            ip_requests_this_minute[ip] = ip_requests_this_minute.get(ip, 0) + 1
            if ip_requests_this_minute[ip] > MAX_REQUESTS_PER_MIN:
                attack_stats.append([minute, ip, f"Превышен лимит {MAX_REQUESTS_PER_MIN} запросов/мин"])
                continue

            if current_connections >= MAX_CONCURRENT_CONNECTIONS:
                attack_stats.append([minute, ip, f"Превышение одновременных соединений ({MAX_CONCURRENT_CONNECTIONS})"])
                continue

            current_connections += 1
            active_connections_list.append({
                'ip': ip,
                'start_minute': minute,
                'duration': random.randint(1, 10)
            })

        new_active_connections = []
        for conn in active_connections_list:
            if minute - conn['start_minute'] < conn['duration']:
                new_active_connections.append(conn)
            else:
                current_connections -= 1
        active_connections_list = new_active_connections

        if random.random() < 0.2 and current_connections > 0:
            to_close = random.randint(1, min(5, current_connections))
            for _ in range(to_close):
                if active_connections_list:
                    active_connections_list.pop()
                    current_connections -= 1

    reason_count = {}
    minute_counts = {}
    for row in attack_stats:
        reason = row[2]
        reason_count[reason] = reason_count.get(reason, 0) + 1
        m = row[0]
        minute_counts[m] = minute_counts.get(m, 0) + 1

    minutes = sorted(minute_counts.keys())
    counts = [minute_counts[m] for m in minutes]

    chart_paths = generate_charts(minutes, counts, reason_count)

    return {
        'attack_stats': attack_stats,
        'total_attacks': len(attack_stats),
        'reason_count': reason_count,
        'minute_counts': minute_counts,
        'chart_paths': chart_paths,
        'limits': {
            'max_requests': MAX_REQUESTS_PER_MIN,
            'max_connections': MAX_CONCURRENT_CONNECTIONS
        }
    }

def generate_charts(minutes, counts, reason_counts):
    import os
    static_dir = os.path.join(settings.BASE_DIR, 'tasks', 'static', 'tasks')
    os.makedirs(static_dir, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.bar(minutes, counts, color='red', alpha=0.7, edgecolor='darkred')
    plt.title('Количество DoS-атак по минутам')
    plt.xlabel('Минута симуляции')
    plt.ylabel('Количество атак')
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, max(minutes)+1, 5))
    plt.tight_layout()
    bar_path = os.path.join(static_dir, 'attacks_bar.png')
    plt.savefig(bar_path, dpi=100)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(minutes, counts, marker='o', linestyle='-', color='blue')
    plt.title('Тренд атак по минутам')
    plt.xlabel('Минута симуляции')
    plt.ylabel('Количество атак')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    line_path = os.path.join(static_dir, 'attacks_line.png')
    plt.savefig(line_path, dpi=100)
    plt.close()

    plt.figure(figsize=(8, 8))
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    wedges, texts, autotexts = plt.pie(
        reason_counts.values(),
        labels=reason_counts.keys(),
        autopct='%1.1f%%',
        shadow=True,
        startangle=90,
        colors=colors[:len(reason_counts)]
    )
    plt.setp(autotexts, size=10, weight="bold")
    plt.setp(texts, size=11)
    plt.title('Распределение причин DoS-атак', pad=20)
    plt.tight_layout()
    pie_path = os.path.join(static_dir, 'attacks_pie.png')
    plt.savefig(pie_path, dpi=100, bbox_inches='tight')
    plt.close()

    return {
        'bar': 'tasks/attacks_bar.png',
        'line': 'tasks/attacks_line.png',
        'pie': 'tasks/attacks_pie.png',
    }

def index(request):
    data = run_simulation()
    context = {
        'attack_stats': data['attack_stats'],
        'total_attacks': data['total_attacks'],
        'reason_count': data['reason_count'],
        'limits': data['limits'],
        'chart_paths': data['chart_paths'],
    }
    return render(request, 'index.html', context)