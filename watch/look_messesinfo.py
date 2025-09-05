import json

import requests


def look_messes_info():
    print("Looking at messages info...")

    # Curl this URL
    response = requests.get(
        "https://sanctifio.com/map/query?maxlat=48.9342285800668&minlat=48.799175059241506"
        "&maxlng=2.39501953125&minlng=2.2717666625976567"
    )

    # print(response.text)
    data = json.loads(response.text)
    for church in data:
        print(church)
        latitude = church["lat"]
        longitude = church["lon"]
        print(church['schedules'])
        print(f"Latitude: {latitude}, Longitude: {longitude}")
        exit()


if __name__ == '__main__':
    look_messes_info()
