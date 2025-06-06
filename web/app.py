from flask import Flask, render_template, jsonify, request
import segno
import io
import base64
import requests
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import os
import glob
from datetime import datetime

app = Flask(__name__)

# Service definitions
SERVICES = [
    {
        'name': 'Navigation',
        'public_hostname': 'nav.irl5795.net',
        'local_ip': '192.168.10.200',
        'local_port': '8080',
        'path': '*'
    },
    {
        'name': 'Router',
        'public_hostname': 'router.irl5795.net',
        'local_ip': '192.168.10.1',
        'local_port': '80',
        'path': '*'
    },
    {
        'name': 'AIS',
        'public_hostname': 'ais.irl5795.net',
        'local_ip': '192.168.10.158',
        'local_port': '80',
        'path': '*'
    },
    {
        'name': 'SignalK',
        'public_hostname': 'signalk.irl5795.net',
        'local_ip': '192.168.10.200',
        'local_port': '3000',
        'path': '*'
    },
    {
        'name': 'InfluxDB',
        'public_hostname': 'influx.irl5795.net',
        'local_ip': '192.168.10.200',
        'local_port': '8086',
        'path': '*'
    },
    {
        'name': 'Dashboard',
        'public_hostname': 'dash.irl5795.net',
        'local_ip': '192.168.10.200',
        'local_port': '8000',
        'path': '*'
    },
    {
        'name': 'SmartSolar',
        'public_hostname': '9572d651c84002ede9cad72ccfda371e.balena-devices.com',
        'local_ip': '192.168.10.162',
        'local_port': '8080',
        'path': '/smartsolar'
    }
]

def generate_qr_code(url):
    """Generate a QR code for the given URL and return as base64 string"""
    # Create QR code with segno
    qr = segno.make(url, error='l')
    
    # Save to BytesIO buffer as PNG
    buffer = io.BytesIO()
    qr.save(buffer, kind='png', scale=10, border=4)
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def check_connectivity(url, timeout=3):
    """Check if a URL is accessible"""
    try:
        response = requests.get(url, timeout=timeout, verify=False)
        return response.status_code < 500
    except:
        return False

def is_local_network(check_request=True):
    """Detect if we're on the local network by checking request headers and local connectivity"""
    # First check if request is coming through Cloudflare (if we have request context)
    if check_request:
        try:
            # Cloudflare adds specific headers to proxied requests
            cf_headers = ['CF-Ray', 'CF-Visitor', 'CF-Connecting-IP', 'CF-IPCountry']
            if any(request.headers.get(header) for header in cf_headers):
                return False
            
            # Also check for X-Forwarded-For which indicates proxy
            if request.headers.get('X-Forwarded-For'):
                return False
        except:
            # No request context available
            pass
    
    try:
        # Try to connect to the router
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('192.168.10.1', 80))
        sock.close()
        return result == 0
    except:
        return False

@app.route('/')
def index():
    """Main page showing all services with QR codes"""
    is_local = is_local_network()
    
    # Prepare service data with URLs and QR codes
    services_data = []
    for service in SERVICES:
        if is_local:
            # Use local IP
            port_suffix = f":{service['local_port']}" if service['local_port'] != '80' else ''
            url = f"http://{service['local_ip']}{port_suffix}"
        else:
            # Use public hostname with HTTPS
            url = f"https://{service['public_hostname']}"
        
        # Add path if specified and not wildcard
        if service.get('path') and service['path'] != '*':
            url += service['path']
        
        service_info = {
            'name': service['name'],
            'url': url,
            'qr_code': generate_qr_code(url),
            'is_local': is_local
        }
        services_data.append(service_info)
    
    return render_template('index.html', services=services_data, is_local=is_local)

@app.route('/api/check-connectivity')
def check_all_connectivity():
    """API endpoint to check connectivity for all services"""
    is_local = is_local_network()
    results = {}
    
    # Always check local connectivity from server side
    # This tells us if the services are actually running
    urls_to_check = []
    for service in SERVICES:
        port_suffix = f":{service['local_port']}" if service['local_port'] != '80' else ''
        local_url = f"http://{service['local_ip']}{port_suffix}"
        # This conditional is redundant since both branches assign the same value
        check_url = local_url
        urls_to_check.append((service['name'], check_url, service))
    
    # Check connectivity in parallel
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_service = {
            executor.submit(check_connectivity, url, timeout=2): (name, url, service) 
            for name, url, service in urls_to_check
        }
        
        for future in as_completed(future_to_service):
            name, local_url, service = future_to_service[future]
            try:
                is_accessible = future.result()
                
                # Determine which URL to return to the client
                if is_local:
                    # User is on local network, return local URL
                    display_url = local_url
                else:
                    # User is remote, return public URL
                    display_url = f"https://{service['public_hostname']}"
                
                # Add path if specified and not wildcard
                if service.get('path') and service['path'] != '*':
                    display_url += service['path']
                
                results[name] = {
                    'url': display_url,
                    'accessible': is_accessible,  # This reflects actual local service status
                    'local_url': local_url + (service['path'] if service.get('path') and service['path'] != '*' else ''),
                    'public_url': f"https://{service['public_hostname']}" + (service['path'] if service.get('path') and service['path'] != '*' else '')
                }
            except Exception as e:
                display_url = local_url if is_local else f"https://{service['public_hostname']}"
                
                # Add path if specified and not wildcard
                if service.get('path') and service['path'] != '*':
                    display_url += service['path']
                
                results[name] = {
                    'url': display_url,
                    'accessible': False,
                    'error': str(e),
                    'local_url': local_url + (service['path'] if service.get('path') and service['path'] != '*' else ''),
                    'public_url': f"https://{service['public_hostname']}" + (service['path'] if service.get('path') and service['path'] != '*' else '')
                }
    
    return jsonify({
        'is_local': is_local,
        'results': results,
        'timestamp': time.time()
    })

# SmartSolar Dashboard Routes
SMARTSOLAR_DATA_DIR = "/data/smartsolar-v1"

def load_device_keys():
    """Load device encryption keys from JSON file."""
    keys_file = os.path.join(SMARTSOLAR_DATA_DIR, "../smartsolar-keys.json")
    if os.path.exists(keys_file):
        try:
            with open(keys_file, 'r') as f:
                data = json.load(f)
                return data.get('devices', {})
        except Exception:
            pass
    return {}

def save_device_keys(keys):
    """Save device encryption keys to JSON file."""
    keys_file = os.path.join(SMARTSOLAR_DATA_DIR, "../smartsolar-keys.json")
    try:
        data = {'devices': keys}
        with open(keys_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

@app.route('/smartsolar')
def smartsolar_dashboard():
    """SmartSolar dashboard page."""
    return render_template('smartsolar.html')

@app.route('/api/smartsolar/data/<date>')
def get_smartsolar_data(date):
    """Get SmartSolar data for a specific date."""
    try:
        ndjson_file = os.path.join(SMARTSOLAR_DATA_DIR, f"data_{date}.ndjson")
        if os.path.exists(ndjson_file):
            data = []
            with open(ndjson_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data.append(json.loads(line))
            return jsonify(data)
        else:
            return jsonify([]), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartsolar/dates')
def get_smartsolar_dates():
    """Get list of dates with available SmartSolar data."""
    try:
        files = glob.glob(os.path.join(SMARTSOLAR_DATA_DIR, "data_*.ndjson"))
        dates = []
        for file in files:
            filename = os.path.basename(file)
            date = filename.replace("data_", "").replace(".ndjson", "")
            dates.append(date)
        dates.sort(reverse=True)
        return jsonify(dates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartsolar/latest')
def get_smartsolar_latest():
    """Get the most recent SmartSolar data entry."""
    try:
        files = glob.glob(os.path.join(SMARTSOLAR_DATA_DIR, "data_*.ndjson"))
        if not files:
            return jsonify({"message": "No data available"}), 404
        
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        # Read the last line of the file
        last_entry = None
        with open(latest_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    last_entry = json.loads(line)
        
        if last_entry:
            return jsonify(last_entry)
        else:
            return jsonify({"message": "No data in file"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartsolar/tail/<int:n>')
def tail_smartsolar_data(n=10):
    """Get the last n SmartSolar data entries across all files."""
    try:
        all_data = []
        files = glob.glob(os.path.join(SMARTSOLAR_DATA_DIR, "data_*.ndjson"))
        files.sort(reverse=True)  # Most recent first
        
        for file in files:
            if len(all_data) >= n:
                break
            
            file_data = []
            with open(file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        file_data.append(json.loads(line))
            
            # Add in reverse order (most recent first)
            all_data.extend(reversed(file_data))
                
        # Return only the requested number of entries
        return jsonify(all_data[:n])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartsolar/keys', methods=['GET'])
def get_smartsolar_keys():
    """Get configured SmartSolar device keys (without exposing the actual keys)."""
    try:
        keys = load_device_keys()
        # Return device addresses with masked keys
        masked_keys = {}
        for address, key in keys.items():
            if key:
                masked_keys[address] = key[:8] + '...' + key[-4:] if len(key) > 12 else '****'
            else:
                masked_keys[address] = ''
        return jsonify(masked_keys)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartsolar/keys', methods=['POST'])
def update_smartsolar_keys():
    """Update SmartSolar device encryption keys."""
    try:
        data = request.get_json()
        if not data or 'device_address' not in data or 'encryption_key' not in data:
            return jsonify({"error": "Missing device_address or encryption_key"}), 400
        
        device_address = data['device_address'].upper()
        encryption_key = data['encryption_key'].strip()
        
        # Validate MAC address format
        if not all(len(part) == 2 for part in device_address.split(':')):
            return jsonify({"error": "Invalid MAC address format"}), 400
        
        # Load existing keys
        keys = load_device_keys()
        
        # Update or add the key
        if encryption_key:
            keys[device_address] = encryption_key
        elif device_address in keys:
            # Empty key means delete
            del keys[device_address]
        
        # Save updated keys
        if save_device_keys(keys):
            return jsonify({"success": True, "message": "Key updated successfully"})
        else:
            return jsonify({"error": "Failed to save keys"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/smartsolar/keys/<device_address>', methods=['DELETE'])
def delete_smartsolar_key(device_address):
    """Delete a SmartSolar device encryption key."""
    try:
        device_address = device_address.upper()
        keys = load_device_keys()
        
        if device_address in keys:
            del keys[device_address]
            if save_device_keys(keys):
                return jsonify({"success": True, "message": "Key deleted successfully"})
            else:
                return jsonify({"error": "Failed to save keys"}), 500
        else:
            return jsonify({"error": "Device not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.after_request
def after_request(response):
    """Add security headers to all responses."""
    # Add Permissions-Policy header without browsing-topics
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    # Add other security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False) 