CLASS_MAPPING = {
    "TEXTVIEW": "p",
    "BUTTON": "button",
    "IMAGEBUTTON": "button",
    "IMAGEVIEW": "img",
    "EDITTEXT": "input",
    "CHECKBOX": "input",
    "CHECKEDTEXTVIEW": "input",
    "TOGGLEBUTTON": "button",
    "RADIOBUTTON": "input",
    "SPINNER": "select",
    "SWITCH": "input",
    "SLIDINGDRAWER": "input",
    "TABWIDGET": "div",
    "VIDEOVIEW": "video",
    "SEARCHVIEW": "div",
}

from loguru import logger

from mobileadapt.device.android.android_view_hierarchy import ViewHierarchy
from mobileadapt.utils.constants import XML_SCREEN_HEIGHT, XML_SCREEN_WIDTH


def sortchildrenby_viewhierarchy(view, attr="bounds"):
    if attr == "bounds":
        bounds = [
            (
                ele.uiobject.bounding_box.x1,
                ele.uiobject.bounding_box.y1,
                ele.uiobject.bounding_box.x2,
                ele.uiobject.bounding_box.y2,
            )
            for ele in view
        ]
        sorted_bound_index = [
            bounds.index(i) for i in sorted(bounds, key=lambda x: (x[1], x[0]))
        ]

        sort_children = [view[i] for i in sorted_bound_index]
        view[:] = sort_children


class UI:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.elements = {}

    def encoding(self):
        logger.info(
            "reading hierarchy tree from {} ...".format(self.xml_file.split("/")[-1])
        )
        with open(self.xml_file, "r", encoding="utf-8") as f:
            vh_data = f.read().encode()

        vh = ViewHierarchy(
            screen_width=XML_SCREEN_WIDTH, screen_height=XML_SCREEN_HEIGHT
        )
        vh.load_xml(vh_data)
        view_hierarchy_leaf_nodes = vh.get_leaf_nodes()
        sortchildrenby_viewhierarchy(view_hierarchy_leaf_nodes)

        # logger.debug("encoding the ui elements in hierarchy tree...")
        codes = ""
        # logger.info(view_hierarchy_leaf_nodes)
        for _id, ele in enumerate(view_hierarchy_leaf_nodes):
            obj_type = ele.uiobject.obj_type.name
            text = ele.uiobject.text
            text = text.replace("\n", " ")
            resource_id = (
                ele.uiobject.resource_id if ele.uiobject.resource_id is not None else ""
            )
            content_desc = ele.uiobject.content_desc
            html_code = self.element_encoding(
                _id, obj_type, text, content_desc, resource_id
            )
            codes += html_code
            self.elements[_id] = ele.uiobject
        codes = "<html>\n" + codes + "</html>"

        # logger.info('Encoded UI\n' + codes)
        return codes

    def element_encoding(self, _id, _obj_type, _text, _content_desc, _resource_id):

        _class = _resource_id.split("id/")[-1].strip()
        _text = _text.strip()
        assert _obj_type in CLASS_MAPPING.keys(), print(_obj_type)
        tag = CLASS_MAPPING[_obj_type]

        if _obj_type in ["CHECKBOX", "CHECKEDTEXTVIEW", "SWITCH"]:
            code = f'  <input id={_id} type="checkbox" name="{_class}">\n'
            code += f"  <label for={_id}>{_text}</label>\n"
        elif _obj_type == "RADIOBUTTON":
            code = f'  <input id={_id} type="radio" name="{_class}">\n'
            code += f"  <label for={_id}>{_text}</label>\n"
        elif _obj_type == "SPINNER":
            code = f"  <label for={_id}>{_text}</label>\n"
            code += f'  <select id={_id} name="{_class}"></select>\n'
        elif _obj_type == "IMAGEVIEW":
            if _class == "":
                code = f'  <img id={_id} alt="{_content_desc}" />\n'
            else:
                code = f'  <img id={_id} class="{_class}" alt="{_content_desc}" />\n'
        else:
            if _class == "":
                _text = _content_desc if _text == "" else _text
                code = f'  <{tag} id={_id}">{_text}</{tag}>\n'
            else:
                _text = _content_desc if _text == "" else _text
                code = f'  <{tag} id={_id} class="{_class}">{_text}</{tag}>\n'
        return code
