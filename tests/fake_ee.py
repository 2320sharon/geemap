"""Fake ee module for use with testing."""

import box


class Image:
    def __init__(self, *_, **__):
        pass

    @classmethod
    def constant(self, *_, **__):
        return Image()

    def getMapId(self, *_, **__):
        return box.Box({"tile_fetcher": {"url_format": "url-format"}})

    def updateMask(self, *_, **__):
        return self

    def blend(self, *_, **__):
        return self

    def reduceRegion(self, *_, **__):
        return Dictionary({"B1": 42, "B2": 3.14})


class Dictionary:
    def __init__(self, data):
        self.data = data

    def getInfo(self):
        return self.data


class ReduceRegionResult:
    def getInfo(self):
        return


class Geometry:
    geometry = None

    def __init__(self, *args, **kwargs):
        if len(args):
            self.geometry = args[0]
        if kwargs.get("type"):
            self.geom_type = kwargs.get("type")

    @classmethod
    def Point(self, lat, **__):
        return Geometry(type=String("Point"))

    @classmethod
    def BBox(self, *_, **__):
        return Geometry(type=String("BBox"))

    def type(self, *_, **__):
        return self.geom_type

    def __eq__(self, other: object):
        return self.geometry == getattr(other, 'geometry')


class String:
    def __init__(self, value):
        self.value = value

    def compareTo(self, other_str):
        return self.value == other_str.value


class FeatureCollection:
    features = []

    def __init__(self, *args, **_):
        if len(args):
            self.features = args[0]

    def style(self, *_, **__):
        return Image()

    def first(self, *_, **__):
        return Feature()

    def filterBounds(self, *_, **__):
        return FeatureCollection()

    def __eq__(self, other: object):
        return self.features == getattr(other, 'features')


class Feature:
    feature = None
    properties = None

    def __init__(self, *args, **_):
        if len(args) > 0:
            self.feature = args[0]
        if len(args) >= 2:
            self.properties = args[1]

    def geometry(self, *_, **__):
        return Geometry(type=String("Polygon"))

    def getInfo(self, *_, **__):
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-67.1, 46.2], [-67.3, 46.4], [-67.5, 46.6]],
            },
            "id": "00000000000000000001",
            "properties": {
                "fullname": "",
                "linearid": "110469267091",
                "mtfcc": "S1400",
                "rttyp": "",
            },
        }

    def __eq__(self, other: object):
        featuresEqual = self.feature == getattr(other, 'feature')
        propertiesEqual = self.properties == getattr(other, 'properties')
        return featuresEqual and propertiesEqual


class ImageCollection:
    def __init__(self, *_, **__):
        pass

    def mosaic(self, *_, **__):
        return Image()


class Reducer:
    @classmethod
    def first(cls, *_, **__):
        return Reducer()


class Algorithms:
    @classmethod
    def If(cls, *_, **__):
        return Algorithms()
