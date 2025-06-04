import requests; response = requests.get("http://localhost:8888/api/data"); print(f"Status: {response.status_code}"); print(response.text[:500] if response.status_code == 200 else response.text)
