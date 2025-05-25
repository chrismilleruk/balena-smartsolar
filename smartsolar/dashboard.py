from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta
import glob
from key_manager import load_device_keys, save_device_keys

app = Flask(__name__)

# Constants
VERSION = "v1"
SLUG = "smartsolar"
DATA_DIR = f"/data/{SLUG}-{VERSION}"

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/data/<date>')
def get_data(date):
    """Get data for a specific date."""
    try:
        json_file = os.path.join(DATA_DIR, f"data_{date}.json")
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify([]), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dates')
def get_available_dates():
    """Get list of dates with available data."""
    try:
        files = glob.glob(os.path.join(DATA_DIR, "data_*.json"))
        dates = []
        for file in files:
            filename = os.path.basename(file)
            date = filename.replace("data_", "").replace(".json", "")
            dates.append(date)
        dates.sort(reverse=True)
        return jsonify(dates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/latest')
def get_latest_data():
    """Get the most recent data entry."""
    try:
        files = glob.glob(os.path.join(DATA_DIR, "data_*.json"))
        if not files:
            return jsonify({"message": "No data available"}), 404
        
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        if data:
            return jsonify(data[-1])  # Return last entry
        else:
            return jsonify({"message": "No data in file"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tail/<int:n>')
def tail_data(n=10):
    """Get the last n data entries across all files."""
    try:
        all_data = []
        files = glob.glob(os.path.join(DATA_DIR, "data_*.json"))
        files.sort(reverse=True)  # Most recent first
        
        for file in files:
            if len(all_data) >= n:
                break
            
            with open(file, 'r') as f:
                data = json.load(f)
                all_data.extend(reversed(data))  # Add in reverse order
                
        # Return only the requested number of entries
        return jsonify(all_data[:n])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/keys', methods=['GET'])
def get_keys():
    """Get configured device keys (without exposing the actual keys)."""
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

@app.route('/api/keys', methods=['POST'])
def update_keys():
    """Update device encryption keys."""
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

@app.route('/api/keys/<device_address>', methods=['DELETE'])
def delete_key(device_address):
    """Delete a device encryption key."""
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False) 