import requests
import json
import sys

def main():
    try:
        # Make request to the API
        response = requests.get('http://localhost:8888/api/data')
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            
            # Print available keys
            print("Available keys in response:")
            for key in data.keys():
                if isinstance(data[key], list):
                    print(f"- {key}: {len(data[key])} items")
                else:
                    print(f"- {key}")
            
            # Check specific sections
            sections = ['pods', 'deployments', 'services', 'namespaces', 'nodes']
            for section in sections:
                if section in data:
                    print(f"\n{section.capitalize()} data:")
                    if isinstance(data[section], list) and len(data[section]) > 0:
                        print(f"  Count: {len(data[section])}")
                        print(f"  First item: {json.dumps(data[section][0], indent=2)[:200]}...")
                    else:
                        print(f"  No {section} data or empty list")
                else:
                    print(f"\n{section.capitalize()} data: Not found in response")
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
