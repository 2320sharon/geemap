#!/usr/bin/env python

"""Tests for `map_widgets` module."""
import unittest
from unittest.mock import patch, MagicMock, Mock, ANY

import ipytree
import ipywidgets
import ee

from geemap import map_widgets
from tests import fake_ee, fake_map


def _query_widget(node, type_matcher, matcher):
    """Recursively searches the widget hierarchy for the widget."""
    if hasattr(node, "layout"):
        if hasattr(node.layout, "display"):
            if node.layout.display == "none":
                return None
    if hasattr(node, "style"):
        if hasattr(node.style, "display"):
            if node.style.display == "none":
                return None

    children = getattr(node, "children", getattr(node, "nodes", None))
    if children is not None:
        for child in children:
            result = _query_widget(child, type_matcher, matcher)
            if result:
                return result
    if isinstance(node, type_matcher) and matcher(node):
        return node
    return None


class TestColorbar(unittest.TestCase):
    """Tests for the Colorbar class in the `map_widgets` module."""

    TEST_COLORS = ["blue", "red", "green"]
    TEST_COLORS_HEX = ["#0000ff", "#ff0000", "#008000"]

    def setUp(self):
        self.fig_mock = MagicMock()
        self.ax_mock = MagicMock()
        self.subplots_mock = patch("matplotlib.pyplot.subplots").start()
        self.subplots_mock.return_value = (self.fig_mock, self.ax_mock)

        self.colorbar_base_mock = MagicMock()
        self.colorbar_base_class_mock = patch(
            "matplotlib.colorbar.ColorbarBase"
        ).start()
        self.colorbar_base_class_mock.return_value = self.colorbar_base_mock

        self.normalize_mock = MagicMock()
        self.normalize_class_mock = patch("matplotlib.colors.Normalize").start()
        self.normalize_class_mock.return_value = self.normalize_mock

        self.boundary_norm_mock = MagicMock()
        self.boundary_norm_class_mock = patch("matplotlib.colors.BoundaryNorm").start()
        self.boundary_norm_class_mock.return_value = self.boundary_norm_mock

        self.listed_colormap = MagicMock()
        self.listed_colormap_class_mock = patch(
            "matplotlib.colors.ListedColormap"
        ).start()
        self.listed_colormap_class_mock.return_value = self.listed_colormap

        self.linear_segmented_colormap_mock = MagicMock()
        self.colormap_from_list_mock = patch(
            "matplotlib.colors.LinearSegmentedColormap.from_list"
        ).start()
        self.colormap_from_list_mock.return_value = self.linear_segmented_colormap_mock

        check_cmap_mock = patch("geemap.common.check_cmap").start()
        check_cmap_mock.side_effect = lambda x: x

        self.cmap_mock = MagicMock()
        self.get_cmap_mock = patch("matplotlib.pyplot.get_cmap").start()
        self.get_cmap_mock.return_value = self.cmap_mock

    def tearDown(self):
        patch.stopall()

    def test_colorbar_no_args(self):
        map_widgets.Colorbar()
        self.normalize_class_mock.assert_called_with(vmin=0, vmax=1)
        self.get_cmap_mock.assert_called_with("gray")
        self.subplots_mock.assert_called_with(figsize=(3.0, 0.3))
        self.ax_mock.set_axis_off.assert_not_called()
        self.ax_mock.tick_params.assert_called_with(labelsize=9)
        self.fig_mock.patch.set_alpha.assert_not_called()
        self.colorbar_base_mock.set_label.assert_not_called()
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.normalize_mock,
            alpha=1,
            cmap=self.cmap_mock,
            orientation="horizontal",
        )

    def test_colorbar_orientation_horizontal(self):
        map_widgets.Colorbar(orientation="horizontal")
        self.subplots_mock.assert_called_with(figsize=(3.0, 0.3))

    def test_colorbar_orientation_vertical(self):
        map_widgets.Colorbar(orientation="vertical")
        self.subplots_mock.assert_called_with(figsize=(0.3, 3.0))

    def test_colorbar_orientation_override(self):
        map_widgets.Colorbar(orientation="horizontal", width=2.0)
        self.subplots_mock.assert_called_with(figsize=(2.0, 0.3))

    def test_colorbar_invalid_orientation(self):
        with self.assertRaisesRegex(ValueError, "orientation must be one of"):
            map_widgets.Colorbar(orientation="not an orientation")

    def test_colorbar_label(self):
        map_widgets.Colorbar(label="Colorbar lbl", font_size=42)
        self.colorbar_base_mock.set_label.assert_called_with(
            "Colorbar lbl", fontsize=42
        )

    def test_colorbar_label_as_bands(self):
        map_widgets.Colorbar(vis_params={"bands": "b1"})
        self.colorbar_base_mock.set_label.assert_called_with("b1", fontsize=9)

    def test_colorbar_label_with_caption(self):
        map_widgets.Colorbar(caption="Colorbar caption")
        self.colorbar_base_mock.set_label.assert_called_with(
            "Colorbar caption", fontsize=9
        )

    def test_colorbar_label_precedence(self):
        map_widgets.Colorbar(
            label="Colorbar lbl",
            vis_params={"bands": "b1"},
            caption="Colorbar caption",
            font_size=21,
        )
        self.colorbar_base_mock.set_label.assert_called_with(
            "Colorbar lbl", fontsize=21
        )

    def test_colorbar_axis(self):
        map_widgets.Colorbar(axis_off=True, font_size=24)
        self.ax_mock.set_axis_off.assert_called()
        self.ax_mock.tick_params.assert_called_with(labelsize=24)

    def test_colorbar_transparent_bg(self):
        map_widgets.Colorbar(transparent_bg=True)
        self.fig_mock.patch.set_alpha.assert_called_with(0.0)

    def test_colorbar_vis_params_palette(self):
        map_widgets.Colorbar(
            vis_params={
                "palette": self.TEST_COLORS,
                "min": 11,
                "max": 21,
                "opacity": 0.2,
            }
        )
        self.normalize_class_mock.assert_called_with(vmin=11, vmax=21)
        self.colormap_from_list_mock.assert_called_with(
            "custom", self.TEST_COLORS_HEX, N=256
        )
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.normalize_mock,
            alpha=0.2,
            cmap=self.linear_segmented_colormap_mock,
            orientation="horizontal",
        )

    def test_colorbar_vis_params_discrete_palette(self):
        map_widgets.Colorbar(
            vis_params={"palette": self.TEST_COLORS, "min": -1}, discrete=True
        )
        self.boundary_norm_class_mock.assert_called_with([-1], ANY)
        self.listed_colormap_class_mock.assert_called_with(self.TEST_COLORS_HEX)
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.boundary_norm_mock,
            alpha=1,
            cmap=self.listed_colormap,
            orientation="horizontal",
        )

    def test_colorbar_vis_params_palette_as_list(self):
        map_widgets.Colorbar(vis_params=self.TEST_COLORS, discrete=True)
        self.boundary_norm_class_mock.assert_called_with([0], ANY)
        self.listed_colormap_class_mock.assert_called_with(self.TEST_COLORS_HEX)
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.boundary_norm_mock,
            alpha=1,
            cmap=self.listed_colormap,
            orientation="horizontal",
        )

    def test_colorbar_kwargs_colors(self):
        map_widgets.Colorbar(colors=self.TEST_COLORS, discrete=True)
        self.boundary_norm_class_mock.assert_called_with([0], ANY)
        self.listed_colormap_class_mock.assert_called_with(self.TEST_COLORS_HEX)
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.boundary_norm_mock,
            alpha=1,
            cmap=self.listed_colormap,
            orientation="horizontal",
            colors=self.TEST_COLORS,
        )

    def test_colorbar_min_max(self):
        map_widgets.Colorbar(
            vis_params={"palette": self.TEST_COLORS, "min": -1.5}, vmin=-1, vmax=2
        )
        self.normalize_class_mock.assert_called_with(vmin=-1.5, vmax=1)

    def test_colorbar_invalid_min(self):
        with self.assertRaisesRegex(TypeError, "min value must be scalar type"):
            map_widgets.Colorbar(vis_params={"min": "invalid_min"})

    def test_colorbar_invalid_max(self):
        with self.assertRaisesRegex(TypeError, "max value must be scalar type"):
            map_widgets.Colorbar(vis_params={"max": "invalid_max"})

    def test_colorbar_opacity(self):
        map_widgets.Colorbar(vis_params={"opacity": 0.5}, colors=self.TEST_COLORS)
        self.colorbar_base_class_mock.assert_called_with(
            ANY, norm=ANY, alpha=0.5, cmap=ANY, orientation=ANY, colors=ANY
        )

    def test_colorbar_alpha(self):
        map_widgets.Colorbar(alpha=0.5, colors=self.TEST_COLORS)
        self.colorbar_base_class_mock.assert_called_with(
            ANY, norm=ANY, alpha=0.5, cmap=ANY, orientation=ANY, colors=ANY
        )

    def test_colorbar_invalid_alpha(self):
        with self.assertRaisesRegex(
            TypeError, "opacity or alpha value must be type scalar"
        ):
            map_widgets.Colorbar(alpha="invalid_alpha", colors=self.TEST_COLORS)

    def test_colorbar_vis_params_throws_for_not_dict(self):
        with self.assertRaisesRegex(TypeError, "vis_params must be a dictionary"):
            map_widgets.Colorbar(vis_params="NOT a dict")


@patch.object(ee, "Algorithms", fake_ee.Algorithms)
@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Feature", fake_ee.Feature)
@patch.object(ee, "Geometry", fake_ee.Geometry)
@patch.object(ee, "Image", fake_ee.Image)
@patch.object(ee, "String", fake_ee.String)
class TestInspector(unittest.TestCase):
    """Tests for the Inspector class in the `map_widgets` module."""

    def setUp(self):
        # ee.Reducer is dynamically initialized (can't use @patch.object).
        ee.Reducer = fake_ee.Reducer

        self.map_fake = fake_map.FakeMap()
        self.inspector = map_widgets.Inspector(self.map_fake)

    def tearDown(self):
        pass

    def _query_checkbox(self, description):
        return _query_widget(
            self.inspector, ipywidgets.Checkbox, lambda c: c.description == description
        )

    def _query_node(self, root, name):
        return _query_widget(root, ipytree.Node, lambda c: c.name == name)

    @property
    def _point_checkbox(self):
        return self._query_checkbox("Point")

    @property
    def _pixels_checkbox(self):
        return self._query_checkbox("Pixels")

    @property
    def _objects_checkbox(self):
        return self._query_checkbox("Objects")

    @property
    def _inspector_toggle(self):
        return _query_widget(
            self.inspector, ipywidgets.ToggleButton, lambda c: c.tooltip == "Inspector"
        )

    @property
    def _close_toggle(self):
        return _query_widget(
            self.inspector,
            ipywidgets.ToggleButton,
            lambda c: c.tooltip == "Close the tool",
        )

    def test_inspector_no_map(self):
        """Tests that a valid map must be passed in."""
        with self.assertRaisesRegex(ValueError, "valid map"):
            map_widgets.Inspector(None)

    def test_inspector(self):
        """Tests that the inspector's initial UI is set up properly."""
        self.assertEqual(self.map_fake.cursor_style, "crosshair")
        self.assertFalse(self._point_checkbox.value)
        self.assertTrue(self._pixels_checkbox.value)
        self.assertFalse(self._objects_checkbox.value)
        self.assertTrue(self._inspector_toggle.value)
        self.assertIsNotNone(self._close_toggle)

    def test_inspector_toggle(self):
        """Tests that toggling the inspector button hides/shows the inspector."""
        self._point_checkbox.value = True
        self._pixels_checkbox.value = False
        self._objects_checkbox.value = True

        self._inspector_toggle.value = False

        self.assertEqual(self.map_fake.cursor_style, "default")
        self.assertIsNotNone(self._inspector_toggle)
        self.assertIsNone(self._point_checkbox)
        self.assertIsNone(self._pixels_checkbox)
        self.assertIsNone(self._objects_checkbox)
        self.assertIsNone(self._close_toggle)

        self._inspector_toggle.value = True

        self.assertEqual(self.map_fake.cursor_style, "crosshair")
        self.assertIsNotNone(self._inspector_toggle)
        self.assertTrue(self._point_checkbox.value)
        self.assertFalse(self._pixels_checkbox.value)
        self.assertTrue(self._objects_checkbox.value)
        self.assertIsNotNone(self._close_toggle.value)

    def test_inspector_close(self):
        """Tests that toggling the close button fires the close event."""
        on_close_mock = Mock()
        self.inspector.on_close = on_close_mock
        self._close_toggle.value = True

        on_close_mock.assert_called_once()
        self.assertEqual(self.map_fake.cursor_style, "default")
        self.assertSetEqual(self.map_fake.interaction_handlers, set())

    def test_map_empty_click(self):
        """Tests that clicking the map triggers inspection."""
        self.map_fake.click((1, 2), "click")

        self.assertEqual(self.map_fake.cursor_style, "crosshair")
        point_root = self._query_node(self.inspector, "Point (2.00, 1.00) at 1024m/px")
        self.assertIsNotNone(point_root)
        self.assertIsNotNone(self._query_node(point_root, "Longitude: 2"))
        self.assertIsNotNone(self._query_node(point_root, "Latitude: 1"))
        self.assertIsNotNone(self._query_node(point_root, "Zoom Level: 7"))
        self.assertIsNotNone(self._query_node(point_root, "Scale (approx. m/px): 1024"))
        self.assertIsNone(self._query_node(self.inspector, "Pixels"))
        self.assertIsNone(self._query_node(self.inspector, "Objects"))

    def test_map_click(self):
        """Tests that clicking the map triggers inspection."""
        self.map_fake.ee_layers = {
            "test-map-1": {
                "ee_object": ee.Image(1),
                "ee_layer": fake_map.FakeEeTileLayer(visible=True),
                "vis_params": None,
            },
            "test-map-2": {
                "ee_object": ee.Image(2),
                "ee_layer": fake_map.FakeEeTileLayer(visible=False),
                "vis_params": None,
            },
            "test-map-3": {
                "ee_object": ee.FeatureCollection([]),
                "ee_layer": fake_map.FakeEeTileLayer(visible=True),
                "vis_params": None,
            },
        }
        self.map_fake.click((1, 2), "click")

        self.assertEqual(self.map_fake.cursor_style, "crosshair")
        self.assertIsNotNone(
            self._query_node(self.inspector, "Point (2.00, 1.00) at 1024m/px")
        )

        pixels_root = self._query_node(self.inspector, "Pixels")
        self.assertIsNotNone(pixels_root)
        layer_1_root = self._query_node(pixels_root, "test-map-1: Image (2 bands)")
        self.assertIsNotNone(layer_1_root)
        self.assertIsNotNone(self._query_node(layer_1_root, "B1: 42"))
        self.assertIsNotNone(self._query_node(layer_1_root, "B2: 3.14"))
        self.assertIsNone(self._query_node(pixels_root, "test-map-2: Image (2 bands)"))

        objects_root = self._query_node(self.inspector, "Objects")
        self.assertIsNotNone(objects_root)
        layer_3_root = self._query_node(objects_root, "test-map-3: Feature ")
        self.assertIsNotNone(layer_3_root)
        self.assertIsNotNone(self._query_node(layer_3_root, "type: Feature"))
        self.assertIsNotNone(self._query_node(layer_3_root, "id: 00000000000000000001"))
        self.assertIsNotNone(self._query_node(layer_3_root, "fullname: "))
        self.assertIsNotNone(self._query_node(layer_3_root, "linearid: 110469267091"))
        self.assertIsNotNone(self._query_node(layer_3_root, "mtfcc: S1400"))
        self.assertIsNotNone(self._query_node(layer_3_root, "rttyp: "))

    def test_map_click_twice(self):
        """Tests that clicking the map a second time removes the original output."""
        self.map_fake.ee_layers = {
            "test-map-1": {
                "ee_object": ee.Image(1),
                "ee_layer": fake_map.FakeEeTileLayer(visible=True),
                "vis_params": None,
            },
        }
        self.map_fake.scale = 32
        self.map_fake.click((1, 2), "click")
        self.map_fake.click((4, 1), "click")

        self.assertIsNotNone(
            self._query_node(self.inspector, "Point (1.00, 4.00) at 32m/px")
        )
        self.assertIsNone(
            self._query_node(self.inspector, "Point (2.00, 1.00) at 1024m/px")
        )


class TestLayerManager(unittest.TestCase):
    """Tests for the LayerManager class in the `map_widgets` module."""

    @property
    def collapse_button(self):
        """Returns the collapse button on layer_manager or None."""
        return _query_widget(
            self.layer_manager,
            ipywidgets.ToggleButton,
            lambda c: c.tooltip == "Layer Manager",
        )

    @property
    def close_button(self):
        """Returns the close button on layer_manager or None."""
        return _query_widget(
            self.layer_manager,
            ipywidgets.Button,
            lambda c: c.tooltip == "Close the tool",
        )

    @property
    def toggle_all_checkbox(self):
        """Returns the toggle all checkbox on layer_manager or None."""
        return _query_widget(
            self.layer_manager,
            ipywidgets.Checkbox,
            lambda c: c.description == "All layers on/off",
        )

    @property
    def layer_rows(self):
        """Returns the ipywidgets rows on layer_manager."""
        return _query_widget(
            self.layer_manager, ipywidgets.VBox, lambda c: True
        ).children[1:]

    def _query_checkbox_on_row(self, row, name):
        return _query_widget(row, ipywidgets.Checkbox, lambda c: c.description == name)

    def _query_slider_on_row(self, row):
        return _query_widget(row, ipywidgets.FloatSlider, lambda _: True)

    def _query_button_on_row(self, row):
        return _query_widget(row, ipywidgets.Button, lambda _: True)

    def _validate_row(self, row, name, checked, opacity):
        self.assertEqual(self._query_checkbox_on_row(row, name).value, checked)
        self.assertEqual(self._query_slider_on_row(row).value, opacity)
        self.assertIsNotNone(self._query_button_on_row(row))

    def setUp(self):
        self.fake_map = fake_map.FakeMap()
        self.fake_map.layers = [
            fake_map.FakeTileLayer(name=None),  # Basemap
            fake_map.FakeTileLayer(
                name="GMaps", visible=False, opacity=0.5
            ),  # Extra basemap
            fake_map.FakeEeTileLayer(name="test-layer", visible=True, opacity=0.8),
            fake_map.FakeGeoJSONLayer(
                name="test-geojson-layer",
                visible=False,
                style={"some-style": "red", "opacity": 0.3, "fillOpacity": 0.2},
            ),
        ]
        self.fake_map.ee_layers = {
            "test-layer": {
                "ee_object": None,
                "ee_layer": self.fake_map.layers[2],
                "vis_params": None,
            },
        }
        self.fake_map.geojson_layers = [self.fake_map.layers[3]]

        self.layer_manager = map_widgets.LayerManager(self.fake_map)

    def test_layer_manager_no_map(self):
        """Tests that a valid map must be passed in."""
        with self.assertRaisesRegex(ValueError, "valid map"):
            map_widgets.LayerManager(None)

    def test_layer_manager(self):
        self.assertIsNotNone(self.collapse_button)
        self.assertIsNotNone(self.close_button)
        self.assertIsNotNone(self.toggle_all_checkbox)

        # Verify computed properties are correct.
        self.assertFalse(self.layer_manager.collapsed)
        self.assertFalse(self.layer_manager.header_hidden)
        self.assertFalse(self.layer_manager.close_button_hidden)

        self.assertEqual(len(self.layer_rows), 3)
        self._validate_row(self.layer_rows[0], "GMaps", False, 0.5)
        self._validate_row(self.layer_rows[1], "test-layer", True, 0.8)
        self._validate_row(self.layer_rows[2], "test-geojson-layer", False, 0.3)

    def test_layer_manager_toggle_all_visibility(self):
        """Tests that the toggle all checkbox changes visibilities."""
        # True then False because the event doesn't fire if the value doesn't change.
        self.toggle_all_checkbox.value = True
        self.toggle_all_checkbox.value = False

        for layer in self.fake_map.layers:
            self.assertEqual(
                layer.visible, False, f"{layer.name} should not be visible"
            )

        self.toggle_all_checkbox.value = True

        for layer in self.fake_map.layers:
            self.assertEqual(layer.visible, True, f"{layer.name} should be visible")

    def test_layer_manager_opacity_changed(self):
        """Tests that the opacity slider changes opacities."""
        ee_layer = self.layer_rows[1]
        ee_layer_slider = self._query_slider_on_row(ee_layer)
        ee_layer_slider.value = 0.01
        self.assertEqual(self.fake_map.layers[2].opacity, 0.01)

        geojson_layer = self.layer_rows[2]
        geojson_layer_slider = self._query_slider_on_row(geojson_layer)
        geojson_layer_slider.value = 0.02
        self.assertEqual(
            self.fake_map.layers[3].style,
            {"some-style": "red", "opacity": 0.02, "fillOpacity": 0.02},
        )

    def test_layer_manager_click_settings(self):
        """Tests that the settings button fires an event."""
        on_open_vis_mock = Mock()
        self.layer_manager.on_open_vis = on_open_vis_mock
        ee_layer_button = self._query_button_on_row(self.layer_rows[1])

        ee_layer_button.click()

        on_open_vis_mock.assert_called_once()

    def test_layer_manager_click_close(self):
        """Tests that the close button fires an event."""
        on_close_mock = Mock()
        self.layer_manager.on_close = on_close_mock

        self.close_button.click()

        on_close_mock.assert_called_once()

    def test_layer_manager_refresh_layers(self):
        """Tests that refresh_layers refreshes the layers."""
        self.fake_map.layers = []
        self.layer_manager.refresh_layers()

        self.assertEqual(len(self.layer_rows), 0)

    def test_layer_manager_collapsed(self):
        """Tests that setting the collapsed property collapses the widget."""
        self.layer_manager.collapsed = True

        self.assertIsNotNone(self.collapse_button)
        self.assertIsNone(self.close_button)
        self.assertIsNone(self.toggle_all_checkbox)
        self.assertEqual(len(self.layer_rows), 0)

        self.layer_manager.collapsed = False

        self.assertIsNotNone(self.collapse_button)
        self.assertIsNotNone(self.close_button)
        self.assertIsNotNone(self.toggle_all_checkbox)
        self.assertEqual(len(self.layer_rows), 3)

    def test_layer_manager_header_hidden(self):
        """Tests that setting the header_hidden property hides the header."""
        self.layer_manager.header_hidden = True

        self.assertIsNone(self.collapse_button)
        self.assertIsNone(self.close_button)
        self.assertIsNotNone(self.toggle_all_checkbox)

        self.layer_manager.header_hidden = False

        self.assertIsNotNone(self.collapse_button)
        self.assertIsNotNone(self.close_button)
        self.assertIsNotNone(self.toggle_all_checkbox)

    def test_layer_manager_close_button_hidden(self):
        """Tests that setting the close_button_hidden property hides the close button."""
        self.layer_manager.close_button_hidden = True

        self.assertIsNotNone(self.collapse_button)
        self.assertIsNone(self.close_button)
        self.assertIsNotNone(self.toggle_all_checkbox)

        self.layer_manager.close_button_hidden = False

        self.assertIsNotNone(self.collapse_button)
        self.assertIsNotNone(self.close_button)
        self.assertIsNotNone(self.toggle_all_checkbox)


@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Feature", fake_ee.Feature)
@patch.object(ee, "Geometry", fake_ee.Geometry)
@patch.object(ee, "Image", fake_ee.Image)
class TestAbstractDrawControl(unittest.TestCase):
    """Tests for the draw control interface in the `map_widgets` module."""
    geo_json = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [0, 1],
                        [0, -1],
                        [1, -1],
                        [1, 1],
                        [0, 1],
                    ]
                ],
            },
            "properties": {
                "name": "Null Island"
            }
        }
    geo_json2 = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [0, 2],
                        [0, -2],
                        [2, -2],
                        [2, 2],
                        [0, 2],
                    ]
                ],
            },
            "properties": {
                "name": "Null Island 2x"
            }
        }

    def setUp(self):
        map = fake_map.FakeMap()
        self.draw_control = TestAbstractDrawControl.TestDrawControl(map)

    def tearDown(self):
        pass

    def test_initialization(self):
        # Initialized is set by the `_bind_draw_controls` method.
        self.assertTrue(self.draw_control.initialized)
        self.assertIsNone(self.draw_control.layer)
        self.assertEquals(self.draw_control.geometries, [])
        self.assertEquals(self.draw_control.properties, [])
        self.assertIsNone(self.draw_control.last_geometry)
        self.assertIsNone(self.draw_control.last_draw_action)
        self.assertEquals(self.draw_control.features, [])
        self.assertEquals(self.draw_control.collection, fake_ee.FeatureCollection([]))
        self.assertIsNone(self.draw_control.last_feature)
        self.assertEquals(self.draw_control.count, 0)

    def test_handles_creation(self):
        self.draw_control.create(self.geo_json)
        self.assertEquals(
            self.draw_control.geometries,
            [fake_ee.Geometry(self.geo_json["geometry"])],
        )

    def test_handles_deletion(self):
        self.draw_control.create(self.geo_json)
        self.assertEquals(len(self.draw_control.geometries), 1)
        self.draw_control.delete(0)
        self.assertEquals(len(self.draw_control.geometries), 0)

    def test_handles_edit(self):
        self.draw_control.create(self.geo_json)
        self.assertEquals(len(self.draw_control.geometries), 1)

        self.draw_control.edit(0, self.geo_json2)
        self.assertEquals(len(self.draw_control.geometries), 1)
        self.assertEquals(
            self.draw_control.geometries[0],
            fake_ee.Geometry(self.geo_json2["geometry"]),
        )

    def test_property_accessors(self):
        self.draw_control.create(self.geo_json)

        # Test layer accessor.
        self.assertIsNotNone(self.draw_control.layer)
        # Test geometries accessor.
        geometry = fake_ee.Geometry(self.geo_json["geometry"])
        self.assertEquals(len(self.draw_control.geometries), 1)
        self.assertEquals(self.draw_control.geometries, [geometry])
        # Test properties accessor.
        self.assertEquals(self.draw_control.properties, [None])
        # Test last_geometry accessor.
        self.assertEquals(self.draw_control.last_geometry, geometry)
        # Test last_draw_action accessor.
        self.assertEquals(
            self.draw_control.last_draw_action,
            map_widgets.DrawActions.CREATED
        )
        # Test features accessor.
        feature = fake_ee.Feature(geometry, None)
        self.assertEquals(self.draw_control.features, [feature])
        # Test collection accessor.
        self.assertEquals(
            self.draw_control.collection,
            fake_ee.FeatureCollection([feature])
        )
        # Test last_feature accessor.
        self.assertEquals(self.draw_control.last_feature, feature)
        # Test count accessor.
        self.assertEquals(self.draw_control.count, 1)

    def test_feature_property_access(self):
        self.draw_control.create(self.geo_json)
        geometry = self.draw_control.geometries[0]
        self.assertIsNone(
            self.draw_control.get_geometry_properties(geometry)
        )
        self.assertEquals(
            self.draw_control.features,
            [fake_ee.Feature(geometry, None)]
        )
        self.draw_control.set_geometry_properties(geometry, {"test": 1})
        self.assertEquals(
            self.draw_control.features,
            [fake_ee.Feature(geometry, {"test": 1})]
        )

    def test_reset(self):
        self.draw_control.create(self.geo_json)
        self.assertEquals(len(self.draw_control.geometries), 1)

        # When clear_draw_control is True, deletes the underlying geometries.
        self.draw_control.reset(clear_draw_control=True)
        self.assertEquals(len(self.draw_control.geometries), 0)
        self.assertEquals(len(self.draw_control.geo_jsons), 0)

        self.draw_control.create(self.geo_json)
        self.assertEquals(len(self.draw_control.geometries), 1)
        # When clear_draw_control is False, does not delete the underlying
        # geometries.
        self.draw_control.reset(clear_draw_control=False)
        self.assertEquals(len(self.draw_control.geometries), 0)
        self.assertEquals(len(self.draw_control.geo_jsons), 1)

    def test_remove_geometry(self):
        self.draw_control.create(self.geo_json)
        self.draw_control.create(self.geo_json2)
        geometry1 = self.draw_control.geometries[0]
        geometry2 = self.draw_control.geometries[1]
        self.assertEquals(len(self.draw_control.geometries), 2)
        self.assertEquals(len(self.draw_control.properties), 2)
        self.assertEquals(
            self.draw_control.last_draw_action,
            map_widgets.DrawActions.CREATED
        )
        self.assertEquals(self.draw_control.last_geometry, geometry2)

        # When there are two geometries and the removed geometry is the last
        # one, then we treat it like an undo.
        self.draw_control.remove_geometry(geometry2)
        self.assertEquals(len(self.draw_control.geometries), 1)
        self.assertEquals(len(self.draw_control.properties), 1)
        self.assertEquals(
            self.draw_control.last_draw_action,
            map_widgets.DrawActions.REMOVED_LAST
        )
        self.assertEquals(self.draw_control.last_geometry, geometry1)

        # When there's only one geometry, last_geometry is the removed geometry.
        self.draw_control.remove_geometry(geometry1)
        self.assertEquals(len(self.draw_control.geometries), 0)
        self.assertEquals(len(self.draw_control.properties), 0)
        self.assertEquals(
            self.draw_control.last_draw_action,
            map_widgets.DrawActions.REMOVED_LAST
        )
        self.assertEquals(self.draw_control.last_geometry, geometry1)

        # When there are two geometries and the removed geometry is the first
        # one, then treat it like a normal delete.
        self.draw_control.create(self.geo_json)
        self.draw_control.create(self.geo_json2)
        geometry1 = self.draw_control.geometries[0]
        geometry2 = self.draw_control.geometries[1]
        self.draw_control.remove_geometry(geometry1)
        self.assertEquals(len(self.draw_control.geometries), 1)
        self.assertEquals(len(self.draw_control.properties), 1)
        self.assertEquals(
            self.draw_control.last_draw_action,
            map_widgets.DrawActions.DELETED
        )
        self.assertEquals(self.draw_control.last_geometry, geometry1)

    class TestDrawControl(map_widgets.AbstractDrawControl):
        """Implements an AbstractDrawControl for tests."""
        geo_jsons = []
        initialized = False

        def __init__(self, host_map, **kwargs):
            """Initialize the test draw control.

            Args:
                host_map (geemap.Map): The geemap.Map object
            """
            super(TestAbstractDrawControl.TestDrawControl, self).__init__(
                host_map=host_map,
                **kwargs
            )
            self.geo_jsons = []

        def _get_synced_geojson_from_draw_control(self):
            return [data.copy() for data in self.geo_jsons]

        def _bind_to_draw_control(self):
            # In a non-test environment, `_on_draw` would be used here.
            self.initialized = True

        def _remove_geometry_at_index_on_draw_control(self, index):
            geo_json = self.geo_jsons[index]
            del self.geo_jsons[index]
            self._on_draw("deleted", geo_json)

        def _clear_draw_control(self):
            self.geo_jsons = []

        def _on_draw(self, action, geo_json):
            """Mimics the ipyleaflet DrawControl handler."""
            if action == "created":
                self._handle_geometry_created(geo_json)
            elif action == "edited":
                self._handle_geometry_edited(geo_json)
            elif action == "deleted":
                self._handle_geometry_deleted(geo_json)

        def create(self, geo_json):
            self.geo_jsons.append(geo_json)
            self._on_draw("created", geo_json)

        def edit(self, i, geo_json):
            self.geo_jsons[i] = geo_json
            self._on_draw("edited", geo_json)

        def delete(self, i):
            geo_json = self.geo_jsons[i]
            del self.geo_jsons[i]
            self._on_draw("deleted", geo_json)


class TestBasemap(unittest.TestCase):
    """Tests for the Basemap class in the `map_widgets` module."""

    def setUp(self):
        self.map_fake = fake_map.FakeMap()
        self.basemaps = ["first", "default", "bounded"]
        self.default = "default"
        self.xyz_services = {"bounded": {"bounds": [[2, 1], [4, 3]]}}
        self.basemap_widget = map_widgets.Basemap(
            self.map_fake, self.basemaps, self.default, self.xyz_services
        )

    def tearDown(self):
        pass

    @property
    def _close_button(self):
        return _query_widget(
            self.basemap_widget,
            ipywidgets.Button,
            lambda c: c.tooltip == "Close the basemap widget",
        )

    @property
    def _droopdown(self):
        return _query_widget(
            self.basemap_widget,
            ipywidgets.Dropdown,
            lambda _: True,
        )

    def test_basemap_no_map(self):
        """Tests that a valid map must be passed in."""
        with self.assertRaisesRegex(ValueError, "valid map"):
            map_widgets.Basemap(None, self.basemaps, self.default, self.xyz_services)

    def test_basemap(self):
        """Tests that the basemap's initial UI is set up properly."""
        self.assertIsNotNone(self._close_button)
        self.assertIsNotNone(self._droopdown)
        self.assertEqual(self._droopdown.value, "default")
        self.assertEqual(len(self._droopdown.options), 3)

    def test_basemap_close(self):
        """Tests that triggering the closing button fires the close event."""
        on_close_mock = Mock()
        self.basemap_widget.on_close = on_close_mock
        self._close_button.click()

        on_close_mock.assert_called_once()

    @patch.object(fake_map.FakeMap, "zoom_to_bounds")
    def test_basemap_selection(self, zoom_to_bounds_mock):
        """Tests that a basemap selection updates the map."""
        self.assertEqual(self.map_fake.find_layer_index("first"), -1)
        self.assertEqual(self.map_fake.find_layer_index("bounded"), -1)

        self._droopdown.value = "first"
        self.assertEqual(self.map_fake.find_layer_index("first"), 0)
        self.assertEqual(self.map_fake.find_layer_index("bounded"), -1)
        zoom_to_bounds_mock.assert_not_called()

        self._droopdown.value = "bounded"
        self.assertEqual(self.map_fake.find_layer_index("first"), 0)
        self.assertEqual(self.map_fake.find_layer_index("bounded"), 1)
        zoom_to_bounds_mock.assert_called_with([1, 2, 3, 4])
