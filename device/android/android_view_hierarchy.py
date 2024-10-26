from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import json
import re
import numpy as np

import attr
from str2bool import str2bool as strtobool
from enum import Enum
from lxml import etree
import cognisim.utils.constants as config


class UIObjectType(Enum):
    """Types of the different UI objects."""
    UNKNOWN = 0
    BUTTON = 1
    CHECKBOX = 2
    CHECKEDTEXTVIEW = 3
    EDITTEXT = 4
    IMAGEBUTTON = 5
    IMAGEVIEW = 6
    RADIOBUTTON = 7
    SLIDINGDRAWER = 8
    SPINNER = 9
    SWITCH = 10
    TABWIDGET = 11
    TEXTVIEW = 12
    TOGGLEBUTTON = 13
    VIDEOVIEW = 14
    SEARCHVIEW = 15


class UIObjectGridLocation(Enum):
    """The on-screen grid location (3x3 grid) of an UI object."""
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    LEFT = 3
    CENTER = 4
    RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTER = 7
    BOTTOM_RIGHT = 8


@attr.s
class BoundingBox(object):
    """The bounding box with horizontal/vertical coordinates of an UI object."""
    x1 = attr.ib()
    y1 = attr.ib()
    x2 = attr.ib()
    y2 = attr.ib()


@attr.s
class UIObject(object):
    """Represents an UI object from the leaf node in the view hierarchy."""
    obj_type = attr.ib()
    obj_name = attr.ib()
    word_sequence = attr.ib()
    text = attr.ib()
    resource_id = attr.ib()
    android_class = attr.ib()
    android_package = attr.ib()
    content_desc = attr.ib()
    clickable = attr.ib()
    visible = attr.ib()
    enabled = attr.ib()
    focusable = attr.ib()
    focused = attr.ib()
    scrollable = attr.ib()
    long_clickable = attr.ib()
    selected = attr.ib()
    bounding_box = attr.ib()
    grid_location = attr.ib()
    dom_location = attr.ib()
    pointer = attr.ib()
    neighbors = attr.ib()


def _build_word_sequence(text, content_desc, resource_id):
    """Returns a sequence of word tokens based on certain attributes.

    Args:
      text: `text` attribute of an element.
      content_desc: `content_desc` attribute of an element.
      resource_id: `resource_id` attribute of an element.

    Returns:
      A sequence of word tokens.
    """
    if text or content_desc:
        return re.findall(r"[\w']+|[?.!/,;:]", text if text else content_desc)
    else:
        # logger.info(f"Resource ID: {resource_id}")
        if resource_id is not None:
            name = resource_id.split('/')[-1]
            return filter(None, name.split('_'))
        else:
            return []


def _build_object_type(android_class):
    """Returns the object type based on `class` attribute.

    Args:
      android_class: `class` attribute of an element (Android class).

    Returns:
      The UIObjectType enum.
    """
    if android_class.startswith('android.widget'):
        widget_type = android_class.split('.')[2]
        for obj_type in UIObjectType:
            if obj_type.name == widget_type.upper():
                return obj_type
    widget_type = android_class.split('.')[-1]
    for obj_type in UIObjectType:
        if obj_type.name in widget_type.upper():
            return obj_type
    return UIObjectType.BUTTON


def _build_object_name(text, content_desc):
    """Returns the object name based on `text` or `content_desc` attribute.

    Args:
      text: The `text` attribute.
      content_desc: The `content_desc` attribute.

    Returns:
      The object name string.
    """
    return text if text else content_desc


def _build_bounding_box(bounds):
    """Returns the object bounding box based on `bounds` attribute.

    Args:
      bounds: The `bounds` attribute.

    Returns:
      The BoundingBox object.
    """
    match = re.compile(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]').match(bounds)
    assert match, f"Invalid bounds format: {bounds}"
    x1, y1, x2, y2 = map(int, match.groups())
    return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)


def _build_clickable(element, tree_child_as_clickable=True):
    """Returns whether the element is clickable or one of its ancestors is.

    Args:
      element: The etree.Element object.
      tree_child_as_clickable: treat all tree children as clickable

    Returns:
      A boolean to indicate whether the element is clickable or one of its
      ancestors is.
    """
    clickable = element.get('clickable')
    if clickable == 'false':
        for node in element.iterancestors():
            if node.get('clickable') == 'true':
                clickable = 'true'
                break

    # Below code is try to fix that: some target UI have 'clickable==False'
    # but it's clickable by human actually

    # Checkable elemnts should also be treated as clickable
    # Some menu items may have clickable==False but checkable==True
    if element.get('checkable') == 'true':
        clickable = 'true'
    if tree_child_as_clickable:
        p = element.getparent()
        while p is not None:
            if p.get('class') == 'android.widget.ListView':
                clickable = 'true'
                break
            p = p.getparent()

    return strtobool(clickable)


def _pixel_distance(a_x1, a_x2, b_x1, b_x2):
    """Calculates the pixel distance between bounding box a and b.

    Args:
      a_x1: The x1 coordinate of box a.
      a_x2: The x2 coordinate of box a.
      b_x1: The x1 coordinate of box b.
      b_x2: The x2 coordinate of box b.

    Returns:
      The pixel distance between box a and b on the x axis. The distance
      on the y axis can be calculated in the same way. The distance can be
      positive number (b is right/bottom to a) and negative number
      (b is left or top to a).
    """
    # if a and b are close enough, then we set the their distance to be 1
    # because there are typically padding spaces inside an object's bounding
    # box
    if b_x1 <= a_x2 and a_x2 - b_x1 <= config.ADJACENT_BOUNDING_BOX_THRESHOLD:
        return 1
    if a_x1 <= b_x2 and b_x2 - a_x1 <= config.ADJACENT_BOUNDING_BOX_THRESHOLD:
        return -1
    # overlap
    if (a_x1 <= b_x1 <= a_x2) or (a_x1 <= b_x2 <= a_x2) or (
            b_x1 <= a_x1 <= b_x2) or (b_x1 <= a_x2 <= b_x2):
        return 0
    elif b_x1 > a_x2:
        return b_x1 - a_x2
    else:
        return b_x2 - a_x1


def _grid_coordinate(x, width):
    """Calculates the 3x3 grid coordinate on the x axis.

    The grid coordinate on the y axis is calculated in the same way.

    Args:
      x: The x coordinate: [0, width).
      width: The screen width.

    Returns:
      The grid coordinate: [0, 2].
      Note that the screen is divided into 3x3 grid, so the grid coordinate
      uses the number from 0, 1, 2.
    """
    assert 0 <= x <= width
    grid_x_0 = width / 3
    grid_x_1 = 2 * grid_x_0
    if 0 <= x < grid_x_0:
        grid_coordinate_x = 0
    elif grid_x_0 <= x < grid_x_1:
        grid_coordinate_x = 1
    else:
        grid_coordinate_x = 2
    return grid_coordinate_x


def _grid_location(bbox, screen_width, screen_height):
    """Calculates the grid number of the UI object's bounding box.

    The screen can be divided into 3x3 grid:
    (0, 0) (0, 1) (0, 2)        0   1   2
    (1, 0) (1, 1) (1, 2)  --->  3   4   5
    (2, 0) (2, 1) (2, 2)        6   7   8

    Args:
      bbox: The bounding box of the UI object.
      screen_width: The width of the screen associated with the hierarchy.
      screen_height: The height of the screen associated with the hierarchy.

    Returns:
      The grid location number.
    """
    bbox_center_x = (bbox.x1 + bbox.x2) / 2
    bbox_center_y = (bbox.y1 + bbox.y2) / 2
    bbox_grid_x = _grid_coordinate(bbox_center_x, screen_width)
    bbox_grid_y = _grid_coordinate(bbox_center_y, screen_height)
    return UIObjectGridLocation(bbox_grid_y * 3 + bbox_grid_x)


def get_view_hierarchy_leaf_relation(objects, _screen_width, _screen_height):
    """Calculates adjacency relation from list of view hierarchy leaf nodes.
    Args:
        objects: a list of objects.
        _screen_width, _screen_height: Screen width and height.
    Returns:
        An un-padded feature dictionary as follow:
        'v_distance': 2d numpy array of ui object vertical adjacency relation.
        'h_distance': 2d numpy array of ui object horizontal adjacency relation.
        'dom_distance': 2d numpy array of ui object dom adjacency relation.
    """
    vh_node_num = len(objects)
    vertical_adjacency = np.zeros((vh_node_num, vh_node_num))
    horizontal_adjacency = np.zeros((vh_node_num, vh_node_num))
    for row in range(len(objects)):
        for column in range(len(objects)):
            if row == column:
                h_dist = v_dist = 0
            else:
                node1 = objects[row]
                node2 = objects[column]
                h_dist, v_dist = normalized_pixel_distance(
                    node1, node2, _screen_width, _screen_height)
                # print(node1.text, node2.text, v_dist)
            vertical_adjacency[row][column] = v_dist
            horizontal_adjacency[row][column] = h_dist
    return {
        'v_distance': vertical_adjacency,
        'h_distance': horizontal_adjacency
    }


def _get_single_direction_neighbors(object_idx, ui_v_dist, ui_h_dist):
    """Gets four 'single direction neighbors' for one target ui_object.
    If B is A's bottom/top 'single direction neighbor', it means B is the
    vertical closest neighbor among all object whose horizontal distance to A is
    smaller than margin threshold. Same with left/right direction neighbor.
    Args:
        object_idx: index number of target ui_object in ui_object_list
        ui_v_dist: ui objects' vertical distances. shape=[num_ui_obj, num_ui_obj]
        ui_h_dist: ui objects' horizontal distances. shape=[num_ui_obj, num_ui_obj]
    Returns:
        a dictionary, keys are NeighborContextDesc Instance, values are neighbor
        object index.
    """
    neighbor_dict = {}
    vertical_dist = ui_v_dist[object_idx]
    horizontal_dist = ui_h_dist[object_idx]
    bottom_neighbors = np.array([
        idx for idx in range(len(vertical_dist)) if vertical_dist[idx] > 0 and
        abs(horizontal_dist[idx]) < config.NORM_HORIZONTAL_NEIGHBOR_MARGIN
    ])
    top_neighbors = np.array([
        idx for idx in range(len(vertical_dist)) if vertical_dist[idx] < 0 and
        abs(horizontal_dist[idx]) < config.NORM_HORIZONTAL_NEIGHBOR_MARGIN
    ])
    right_neighbors = np.array([
        idx for idx in range(len(horizontal_dist)) if horizontal_dist[idx] > 0 and
        abs(vertical_dist[idx]) < config.NORM_VERTICAL_NEIGHBOR_MARGIN
    ])
    left_neighbors = np.array([
        idx for idx in range(len(horizontal_dist)) if horizontal_dist[idx] < 0 and
        abs(vertical_dist[idx]) < config.NORM_VERTICAL_NEIGHBOR_MARGIN
    ])

    if bottom_neighbors.size:
        neighbor_dict['top'] = bottom_neighbors[np.argmin(
            vertical_dist[bottom_neighbors])]
    if top_neighbors.size:
        neighbor_dict['bottom'] = top_neighbors[np.argmax(
            vertical_dist[top_neighbors])]
    if right_neighbors.size:
        neighbor_dict['left'] = right_neighbors[np.argmin(
            horizontal_dist[right_neighbors])]
    if left_neighbors.size:
        neighbor_dict['right'] = left_neighbors[np.argmax(
            horizontal_dist[left_neighbors])]

    return neighbor_dict


def normalized_pixel_distance(node1, node2, _screen_width, _screen_height):
    """Calculates normalized pixel distance between this node and other node.

    Args:
      node1, node2: Another object.
      _screen_width, _screen_height: Screen width and height.

    Returns:
      Normalized pixel distance on both horizontal and vertical direction.
    """
    h_distance = _pixel_distance(_build_bounding_box(node1.get('bounds')).x1,
                                 _build_bounding_box(node1.get('bounds')).x2,
                                 _build_bounding_box(node2.get('bounds')).x1,
                                 _build_bounding_box(node2.get('bounds')).x2)
    v_distance = _pixel_distance(_build_bounding_box(node1.get('bounds')).y1,
                                 _build_bounding_box(node1.get('bounds')).y2,
                                 _build_bounding_box(node2.get('bounds')).y1,
                                 _build_bounding_box(node2.get('bounds')).y2)

    return float(h_distance) / _screen_width, float(
        v_distance) / _screen_height


def _build_neighbors(
        node,
        view_hierarchy_leaf_nodes,
        _screen_width,
        _screen_height):
    """Builds the neighbours from view_hierarchy.

    Args:
      node: The current etree root node.
      view_hierarchy_leaf_nodes: All of the etree nodes.
      _screen_width, _screen_height: Screen width and height.

    Returns:
      Neighbour directions and object pointers.
    """
    if view_hierarchy_leaf_nodes is None:
        return None
    vh_relation = get_view_hierarchy_leaf_relation(
        view_hierarchy_leaf_nodes, _screen_width, _screen_height)
    _neighbor = _get_single_direction_neighbors(
        view_hierarchy_leaf_nodes.index(node),
        vh_relation['v_distance'],
        vh_relation['h_distance'])
    for k, v in _neighbor.items():
        _neighbor[k] = view_hierarchy_leaf_nodes[v].get('pointer')
    return _neighbor


def _build_etree_from_json(root, json_dict):
    """Builds the element tree from json_dict.

    Args:
      root: The current etree root node.
      json_dict: The current json_dict corresponding to the etree root node.
    """
    # set node attributes
    if root is None or json_dict is None:
        return
    x1, y1, x2, y2 = json_dict.get('bounds', [0, 0, 0, 0])
    root.set('bounds', '[%d,%d][%d,%d]' % (x1, y1, x2, y2))
    root.set('class', json_dict.get('class', ''))
    # XML element cannot contain NULL bytes.
    root.set('text', json_dict.get('text', '').replace('\x00', ''))
    root.set('resource-id', json_dict.get('resource-id', ''))
    content_desc = json_dict.get('content-desc', [None])
    root.set(
        'content-desc',
        '' if content_desc[0] is None else content_desc[0].replace('\x00', ''))
    root.set('package', json_dict.get('package', ''))
    root.set('visible', str(json_dict.get('visible-to-user', True)))
    root.set('enabled', str(json_dict.get('enabled', False)))
    root.set('focusable', str(json_dict.get('focusable', False)))
    root.set('focused', str(json_dict.get('focused', False)))
    root.set(
        'scrollable',
        str(
            json_dict.get('scrollable-horizontal', False) or
            json_dict.get('scrollable-vertical', False)))
    root.set('clickable', str(json_dict.get('clickable', False)))
    root.set('long-clickable', str(json_dict.get('long-clickable', False)))
    root.set('selected', str(json_dict.get('selected', False)))
    root.set('pointer', str(json_dict.get('pointer', '')))
    if 'children' not in json_dict:  # leaf node
        return
    for child in json_dict['children']:
        # some json file has 'null' as one of the children.
        if child:
            child_node = etree.Element('node')
            root.append(child_node)
            _build_etree_from_json(child_node, child)


class LeafNode(object):
    """Represents a leaf node in the view hierarchy data from xml."""

    def __init__(self,
                 element,
                 all_elements=None,
                 dom_location=None,
                 screen_width=config.SCREEN_WIDTH,
                 screen_height=config.SCREEN_HEIGHT):
        """Constructor.

        Args:
          element: The etree.Element object.
          all_elements: All the etree.Element objects in the view hierarchy.
          dom_location: [depth, preorder-index, postorder-index] of element.
          screen_width: The width of the screen associated with the element.
          screen_height: The height of the screen associated with the element.
        """
        assert not element.findall('.//node')
        self.element = element
        self._screen_width = screen_width
        self._screen_height = screen_height
        # logger.info(f"element: {element}")
        bbox = _build_bounding_box(element.get('bounds'))
        self.uiobject = UIObject(
            obj_type=_build_object_type(element.get('class')),
            obj_name=_build_object_name(
                element.get('text'), element.get('content-desc')),
            word_sequence=_build_word_sequence(
                element.get('text'), element.get('content-desc'),
                element.get('resource-id')),
            text=element.get('text'),
            resource_id=element.get('resource-id'),
            android_class=element.get('class'),
            android_package=element.get('package'),
            content_desc=element.get('content-desc'),
            clickable=_build_clickable(element),
            visible=strtobool(element.get('visible', default='true')),
            enabled=strtobool(element.get('enabled')),
            focusable=strtobool(element.get('focusable')),
            focused=strtobool(element.get('focused')),
            scrollable=strtobool(element.get('scrollable')),
            long_clickable=strtobool(element.get('long-clickable')),
            selected=strtobool(element.get('selected')),
            bounding_box=bbox,
            grid_location=_grid_location(bbox, self._screen_width,
                                         self._screen_height),
            dom_location=dom_location,
            pointer=element.get('pointer'),
            neighbors=_build_neighbors(
                element, all_elements,
                self._screen_width, self._screen_height))

    def dom_distance(self, other_node):
        """Calculates dom distance between this node and other node.

        Args:
          other_node: Another LeafNode object.

        Returns:
          The dom distance in between two leaf nodes: defined as the number of
          nodes on the path from one leaf node to the other on the tree.
        """
        intersection = [
            node for node in self.element.iterancestors()
            if node in other_node.element.iterancestors()
        ]
        assert intersection
        ancestor_list = list(self.element.iterancestors())
        other_ancestor_list = list(other_node.element.iterancestors())
        return ancestor_list.index(
            intersection[0]) + other_ancestor_list.index(intersection[0]) + 1


class DomLocationKey(Enum):
    """Keys of dom location info."""
    DEPTH = 0
    PREORDER_INDEX = 1
    POSTORDER_INDEX = 2


class ViewHierarchy(object):
    """Represents the view hierarchy data from UIAutomator dump."""

    def __init__(self,
                 screen_width=config.SCREEN_WIDTH,
                 screen_height=config.SCREEN_HEIGHT):
        """Constructor.

        Args:
          screen_width: The pixel width of the screen for the view hierarchy.
          screen_height: The pixel height of the screen for the view hierarchy.
        """
        self._root = None
        self._root_element = None
        self._all_visible_leaves = []
        self._dom_location_dict = None
        self._preorder_index = 0
        self._postorder_index = 0
        self._screen_width = screen_width
        self._screen_height = screen_height

    def load_xml(self, xml_content):
        """Builds the etree from xml content.

        Args:
          xml_content: The string containing xml content.
        """
        self._root = etree.XML(xml_content)
        self._root_element = self._root[0]

        self._all_visible_leaves = self._get_visible_leaves()

        # dom_location_dict:
        #   dict of {id(element): [depth, preorder-index, postorder-index]}
        # Note: for leaves of any tree, the following equation is always true:
        #
        #   depth == preorder-index - postorder-index (depth is # of ancestors)
        #
        self._dom_location_dict = self._calculate_dom_location()

    def load_json(self, json_content):
        """Builds the etree from json content.

        Args:
          json_content: The string containing json content.
        """
        json_dict = json.loads(json_content)
        if json_dict is None:
            raise ValueError('empty json file.')
        self._root = etree.Element('hierarchy', rotation='0')
        self._root_element = etree.Element('node')
        self._root.append(self._root_element)
        _build_etree_from_json(
            self._root_element,
            json_dict['activity']['root'])

        self._all_visible_leaves = self._get_visible_leaves()
        self._dom_location_dict = self._calculate_dom_location()

    def get_leaf_nodes(self):
        """Returns a list of all the leaf Nodes."""
        return [
            LeafNode(element, self._all_visible_leaves,
                     self._dom_location_dict[id(element)],
                     self._screen_width, self._screen_height)
            for element in self._all_visible_leaves
        ]

    def get_ui_objects(self):
        """Returns a list of all ui objects represented by leaf nodes."""
        return [
            LeafNode(element, self._all_visible_leaves,
                     self._dom_location_dict[id(element)],
                     self._screen_width, self._screen_height).uiobject
            for element in self._all_visible_leaves
        ]

    def dedup(self, click_x_and_y):
        """Dedup UI objects with same text or content_desc.

        Args:
          click_x_and_y: the event x and y (like: click pos in screen)
        """
        click_x, click_y = click_x_and_y

        # Map of {'name': [list of UI objects with this name]}
        name_element_map = collections.defaultdict(list)
        for element in self._all_visible_leaves:
            name = _build_object_name(element.get('text'),
                                      element.get('content_desc'))
            name_element_map[name].append(element)

        def delete_element(element):
            element.getparent().remove(element)

        for name, elements in name_element_map.items():
            if not name:
                continue
            # Search if the event (x, y) happens in one of these objects
            target_index = None
            for index, element in enumerate(elements):
                box = _build_bounding_box(element.get('bounds'))
                if (box.x1 <= click_x <= box.x2 and box.y1 <= click_y <= box.y2):
                    target_index = index

            if target_index is None:  # target UI obj is not in this elements
                for ele in elements[1:]:
                    delete_element(ele)
            else:  # if target UI obj is one of them, delete the rest UI objs
                for ele in elements[:target_index] + \
                        elements[target_index + 1:]:
                    delete_element(ele)

        print('Dedup: %d -> %d' % (len(self._all_visible_leaves),
                                   len(self._get_visible_leaves())))

        self._all_visible_leaves = self._get_visible_leaves()
        self._dom_location_dict = self._calculate_dom_location()

    def _get_visible_leaves(self):
        """Gets all the visible leaves from view hierarchy.

        Returns:
          all_visible_leaves: The list of all the visible leaf elements.
        """

        all_elements = [element for element in self._root.iter('*')]
        # View the attributes of each element
        # for element in all_elements:
        # logger.info(element.attrib)
        # logger.info(element.attrib.get('bounds'))
        # logger.info(element.attrib.get('displayed'))

        all_visible_leaves = [
            element for element in all_elements if self._is_leaf(element) and
            strtobool(element.attrib.get('displayed', default='true')) and
            self._is_within_screen_bound(element)
        ]
        return all_visible_leaves

    def _calculate_dom_location(self):
        """Calculate [depth, preorder-index, postorder-index] of all leaf nodes.

        This method is NOT thread safe if multiple threads call this method of same
        ViewHierarchy object: This method keeps updating self._preorder_index
        and self._postorder_index when call pre/post travel method recursively.

        All leaf elements will be filted and cached in self._all_visible_leaves.
        This is necessary because dom_location_dict use id(element) as keys, if
        call _root.iter('*') every time, the id(element) will not be a fixed value
        even for same element in XML.

        Returns:
          dom_location_dict, dict of
            {id(element): [depth, preorder-index, postorder-index]}
        """
        dom_location_dict = collections.defaultdict(lambda: [None, None, None])
        # Calculate the depth of all leaf nodes.
        for element in self._all_visible_leaves:
            ancestors = [node for node in element.iterancestors()]
            dom_location_dict[id(element)][DomLocationKey.DEPTH.value] = len(
                ancestors)

        # Calculate the pre/post index by calling pre/post iteration
        # recursively.
        self._preorder_index = 0
        self._pre_order_iterate(self._root, dom_location_dict)
        self._postorder_index = 0
        self._post_order_iterate(self._root, dom_location_dict)
        return dom_location_dict

    def _pre_order_iterate(self, element, dom_location_dict):
        """Preorder travel on hierarchy tree.

        Args:
          element: etree element which will be visited now.
          dom_location_dict: dict of
            {id(element): [depth, preorder-index, postorder-index]}
        """
        if self._is_leaf(element):
            dom_location_dict[id(element)][DomLocationKey.PREORDER_INDEX
                                           .value] = self._preorder_index
        self._preorder_index += 1

        for child in element:
            if child.getparent() == element:
                self._pre_order_iterate(child, dom_location_dict)

    def _post_order_iterate(self, element, dom_location_dict):
        """Postorder travel on hierarchy tree.

        Args:
          element: etree element which will be visited now.
          dom_location_dict: dict of
            {id(element): [depth, preorder-index, postorder-index]}
        """
        for child in element:
            if child.getparent() == element:
                self._post_order_iterate(child, dom_location_dict)

        if self._is_leaf(element):
            dom_location_dict[id(element)][DomLocationKey.POSTORDER_INDEX
                                           .value] = self._postorder_index
        self._postorder_index += 1

    def _is_leaf(self, element):
        """Whether an etree element is leaf in hierachy tree."""

        return not element.findall('.//*')

    def _is_within_screen_bound(self, element):
        """Whether an etree element's bounding box is within screen boundary."""
        bbox = _build_bounding_box(element.attrib.get('bounds'))
        in_x = (0 <= bbox.x1 <= self._screen_width) and (0 <= bbox.x2 <=
                                                         self._screen_width)
        in_y = (0 <= bbox.y1 <= self._screen_height) and (0 <= bbox.y2 <=
                                                          self._screen_height)
        x1_less_than_x2 = bbox.x1 < bbox.x2
        y1_less_than_y2 = bbox.y1 < bbox.y2
        return in_x and in_y and x1_less_than_x2 and y1_less_than_y2
