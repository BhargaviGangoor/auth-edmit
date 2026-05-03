import requests
import sys

def test():
    try:
        url = "http://localhost:8000/request-otp"
        data = {"email": "bhargavirnsit@gmail.com"}
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
