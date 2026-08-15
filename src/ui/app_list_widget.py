# src/ui/app_list_widget.py
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

class AppListItemWidget(QWidget):
    def __init__(self, app_name, package, findings):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Color indicator dots (up to 3 colors)
        colors = [f['color'] for f in findings if f.get('color')]
        for c in colors[:3]:
            dot = QLabel()
            dot.setFixedSize(12, 12)
            color_hex = {
                'green': '#4CAF50', 'yellow': '#FFC107', 'blue': '#2196F3',
                'purple': '#9C27B0', 'orange': '#FF9800', 'red': '#F44336'
            }
            dot.setStyleSheet(f"background-color: {color_hex.get(c, '#E0E0E0')}; border-radius: 6px;")
            layout.addWidget(dot)

        # App name and package
        name_label = QLabel(app_name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #f0f6fc;")
        layout.addWidget(name_label)

        pkg_label = QLabel(f"({package})")
        pkg_label.setStyleSheet("color: #8b949e; font-size: 10px;")
        layout.addWidget(pkg_label)

        layout.addStretch()
        self.setLayout(layout)

        # Tooltip with details
        tooltip = f"{app_name}\n{package}\n"
        for f in findings:
            tooltip += f"{f.get('description', '')}\n"
        self.setToolTip(tooltip)

class AppListWidget(QListWidget):
    app_context_menu_requested = pyqtSignal(str, str, list, list)  # pkg, name, colors, findings

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(self.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.all_items = []

    def add_app(self, name, package, colors):
        findings = []
        if 'green' in colors:
            findings.append({'type': 'license', 'description': 'License verification found', 'color': 'green'})
        if 'blue' in colors:
            findings.append({'type': 'ads', 'description': 'Google Ads found', 'color': 'blue'})
        if 'purple' in colors:
            findings.append({'type': 'system_boot', 'description': 'System app (boot)', 'color': 'purple'})
        if 'orange' in colors:
            findings.append({'type': 'system', 'description': 'System app', 'color': 'orange'})
        if 'yellow' in colors:
            findings.append({'type': 'custom_patch', 'description': 'Custom patch available', 'color': 'yellow'})
        if 'red' in colors:
            findings.append({'type': 'protected', 'description': 'Cannot patch', 'color': 'red'})
        if not findings:
            findings.append({'type': 'none', 'description': 'No special characteristics', 'color': 'white'})

        item = QListWidgetItem()
        widget = AppListItemWidget(name, package, findings)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, {
            'name': name,
            'package': package,
            'colors': colors,
            'findings': findings
        })
        self.addItem(item)
        self.setItemWidget(item, widget)
        self.all_items.append(item)

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            menu = QMenu()
            menu.addAction("Open Menu of Patches", lambda: self.app_context_menu_requested.emit(
                data['package'], data['name'], data['colors'], data['findings']))
            menu.addAction("Create Modified APK", lambda: self.app_context_menu_requested.emit(
                data['package'], data['name'], data['colors'], data['findings']))  # trigger rebuild dialog
            menu.addAction("Remove License Verification", lambda: None)  # "License removal"))
            menu.addAction("Remove Google Ads", lambda: None)  # "Ads removal"))
            menu.addAction("Custom Patch", lambda: None)  # "Custom patch"))
            menu.addSeparator()
            menu.addAction("Backup App", lambda: None)  # "Backup"))
            menu.addAction("Restore App", lambda: None)  # "Restore"))
            menu.addAction("Launch App", lambda: None)  # "Launch"))
            menu.exec(self.viewport().mapToGlobal(pos))

    def filter(self, text, filter_type):
        for item in self.all_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            name = data['name'].lower()
            colors = data['colors']
            visible = text in name if text else True
            if filter_type == "License check" and 'green' not in colors:
                visible = False
            elif filter_type == "Ads" and 'blue' not in colors:
                visible = False
            elif filter_type == "Custom patch" and 'yellow' not in colors:
                visible = False
            elif filter_type == "System" and ('purple' in colors or 'orange' in colors):
                visible = True
            elif filter_type == "All":
                visible = True
            else:
                visible = True
            item.setHidden(not visible)