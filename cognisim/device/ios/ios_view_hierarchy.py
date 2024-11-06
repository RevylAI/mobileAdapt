from lxml import etree
from enum import Enum
from distutils.util import strtobool
import attr
import numpy as np
import re
import json
import collections
from loguru import logger
SCREEN_WIDTH = 430
SCREEN_HEIGHT = 932

SCREEN_CHANNEL = 4

ADJACENT_BOUNDING_BOX_THRESHOLD = 3
NORM_VERTICAL_NEIGHTBOR_MARGIN = 0.01
NORM_HORIZONTAL_NEIGHTBOR_MARGIN = 0.01
INPUT_ACTION_UPSAMPLE_RATIO = 1
XML_SCREEN_WIDTH = 430
XML_SCREEN_HEIGHT = 932
CLASS_MAPPING = {
    "STATICTEXT": 'p',
    "BUTTON": 'button',
    "IMAGE": 'img',
    "SWITCH": 'input',
    "CELL": 'div',
    "TABLE": 'table',
    "NAVIGATIONBAR": 'nav',
    "APPLICATION": "div",
    "TEXTFIELD": "input",
    "SECURETEXTFIELD": "input",
    "DatePicker:": "input",
    "PICKER": "input",
    "PICKERWHEEL": "input",
    "PAGEINDICATOR": "div",
    "KEY": "button",
    "KEYBOARD": "div",
    "LINK": "a",
    "SEARCHFIELD:": "input",
    "TEXTVIEW": "textarea",
    "WEBVIEW": "iframe",
    "BUTTON": "button",
    "OTHER": "div"
}


class DomLocationKey(Enum):
    '''
    Keys of dom location info
    '''
    DEPTH = 0
    PREORDER_INDEX = 1
    POSTORDER_INDEX = 2


class UIObjectType(Enum):
    """
    Typoes of the different UI objects
    """
    UNKNOWN = 0
    BUTTON = 1
    IMAGE = 2
    SWITCH = 3
    CELL = 4
    OTHER = 5
    TABLE = 6
    NAVIGATIONBAR = 7
    APPLICATION = 8
    WINDOW = 9
    STATICTEXT = 10
    SLIDER = 11
    TEXTFIELD = 12
    SECURETEXTFIELD = 13
    DATEPICKER = 14
    PICKER = 15
    PICKERWHEEL = 16
    PAGEINDICATOR = 17
    KEY = 18
    KEYBOARD = 19
    LINK = 20
    SEARCHFIELD = 21
    TEXTVIEW = 22
    WEBVIEW = 23


class UIObjectGridLocation(Enum):
    '''
    The on-screen grid location (3x3 grid) of an UI object
    '''
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
    '''
    The bounding box with horizontal/vertical coordinates of a ui object
    '''
    x1 = attr.ib()
    y1 = attr.ib()
    x2 = attr.ib()
    y2 = attr.ib()


@attr.s
class UiObject(object):
    '''
    Represents a UI object form the leaf node in the view hierarchy
    '''
    # type
    obj_type = attr.ib()
    # name
    obj_name = attr.ib()

    word_sequence = attr.ib()
    # text
    text = attr.ib()
    # accessibility label
    accesible = attr.ib()

    # ios_Type
    ios_class = attr.ib()

    # name
    content_desc = attr.ib()
    #

    visible = attr.ib()
    enabled = attr.ib()

    bounding_box = attr.ib()

    grid_location = attr.ib()

    dom_location = attr.ib()

    pointer = attr.ib()

    neighbors = attr.ib()


def _build_word_sequence(text, content_desc, resource_id):
    '''
    Returns a sequence of word toekns based on certain attributes

    Args:
    text: the text attribute of an element
    content_desc: the content-desc attribute of an element
    resource_id: `resource_id` attribute of an element
    Priority of the attributes: text > content_desc > resource_id
    Returns:
    A sequence of word tokens
    '''
    if text or content_desc:
        return re.findall(r"[\w']+|[.,!?;]", text if text else content_desc)
    else:
        name = resource_id.split('/')[-1]
        return filter(None, name.split('_'))


def _build_object_type(ios_class: str):
    '''
    Returns the object type based on `class` attribute

    Args:
    ios_class: the `class` attribute of an element
    Returns:
    The UIObjectType of the element

    '''
    if ios_class.startswith("XCUIElementType"):
        widget_type = ios_class.split("XCUIElementType")[1]
    for obj_type in UIObjectType:
        if obj_type.name == widget_type.upper():
            # logger.info(f"obj_type: {obj_type}")
            return obj_type
    return UIObjectType.BUTTON


def _build_object_name(text, content_desc):
    '''
    Returns the object name based on 'text' or 'context_desc' attribute
    Args:
    text: the `text` attribute of an element
    content_desc: the `content_desc` attribute of an element
    Returns:
    The object name
    '''
    return text if text else content_desc


def _build_bounding_box(bounds):
    '''
    Returns the object bounding box based on `bounds` attribute

    Args:
    bounds the `b_ounds` attribute of an element

    Return:
    The BoundingBox Object
    '''
    match = re.compile(
        r'\[\'(\d+)\', \'(\d+)\'\]\[\'(\d+)\', \'(\d+)\'\]').match(bounds)

    assert match
    x1, y1, x2, y2 = map(int, match.groups())
    return BoundingBox(x1, y1, x2, y2)


def _build_clickable(element, tree_child_as_clickable=True):
    ''''
    Returns whether the element is clickable based on certain attributes
    Args:
    element: The etree.element object
    tree_child_as_clickable: Whether to consider the tree child as clickable

    Returns:
    A boolean to indicate whether the element is clickable or one of its ancesors is
    basicallty given an element check if it is clickable or for the purposeo of this
    html representation
    '''
    clickable = element.get('accessible')
    if clickable == 'false':
        for node in element.iterancestors():
            if node.get('accessible') == 'true':
                clickable = True
                break
    if element.get('accessible') == 'true':
        clickable = 'true'
    if tree_child_as_clickable:
        p = element.getparent()
        while p is not None:
            if p.get('class') == 'android.widget.ListView':
                clickable = False
                break
            p = p.getparent()

    return strtobool(clickable)


def _pixel_distance(a_x1, a_x2, b_x1, b_x2):
    '''
    Calculates the pixel distance between bounding box a and b

    Args:
    a_x1: The x_1 coordinate of box a
    a_x2: The x_2 coordinate of box a
    b_x1: The x_1 coordinate of box b
    b_x2: The x_2 coordinate of box b

    Returns:
    The pixel distance between box a and b on the x acis. The distance
    on the y acis can be calculated in the same way. The distance can be
    positive number (b is right/bottom to a ) and negative
    (b is left/top to a)

    The _pixel_distance function calculates the pixel distance between two bounding box (a and b) along the x-axis

    Here's a breakdown:

    1. If box b is close enough to box a on the right side. (distance is less than or equal to a threshold), it returns 1.

    2. If box b is close enough to box a on the left side. (distance is less than or equal to a threshold), it returns -1.

    3. If box a and box b overlap on the x-axis it returns -

    4. If box b is to teh right of box a (b_x1 > a_x2), it reutrns the distance from the right side of box a to the left side of box b (b_x1 - a_x2)

    5. If none of the above conditions are met, box b is to the left of box a, and it returns the distance from the right side of box b to the left side of box a (b_x2- a_x1)

    The function assumes that the x1 coordinate is the left side of a box and the x2 coordinate is teh right side. The returned distance can be positive (if b is to the right of a)
    Tldr: the fucntion runs the distance between two boundings boxes along the x-acis and if they close enoguht it returns 1 or -1
    '''

    if b_x1 <= a_x2 and a_x2 - b_x1 <= ADJACENT_BOUNDING_BOX_THRESHOLD:
        return 1
    if a_x1 <= b_x2 and b_x2 - a_x1 <= ADJACENT_BOUNDING_BOX_THRESHOLD:
        return -1

    # overlap
    if (a_x1 <= b_x1 <= a_x2) or (a_x1 <= b_x2 <= a_x2) or (b_x1 <= a_x1 <= b_x2) or (b_x1 <= a_x2 <= b_x2):
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
    logger.info(f"x: {x}, width: {width}")
    # assert 0 <= x <= width
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
    '''
    Calculates teh grid number of the UI bounding box

    Args:
    bbox: The bounding box of the UI OBject
    screen_width: The width of the screen
    screen_height: The height of the screen

    Returns:
    The grid location number
    '''
    bbox_center_x = (bbox.x1 + bbox.x2) / 2
    bbox_center_y = (bbox.y1 + bbox.y2) / 2
    bbox_grid_x = _grid_coordinate(bbox_center_x, screen_width)
    bbox_grid_y = _grid_coordinate(bbox_center_y, screen_height)
    return UIObjectGridLocation(bbox_grid_y * 3 + bbox_grid_x)


def get_view_hiearchy_leaf_relation(objects, _screen_width, _screen_height):
    '''
    Calculates teh adjacency relatio from list of view hierarchy leaf nodes
    Args:
    object: The list of view hierarchy leaf nodes
    _screen_width, _screen_width: Screen width and height

    Returns:
        An un-padded feature dictionary as follow:
        'v_distance' 2d numpy array of ui object vertical adjancency relation
        'h_distance' 2d numpy array of ui object horizontal adjacency relation
        'dom_distance": 2d numpy array of ui object dom adjacency relation


        Adjacency matrix for vertical, horizontal, and dom relation

    '''

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

            vertical_adjacency[row][column] = v_dist
            horizontal_adjacency[row][column] = h_dist
    return {
        'v_distance': vertical_adjacency,
        'h_distance': horizontal_adjacency
    }


def normalized_pixel_distance(node1, node2, _screen_width, _screen_height):
    '''
    Caclulates teh normalized

    Args:
    node1, node2: Another object

    Reutrns:
    Normalized pixel distance on both horizontal and vertical direction
    '''
    node1_x_1 = int(node1.get('x'))

    node1_x_2 = node1_x_1 + int(node1.get('width'))

    node1_y_1 = int(node1.get('y'))
    node1_y_2 = node1_y_1 + int(node1.get('height'))
    node2_x_1 = int(node2.get('x'))

    node2_x_2 = node2_x_1 + int(node2.get('width'))

    node2_y_1 = int(node2.get('y'))

    node2_y_2 = node2_y_1 + int(node2.get('height'))

    h_distance = _pixel_distance(node1_x_1, node1_x_2, node2_x_1, node2_x_2)

    v_distance = _pixel_distance(node1_y_1, node1_y_2, node2_y_1, node2_y_2)

    return float(h_distance) / _screen_width, float(v_distance) / _screen_height


def _build_neighbors(node, view_hierarchy_leaf_nodes,
                     _screen_width, _screen_height):
    '''
    Builds the neighbors of a node based on the view hierarchy leaf nodes

    Args:
    node: The etree element object
    view_hierarchy_leaf_nodes: The list of view hierarchy leaf nodes
    _screen_width: The screen width
    _screen_height: The screen height

    Returns:
    A list of neighbors of the node
    '''
    if view_hierarchy_leaf_nodes is None:
        return None

    vh_relation = get_view_hiearchy_leaf_relation(
        view_hierarchy_leaf_nodes, _screen_width, _screen_height)
    _neighbor = _get_single_direction_neighbors(
        view_hierarchy_leaf_nodes,
        vh_relation['v_distance'],
        vh_relation['h_distance'],
    )
    for k, v in _neighbor.items():
        _neighbor[k] = view_hierarchy_leaf_nodes[v].get('pointer')
    return _neighbor


def _get_single_direction_neighbors(object_idx, ui_v_dist, ui_h_dist):
    '''
    Gets four single direction neighbor for one target ui_object

    Args:
    object_idx: The index of the target ui_object
    ui_v_dist: The vertical adjacency matrix
    ui_h_dist: The horizontal adjacency matrix

    Returns:
    A dictionary of the four single direction neighbors

    '''
    neighbor_dict = {}
    vertical_distance = ui_v_dist[object_idx]
    horizontal_distance = ui_h_dist[object_idx]
    bottom_neighbor = np.array([
        idx for idx in range(len(vertical_distance)) if vertical_distance[idx] > 0 and
        abs(horizontal_distance[idx]) < NORM_HORIZONTAL_NEIGHTBOR_MARGIN
    ])
    top_neighbor = np.array([
        idx for idx in range(len(vertical_distance)) if vertical_distance[idx] < 0 and
        abs(horizontal_distance[idx]) < NORM_HORIZONTAL_NEIGHTBOR_MARGIN
    ])
    right_neighbor = np.array([
        idx for idx in range(len(horizontal_distance)) if horizontal_distance[idx] > 0 and
        abs(vertical_distance[idx]) < NORM_VERTICAL_NEIGHTBOR_MARGIN
    ])
    left_neighbor = np.array([
        idx for idx in range(len(horizontal_distance)) if horizontal_distance[idx] < 0 and
        abs(vertical_distance[idx]) < NORM_VERTICAL_NEIGHTBOR_MARGIN
    ])

    if bottom_neighbor.size:
        neighbor_dict['top'] = bottom_neighbor[
            np.argmin(vertical_distance[bottom_neighbor])]
    if top_neighbor.size:
        neighbor_dict['bottom'] = top_neighbor[np.argmax(
            vertical_distance[top_neighbor])]
    if right_neighbor.size:
        neighbor_dict['left'] = right_neighbor[np.argmax(
            horizontal_distance[right_neighbor])]
    if left_neighbor.size:
        neighbor_dict['right'] = left_neighbor[np.argmin(
            horizontal_distance[left_neighbor])]

    return neighbor_dict


def _build_etree_from_json(root, json_dict):
    '''
    Builds teh element tree from json_dict

    Args:
    root: The current etree root node
    json_dict: The current json_dict corresponding ot the etree root node


    '''

    if root is None or json_dict is None:
        return
    x1, y1, x2, y2 = json_dict.get('bounds', [0, 0, 0, 0])
    root.set('bounds', '[%d, %d, %d, %d]' % (x1, y1, x2, y2))
    root.set('class', json_dict.get('class', ''))
    root.set('type', json_dict.get('type', ''))

    root.set('text', json_dict.get('text', '').replace('\x00', ''))

    root.set('resource-id', json_dict.get('resource-id', ''))

    root.set('content-desc', json_dict.get('content-desc', [None]))
    root.set('package', json_dict.get('package', ''))
    root.set('visible', str(json_dict.get('displayed', True)))
    root.set('enable', str(json_dict.get('enabled', False)))
    root.set('focusable', str(json_dict.get('focusable', False)))
    root.set('focused', str(json_dict.get('focused', False)))

    root.set('scrollable',
             str(
                 json_dict.get('scrollable-horizontal', False) or
                 json_dict.get('scrollable-vertical', False)
             ))
    root.set('clickable', str(json_dict.get('clickable', False)))
    root.set('long-clickable', str(json_dict.get('long-clickable', False)))

    root.set('selected', str(json_dict.get('selected', False)))

    root.set('pointer', json_dict.get('pointer', ''))

    if 'children' in json_dict:
        for child in json_dict['children']:
            child_element = etree.Element('node')
            root.append(child_element)
            _build_etree_from_json(child_element, child)


class LeafNode(object):
    '''
    Represent a leaf node in the view hierachy
    '''

    def __init__(
            self,
            element,
            all_elements=None,
            dom_location=None,
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
    ):
        '''
        Constructor.

        Args:

        element: the etree.Element object
        all_element: All the etree.Element objects in the view hierarchy
        dom_location: [depth, preorder-index, postorder-index] of element
        screen_width: The width of the screen associated with the element
        screen_height: The height of the screen associated with the element
        '''

        assert not len(element)
        self.element = element

        self._screen_width = screen_width

        self._screen_height = screen_height

        x_1 = str(max(0, int(element.get('x'))))
        y_1 = str(max(0, int(element.get('y'))))
        x_2 = str(int(x_1) + int(element.get('width')))
        y_2 = str(int(y_1) + int(element.get('height')))

        inits = str([x_1, y_1])
        ends = str([x_2, y_2])
        bounds = str(inits) + str(ends)

        bbox = _build_bounding_box(bounds)

        self.uiobject = UiObject(
            obj_type=_build_object_type(element.get('type')),
            content_desc=element.get('content-desc', default='').split('.')[-1]
            if '.' in element.get('name', default='') else element.get('name', default=''),
            obj_name=_build_object_name(
                text=element.get('name', default=''),
                content_desc=element.get('content-desc', default='')
            ),
            word_sequence=_build_word_sequence(
                text=element.get(
                    'text', default=''
                ),
                content_desc=element.get(
                    'content-desc', default=''
                ),
                resource_id=element.get('resource-id', default='')

            ),
            text=element.get('label', default=''),
            accesible=element.get('accessible', default='true'),

            ios_class=element.get('type', default=''),
            visible=strtobool(element.get('visible', default='true')),
            enabled=strtobool(element.get('enabled', default='true')),
            bounding_box=bbox,
            grid_location=_grid_location(bbox, self._screen_width, self._screen_height),
            dom_location=dom_location,
            pointer=element.get('pointer', default=''),
            neighbors=_build_neighbors(element, all_elements, self._screen_width, self._screen_height),

        )

    def dom_distance(self, other_node):
        '''
        Calculate the dom distance between two nodes
        Args:
        other_node: Another LeafNode
        Returns dom distance
        '''
        intersection = [
            node for node in self.element.iterancestors()
            if node in other_node.element.iterancestors()
        ]
        assert intersection
        ancestor_list = list(self.element.iterancestors())

        other_ancestor_list = list(other_node.element.iterancestors())

        return ancestor_list.index(
            intersection[0]) + other_ancestor_list.index(intersection[0]) + 1


class ViewHierarchy(object):
    '''
    Represents the view hierachy from XCUI Test
    '''

    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        '''
        Constructor

        Args:

        screen_width: The pixel width of the screen
        screen_height: The pixel height of the screen
        '''

        self._root = None
        self._root_element = None

        self._all_visible_leaves = []

        self._dom_location_dict = None
        self._preorder_index = 0
        self._postorder_index = 0

        self._screen_width = screen_width
        self._screen_height = screen_height

    def load_xml(self, xml_content):
        '''
        Builds the etree from xml content
        Args:
        xml_content: The string containing xml content
        '''
        self._root = etree.XML(xml_content)

        self._root_element = self._root[0]
        self._all_visible_leaves = self._get_visible_leaves()

        self._dom_location_dict = self._calculate_dom_location()

    def load_json(self, json_content):
        '''
        Builds the etree from json content
        args:
        json_content: The string containing json content
        '''
        json_dict = json.loads(json_content)
        if json_dict:
            raise ValueError('The json content is empty')

        self._root = etree.Element('hierarchy', rotation='0')
        self._root_element = etree.Element('node')
        self._root.append(self._root_element)
        _build_etree_from_json(self._root_element, json_dict['activity']['root'])

        self._all_visible_leaves = self._get_all_visible_leaves()

        self._dom_location_dict = self._calculate_dom_location_dict()

    def get_leaf_nodes(self):
        '''
        Returns all the leaf nodes in the view hierarchy

        '''
        return [

            LeafNode(
                element,
                self._all_visible_leaves,
                self._dom_location_dict[id(element)],
                self._screen_width,
                self._screen_height
            )
            for element in self._all_visible_leaves
        ]

    def get_ui_objects(self):
        '''
        Returns a list of all UI objects represented by leaf nodes
        '''
        return [
            LeafNode(element, self._all_visible_leaves, self._dom_location_dict[id(element)], self._screen_width, self._screen_height).uiobject
            for element in self._all_visible_leaves
        ]

    def dedup(self, click_x_and_y):
        '''
        Dedup UI objects with same text or content_desc
        Args
        click_x_and_y: The click x and y coordinates
        '''
        click_x, click_y = click_x_and_y

        name_element_map = collections.defaultdict(list)

        for element in self._all_visible_leaves:
            name = _build_object_name(
                element.get('text'),
                element.get('content-desc')
            )
            name_element_map[name].append(element)

        def delete_element(element):
            element.getparent().remove(element)

        for name, elements in name_element_map.items():
            if not name:
                continue
        target_index = None
        for index, element in enumerate(elements):
            box = _build_bounding_box(element.get('bounds'))
            if (box.x1 <= click_x <= box.x2) and (box.y1 <= click_y <= box.y2):
                target_index = index
                break

        if target_index is None:
            for ele in elements[1:]:
                delete_element(ele)
        else:
            for ele in elements[:target_index] + elements[target_index + 1:]:
                delete_element(ele)

        print('Dedup %d elements' % (len(elements) - 1))

        self._dom_location_dict = self._calculate_dom_location_dict()
        self._all_visible_leaves = self._get_visible_leaves()

    def _get_visible_leaves(self):
        '''
        Gets all visible leaves from view hierarchy
        All_visible_leaves: The list of teh visible leaf elements
        '''
        all_elements = [element for element in self._root.iter('*')]
        button_elements = [element for element in all_elements if element.get('type') == 'XCUIElementTypeButton']

        for button in button_elements:
            self._make_button_a_leaf(button)

        all_visible_leaves = [

            element for element in all_elements if self._is_leaf(element) and
            strtobool(element.get('visible', default='true')) and
            self._is_within_screen_bound(element)
        ]

        return all_visible_leaves

    def _make_button_a_leaf(self, element):
        '''
        IF an element is a button remove its children
        '''
        if element.get('type') == 'XCUIElementTypeButton':
            for child in element.findall('*'):
                element.remove(child)

    def _calculate_dom_location(self):
        '''
        Calcualte [depth, preorder-index, postorder-index] for each element

        This method is not thread safe if multiple threads call this method of same ViewHierarchy object object

        Returns:
        dom_location_dict, dict of
        {
            id(element): [depth, preorder-index, postorder-index]
        }
        '''
        dom_location_dict = collections.defaultdict(lambda: [None, None, None])
        for element in self._all_visible_leaves:
            ancestors = [node for node in element.iterancestors()]
            dom_location_dict[id(element)][DomLocationKey.DEPTH.value] = len(ancestors)

        self._peorder_index = 0
        self._preorder_iterate(self._root, dom_location_dict)
        self._postorder_index = 0
        self._postorder_iterate(self._root, dom_location_dict)
        return dom_location_dict

    def _preorder_iterate(self, element, dom_location_dict):
        '''
        Preorder traversal on the view hierarchy tree
        ARGS:
        element: The current etree element
        dom_location_dict: The dict of dom location info

        '''
        if self._is_leaf(element):
            dom_location_dict[id(element)][DomLocationKey.PREORDER_INDEX.value] = self._preorder_index
        self._preorder_index += 1
        for child in element:
            if child.getparent() == element:
                self._preorder_iterate(child, dom_location_dict)

    def _postorder_iterate(self, element, dom_location_dict):
        '''
        Postorder traversal on the view hierarchy tree
        Args:
        element: The current etree element
        dom_location_dict: The dict of dom location info
        '''
        for child in element:
            if child.getparent() == element:
                self._postorder_iterate(child, dom_location_dict)
        if self._is_leaf(element):
            dom_location_dict[id(element)][DomLocationKey.POSTORDER_INDEX.value] = self._postorder_index
        self._postorder_index += 1

    def _is_leaf(self, element):
        return not element.findall('.//*')

    def _is_within_screen_bound(self, element):
        '''
        Checks if the element is within the screen bound
        Args:
        element: The etree element object
        Returns:
        A boolean to indicate whether the element is within the screen bound
        '''
        x_1 = str(max(0, int(element.get('x'))))

        y_1 = str(max(0, int(element.get('y'))))

        x_2 = str(int(x_1) + int(element.get('width')))

        y_2 = str(int(y_1) + int(element.get('height')))
        # logger.info(x_1)
        inits = str([x_1, y_1])

        ends = str([x_2, y_2])

        bbox = _build_bounding_box(inits + ends)

        in_x = (0 <= bbox.x1 <= self._screen_width) or (0 <= bbox.x2 <= self._screen_width)

        in_y = (0 <= bbox.y1 <= self._screen_height) or (0 <= bbox.y2 <= self._screen_height)

        x1_less_than_x2 = bbox.x1 < bbox.x2

        y1_less_than_y2 = bbox.y1 < bbox.y2

        return in_x and in_y and x1_less_than_x2 and y1_less_than_y2


class UI:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.elements = {
        }

    def sortchildrenby_viewhierarchy(self, view, attr="bounds"):
        if attr == "bounds":
            bounds = [
                (ele.uiobject.bounding_box.x1, ele.uiobject.bounding_box.y1, ele.uiobject.bounding_box.x2, ele.uiobject.bounding_box.y2)
                for ele in view
            ]
            sorted_bounds_index = [
                bounds.index(i) for i in sorted(
                    bounds, key=lambda x: (x[1], x[0])
                )
            ]
            sort_children = [view[i] for i in sorted_bounds_index]
            view[:] = sort_children

    def encoding(self):
        '''
        Encodes the UI into a string representation

        Returns:
        the string representation of the UI
        '''
        with open(self.xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read().encode()

        vh = ViewHierarchy(
            screen_width=XML_SCREEN_WIDTH,
            screen_height=XML_SCREEN_HEIGHT
        )
        vh.load_xml(xml_content)
        view_hierarchy_leaf_nodes = vh.get_leaf_nodes()
        # logger.info(view_hierarchy_leaf_nodes)
        self.sortchildrenby_viewhierarchy(
            view_hierarchy_leaf_nodes,
            attr="bounds")

        codes = ''
        for _id, ele in enumerate(view_hierarchy_leaf_nodes):
            obj_type_str = ele.uiobject.obj_type.name
            text = ele.uiobject.text
            text = text.replace('\n', ' ')

            resource_id = ele.uiobject.obj_name

            content_desc = ele.uiobject.content_desc
            # logger.info(resource_id)
            # ogger.info(content_desc)

            html_code = self.element_encoding(
                _id=_id,
                _obj_type=obj_type_str,
                _text=text,
                _content_desc=content_desc,
                _resource_id=resource_id
            )

            codes += html_code if html_code else ''
            self.elements[_id] = ele.uiobject

        codes = "<html>\n" + codes + "</html>"

        return codes

    def action_encoding(self):
        '''
        Get Heuristic of possible actions output
        {action_type: type, encoding}
        '''
        pass

    def element_encoding(self,
                         _id,
                         _obj_type,
                         _text,
                         _content_desc,
                         _resource_id):
        '''
        Encodes the element into a string representation

        Args:
        _id: The id of the element
        _obj_type: The type of the element
        _text: The text of the element
        _content_desc: The content description of the element
        _resource_id: The resource id of the element

        Returns:
        The string representation of the element
        '''
        _class = _resource_id.split('.')[-1] if '.' in _resource_id else _resource_id
        _text = _text.strip()
        # logger.info(_id)
        # logger.info(_obj_type)

        assert _obj_type in CLASS_MAPPING.keys()

        tag = CLASS_MAPPING[_obj_type]

        if _obj_type == 'None':
            tag = ''
        code = ''
        if _obj_type == "XCUIElementTypeSwitch":
            code = f'<input id="{_id}" type="checkbox" name="{_resource_id}" class="{_class}" value="{_text}">\n'
            code += f'<label for="{_id}">{_text}</label>\n'

        elif _obj_type == "XCUIElementTypeImage":
            if _class == "":
                code = f'<img id="{_id}" src="{_resource_id}">\n'
            else:
                code = f'<img id="{_id}" class="{_class}" src="{_resource_id}">\n'
        else:
            _text = _content_desc if _text == "" else _text
            if _class == "":
                code = f'<{tag} id="{_id}">{_text}</{tag}>\n'
            else:
                code = f'<{tag} id="{_id}" class="{_class}">{_text}</{tag}>\n'
        return code
