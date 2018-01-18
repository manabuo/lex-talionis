# Terrain Data Menu
import sys
from PyQt4 import QtGui, QtCore

sys.path.append('../')
import Code.Engine as Engine
# So that the code basically starts looking in the parent directory
Engine.engine_constants['home'] = '../'
import Code.GlobalConstants as GC
import Code.StatusObject as StatusObject
import Code.CustomObjects as CustomObjects

import EditorUtilities
from CustomGUI import SignalList, CheckableComboBox
import DataImport

class InfoKind(object):
    def __init__(self, num, name, kind):
        self.num = num
        self.name = name
        self.kind = kind
        self.image = Engine.subsurface(GC.ICONDICT['TileInfoIcons'], (0, num * 16, 16, 16))

info_kinds = [('Status', 'Status'),
              ('Formation', None),
              ('Seize', 'string'),
              ('Escape', 'string'),
              ('Arrive', 'string'),
              ('Shop', 'Item'),
              ('Village', 'string'),
              ('Locked', 'string'),
              ('Switch', 'string'),
              ('Search', 'string'),
              ('Thief_Escape', None),
              ('Reinforcement', 'string')]

kinds = {name: InfoKind(i, name, kind) for i, (name, kind) in enumerate(info_kinds)}

class TileInfo(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.tile_info_dict = dict()
        self.formation_highlights = dict()
        self.escape_highlights = dict()

    def get(self, coord):
        if coord in self.tile_info_dict:
            return self.tile_info_dict[coord]
        else:
            return None

    def get_str(self, coord):
        if coord in self.tile_info_dict and self.tile_info_dict[coord]:
            return ';'.join([(name + '=' + value) for name, value in self.tile_info_dict[coord].iteritems()])
        else:
            return None

    def set(self, coord, name, value):
        if coord not in self.tile_info_dict:
            self.tile_info_dict[coord] = {}
        self.tile_info_dict[coord][str(name)] = str(value)

    def delete(self, coord):
        self.tile_info_dict[coord] = {}

    def load(self, tile_info_location):
        self.clear()
        with open(tile_info_location) as fp:
            tile_info = fp.readlines()

        for line in tile_info:
            line = line.strip().split(':') # Should split in 2. First half being coordinate. Second half being properties
            coord = line[0].split(',')
            x1 = int(coord[0])
            y1 = int(coord[1])
            if len(coord) > 2:
                x2 = int(coord[2])
                y2 = int(coord[3])
                for i in range(x1, x2+1):
                    for j in range(y1, y2+1):
                        self.parse_tile_line((i, j), line[1].split(';'))
            else:
                self.parse_tile_line((x1, y1), line[1].split(';'))

    def parse_tile_line(self, coord, property_list):
        if coord not in self.tile_info_dict:
            self.tile_info_dict[coord] = {}
        for tile_property in property_list:
            property_name, property_value = tile_property.split('=')
            # Handle special cases...
            if property_name == 'Status': # Treasure does not need to be split. It is split by the itemparser function itself.
                # Turn these string of ids into a list of status objects
                status_list = []
                for status in property_value.split(','):
                    status_list.append(StatusObject.statusparser(status))
                property_value = status_list
            elif property_name in ("Escape", "Arrive"):
                self.escape_highlights[coord] = CustomObjects.Highlight(GC.IMAGESDICT["YellowHighlight"])
            elif property_name == "Formation":
                self.formation_highlights[coord] = CustomObjects.Highlight(GC.IMAGESDICT["BlueHighlight"])
            self.tile_info_dict[coord][property_name] = property_value

    def get_images(self):
        image_coords = {}
        # Returns a dictionary of coordinates mapped to images to display
        for coord, properties in self.tile_info_dict.iteritems():
            for name, value in properties.iteritems():
                image_coords[coord] = EditorUtilities.ImageWidget(kinds[name].image).image
        return image_coords

class ComboDialog(QtGui.QDialog):
    def __init__(self, instruction, items, item_list=[], parent=None):
        super(ComboDialog, self).__init__(parent)
        self.form = QtGui.QFormLayout(self)
        self.form.addRow(QtGui.QLabel(instruction))

        self.items = items

        # Create item combo box
        self.item_box = CheckableComboBox()
        self.item_box.uniformItemSizes = True
        self.item_box.setIconSize(QtCore.QSize(16, 16))
        for idx, item in enumerate(self.items):
            if item.image:
                self.item_box.addItem(EditorUtilities.create_icon(item.image), item.name)
            else:
                self.item_box.addItem(item.name)
            row = self.item_box.model().item(idx, 0)
            if str(self.item_box.itemText(idx)) in item_list:
                row.setCheckState(QtCore.Qt.Checked)
            else:
                row.setCheckState(QtCore.Qt.Unchecked)
        self.form.addRow(self.item_box)

        self.buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.form.addRow(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

    def getCheckedItems(self):
        item_list = []
        for idx, item in enumerate(self.items):
            row = self.item_box.model().item(idx, 0)
            if row.checkState() == QtCore.Qt.Checked:
                item_list.append(str(self.item_box.itemText(idx)))
        return item_list

    @staticmethod
    def getItems(parent, title, instruction, items, item_list=[]):
        dialog = ComboDialog(instruction, items, item_list, parent)
        dialog.setWindowTitle(title)
        result = dialog.exec_()
        items = dialog.getCheckedItems()
        return items, result == QtGui.QDialog.Accepted

class TileInfoMenu(QtGui.QWidget):
    def __init__(self, view, window=None):
        super(TileInfoMenu, self).__init__(window)
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.window = window

        self.view = view

        self.list = SignalList(self)
        self.list.setMinimumSize(128, 320)
        self.list.uniformItemSizes = True
        self.list.setIconSize(QtCore.QSize(32, 32))

        # Ingest Data
        self.info = sorted(kinds.values(), key=lambda x: x.num)
        for info in self.info:
            image = Engine.transform_scale(info.image, (32, 32))
            pixmap = EditorUtilities.create_pixmap(image)

            item = QtGui.QListWidgetItem(info.name)
            item.setIcon(QtGui.QIcon(pixmap))
            self.list.addItem(item)

        self.grid.addWidget(self.list, 0, 0)

        self.item_list = []
        self.status_list = []

        self.update()

    def trigger(self):
        self.view.tool = 'Tile Info'

    def start_dialog(self):
        kind = self.info[self.list.currentRow()].kind
        if kind == 'Status':
            statuses, ok = ComboDialog.getItems(self, "Tile Status Effects", "Select Status:", DataImport.skill_data, self.status_list)
            if ok:
                self.status_list = statuses
                return ','.join(statuses)
            else:
                return None
        elif kind == 'Item':
            items, ok = ComboDialog.getItems(self, "Shop Items", "Select Items:", DataImport.item_data, self.item_list)
            if ok:
                self.item_list = items
                return ','.join(items)
            else:
                return None
        elif kind == 'string':
            text, ok = QtGui.QInputDialog.getText(self, self.get_current_name(), 'Enter ID to use:')
            if ok:
                return text
            else:
                return None
        else:  # None
            return '0'

    def get_current_name(self):
        return self.info[self.list.currentRow()].name

    def update(self):
        pass

    def new(self):
        pass

    def load(self, overview):
        pass

    def save(self):
        pass
