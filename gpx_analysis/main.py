import xml.etree.ElementTree as ET

# open exeter head file
tree = ET.parse('example_data/Exeter Head.gpx')
root = tree.getroot()

# Define namespaces
ns = {'gpx': 'http://www.topografix.com/GPX/1/1',
      'gpxdata': 'http://www.cluetrust.com/XML/GPXDATA/1/0'}

track_points = []

# Iterate through each track segment and track point
for trkseg in root.findall(".//gpx:trkseg", namespaces=ns):
    for trkpt in trkseg.findall("gpx:trkpt", namespaces=ns):
        lat = trkpt.get('lat')
        lon = trkpt.get('lon')

        cadence_element = trkpt.find("gpx:extensions/gpxdata:cadence", namespaces=ns)
        time = trkpt.find("gpx:time", namespaces=ns).text if trkpt.find("gpx:time", namespaces=ns) is not None else None
        print(time)

        if cadence_element is not None:
            cadence = cadence_element.text
        else:
            cadence_element = trkpt.find("gpx:extensions/gpx:cadence", namespaces=ns)
            cadence = cadence_element.text if cadence_element is not None else None

        track_point = {'lat': float(lat), 'lon': float(lon), 'cadence': cadence}
        track_points.append(track_point)

print(track_points)