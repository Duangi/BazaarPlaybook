from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Slot

class DebugOverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scanner Debug Info")
        self.resize(400, 600)
        # Always on top, tool window style
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool) 
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Summary Label
        self.lbl_summary = QLabel("Waiting for scan data...")
        self.lbl_summary.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background-color: #333; padding: 5px;")
        layout.addWidget(self.lbl_summary)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Class", "Conf", "X", "Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # Styles for Dark Mode
        self.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
            }
            QTableWidget {
                gridline-color: #444;
                background-color: #1e1e1e;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                border: 1px solid #444;
            }
            QTableWidgetItem {
                color: #ddd;
            }
        """)

    @Slot(list)
    def update_data(self, detections):
        """
        Update the debug window with new detections.
        detections: list of dicts {'class_id': int, 'confidence': float, 'box': [x,y,w,h]}
        """
        counts = {}
        rows = []

        for det in detections:
            cls_id = det.get('class_id', -1)
            conf = det.get('confidence', 0.0)
            box = det.get('box', [0, 0, 0, 0])
            
            # Map Class ID to Name
            # {0: 'day', 1: 'detail', 2: 'event', 3: 'item', 4: 'monstericon', 5: 'next', 
            #  6: 'randomicon', 7: 'shopicon', 8: 'skill', 9: 'store'}
            CLASS_MAP = {
                0: "Day (0)",
                1: "Detail (1)",
                2: "Event (2)",
                3: "Item (3)",
                4: "Monster (4)",
                5: "Next (5)",
                6: "Random (6)",
                7: "Shop (7)",
                8: "Skill (8)",
                9: "Store (9)"
            }
            cls_name = CLASS_MAP.get(cls_id, f"Unknown ({cls_id})")
            
            counts[cls_name] = counts.get(cls_name, 0) + 1
            
            rows.append((cls_name, conf, box))
            
        # Update Summary
        summary_text = "Detections Summary:\n"
        if not counts:
            summary_text += "No objects detected."
        else:
            for name, count in counts.items():
                summary_text += f"• {name}: {count}\n"
        self.lbl_summary.setText(summary_text)

        # Update Table - optimize by only updating if changed? 
        # For debug, just rewriting is fine, though it might flicker.
        # To avoid flicker, turn off sorting during update.
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        
        for i, (name, conf, box) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{conf:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(str(int(box[0]))))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(box[1]))))
            
        # Maybe auto scroll?
        # self.table.scrollToBottom()
