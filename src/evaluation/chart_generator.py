import io
import logging

import matplotlib
import numpy as np

matplotlib.use('Agg')  # Headless backend

import matplotlib.pyplot as plt
import networkx as nx

logger = logging.getLogger(__name__)

# Styling
# Remove dark_background so it defaults to light
COLORS = {
    'Critical': '#ff4d4d',
    'High': '#ff9933',
    'Medium': '#ffcc00',
    'Low': '#33cc33',
    'Neutral': '#555555'
}

def _save_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf.read()

def generate_severity_donut(findings: list) -> bytes:
    counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for f in findings:
        sev = f.get('severity', 'Medium').capitalize()
        if sev in counts:
            counts[sev] += 1
            
    labels = []
    sizes = []
    colors = []
    
    for k, v in counts.items():
        if v > 0:
            labels.append(f"{k} ({v})")
            sizes.append(v)
            colors.append(COLORS[k])
            
    fig, ax = plt.subplots(figsize=(6, 6))
    if sum(sizes) == 0:
        ax.text(0.5, 0.5, "0 Vulnerabilities\nDetected", ha='center', va='center', fontsize=20, color=COLORS['Low'])
        ax.axis('off')
    else:
        _wedges, _texts, _autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
        centre_circle = plt.Circle((0, 0), 0.70, fc='#1e1e1e')
        fig.gca().add_artist(centre_circle)
        ax.axis('equal')  
    
    plt.title('Vulnerability Severity Distribution', color='#18181b')
    return _save_to_bytes(fig)

def generate_radar_chart(findings: list) -> bytes | None:
    if not findings:
        return None
        
    categories = ['Tool Disclosure', 'Prompt Leakage', 'Tool Abuse', 'Privilege Escalation']
    weights = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
    scores = {c: 0 for c in categories}
    
    for f in findings:
        cat = f.get('category', 'Tool Abuse')
        sev = f.get('severity', 'Low').capitalize()
        weight = weights.get(sev, 1)
        if cat in scores:
            scores[cat] += weight
        else:
            for c in categories:
                if c.lower() in cat.lower():
                    scores[c] += weight
                    break
    
    max_score = max(max(scores.values()), 10)
    values = [min(scores[c], max_score) for c in categories]
    
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
    plt.xticks(angles[:-1], categories, color='#3f3f46', size=10)
    ax.set_rlabel_position(0)
    plt.yticks([max_score*0.25, max_score*0.5, max_score*0.75, max_score], [], color="#3f3f46", size=7)
    plt.ylim(0, max_score)
    
    ax.plot(angles, values, linewidth=2, linestyle='solid', color='#ff4d4d', marker='o', markersize=6)
    ax.fill(angles, values, '#ff4d4d', alpha=0.25)
    plt.title('Threat Class Exposure Profile', y=1.1, color='#18181b')
    return _save_to_bytes(fig)

def generate_timeline_gantt(timeline_data: list) -> bytes:
    fig, ax = plt.subplots(figsize=(10, 4))
    
    y_labels = []
    y_ticks = []
    
    for i, item in enumerate(timeline_data):
        it = item.get('iteration', i+1)
        cat = item.get('category', 'Unknown')
        verdict = item.get('verdict', 'UNKNOWN').upper()
        
        color = COLORS['Neutral']
        if verdict in ['SUCCESS', 'PARTIAL']:
            color = COLORS['Critical']
        elif verdict == 'FAIL':
            color = COLORS['Low']
            
        ax.barh(i, 1, left=it-1, height=0.5, color=color, edgecolor='#fafafa')
        y_labels.append(f"Iter {it}: {cat[:15]}")
        y_ticks.append(i)
        
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=8, color='#18181b')
    ax.set_xlabel('Iteration', color='#18181b')
    ax.set_title('Attack Timeline progression', color='#18181b')
    ax.invert_yaxis()
    ax.grid(True, axis='x', linestyle='--', alpha=0.3, color='#a1a1aa')
    return _save_to_bytes(fig)

def generate_funnel_chart(timeline_data: list) -> bytes:
    total = len(timeline_data)
    completed = len([t for t in timeline_data if t.get('verdict', '').upper() != 'CANCELLED'])
    partial = len([t for t in timeline_data if t.get('verdict', '').upper() in ['PARTIAL', 'SUCCESS']])
    success = len([t for t in timeline_data if t.get('verdict', '').upper() == 'SUCCESS'])
    
    stages = ['Generated & Attempted', 'Completed (No Error)', 'Partial Exploit', 'Full Compromise']
    values = [total, completed, partial, success]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    y_pos = np.arange(len(stages))
    max_val = max(values) if values else 1
    
    for i, (val, stage) in enumerate(zip(values, stages)):
        left = (max_val - val) / 2
        ax.barh(i, val, left=left, height=0.6, color='#ff9933', alpha=0.8 - (i*0.15))
        ax.text(max_val/2, i, f"{val}", ha='center', va='center', color='#18181b', fontweight='bold', fontsize=12)
        
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages)
    ax.invert_yaxis()
    ax.set_title('Payload Mutation Funnel', color='#18181b')
    ax.axis('off')
    
    for i, stage in enumerate(stages):
        ax.text(-max_val*0.1, i, stage, ha='right', va='center', color='#18181b', fontsize=10)
        
    return _save_to_bytes(fig)

def generate_surface_map(findings: list) -> bytes:
    """
    Generates a conceptual Attack Surface Map showing the testing pathway.
    If findings is empty, lines are green. If vulnerabilities exist, the line is red.
    """
    G = nx.DiGraph()
    
    # Define standard conceptual nodes
    G.add_node("Aegis-Red\nAttacker", pos=(0, 1))
    G.add_node("Target\nAPI/Endpoint", pos=(1, 1))
    G.add_node("Underlying\nAI Model", pos=(2, 1.5))
    G.add_node("Backend\nTools/DB", pos=(2, 0.5))
    
    # Define edge colors based on findings
    is_secure = len(findings) == 0
    edge_color = COLORS['Low'] if is_secure else COLORS['Critical']
    
    # Add edges
    G.add_edge("Aegis-Red\nAttacker", "Target\nAPI/Endpoint", color=edge_color)
    G.add_edge("Target\nAPI/Endpoint", "Underlying\nAI Model", color=edge_color)
    G.add_edge("Target\nAPI/Endpoint", "Backend\nTools/DB", color=edge_color)
    
    pos = nx.get_node_attributes(G, 'pos')
    colors = [G[u][v]['color'] for u,v in G.edges()]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='#e4e4e7', edgecolors='#a1a1aa', ax=ax)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=2, edge_color=colors, arrowsize=20, arrowstyle='-|>', ax=ax)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_color='#18181b', font_weight='bold', ax=ax)
    
    status_text = "SECURE (0 Vulnerabilities)" if is_secure else "COMPROMISED"
    plt.title(f'Attack Surface Map - {status_text}', color='#18181b', y=1.05)
    
    # Increase margins so nodes don't bleed off the edge
    ax.margins(0.30)
    ax.axis('off')
    return _save_to_bytes(fig)

