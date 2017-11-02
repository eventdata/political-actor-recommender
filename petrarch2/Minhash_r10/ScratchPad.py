import requests

print requests.get("http://149.165.168.205:8080/CLIFF-2.3.0/parse/text?q=In%20Syria,%20two%20airstrikes%20west%20of%20Al-Hasakah%20successfully%20struck%20multiple%20ISIL%20buildings,%20including%20an%20air%20observation%20building%20and%20staging%20areas").json()