from PySide6.QtCore import QThread, Signal, QRect, QTimer, QMutex
from PySide6.QtWidgets import QApplication
import time
import cv2
import numpy as np
import os
import json
from loguru import logger
import config

from core.detectors.yolo_detector import YoloDetector
from core.capturers.dxcam_capturer import DXCamCapturer
from core.capturers.mss_capturer import MSSCapturer
from core.comparators.feature_matcher import FeatureMatcher
from utils.window_utils import get_window_rect, get_mouse_pos_relative, is_window_foreground, is_focus_valid

from services.ocr_service import OCRService
from data_manager.config_manager import ConfigManager
import keyboard
import mouse

class AutoScanner(QThread):
    # type: 'monster' | 'card', id: str, rect: QRect
    show_detail = Signal(str, str) 
    hide_detail = Signal()
    status_changed = Signal(bool, str) # active, message
    scan_results_updated = Signal(list) # list of detection dicts
    force_show_detail = Signal(str, str) # New signal for hotkey
    item_pre_detected = Signal(str, str, str) # type, id, name (Hover pre-detection)

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.running = False
        self.paused = False
        self.mutex = QMutex()
        self._last_result = None
        self._last_status_msg = None
        
        # Hover State
        self._hover_start_time = 0
        self._last_hover_obj_box = None
        self._hover_recognized = False
        self._cached_result = None
        
        # Paths
        self.model_path = config.MODEL_PATH
        self.monster_db = os.path.join("assets", "json", "monsters_db.json")
        self.item_db = os.path.join("assets", "json", "items_db.json")

        # Load Name Maps
        self.item_map = self._load_json_db(self.item_db)
        self.monster_map = self._load_json_db(self.monster_db)

        # Services (Lazy Init)
        self.yolo = None
        self.capturer = None
        self.matcher = None
        self.ocr_monster = None
        self.ocr_card = None

    def _load_json_db(self, path):
        """Load minimal ID->Name map"""
        data_map = {}
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if 'id' in item:
                            # Prefer Chinese Name, fallback to English or ID
                            name = item.get('name_cn') or item.get('name_en') or item.get('id')
                            data_map[item['id']] = name
        except Exception as e:
            logger.error(f"Failed to load DB {path}: {e}")
        return data_map

    def initialize_services(self):
        if not self.yolo:
            try:
                self.yolo = YoloDetector(self.model_path, use_gpu=True)
            except Exception as e:
                logger.error(f"Failed to load YOLO: {e}")
        
        if not self.capturer:
            # Try DXCam first, then MSS
            try:
                self.capturer = DXCamCapturer()
                if not self.capturer.camera: # DXCam might fail inside init
                     raise Exception("DXCam init failed")
            except:
                logger.warning("DXCam unavailable, using MSS")
                self.capturer = MSSCapturer()
        
        if not self.matcher:
            self.matcher = FeatureMatcher()

        # Disable OCR for memory optimization test
        # if not self.ocr_monster:
        #     self.ocr_monster = OCRService(self.monster_db)
            
        # if not self.ocr_card and os.path.exists(self.item_db):
        #     # We reuse OCRService logic but different DB
        #     self.ocr_card = OCRService(self.item_db)

    def _emit_status(self, active, msg):
        if self._last_status_msg != msg:
            self.status_changed.emit(active, msg)
            self._last_status_msg = msg

    def _calculate_iou_or_overlap(self, box_container, box_inner):
        """
        Check if box_inner is mostly inside box_container.
        Returns: overlap ratio relative to box_inner area.
        """
        cx, cy, cw, ch = box_container
        ix, iy, iw, ih = box_inner
        
        # Calculate intersection
        x_left = max(cx, ix)
        y_top = max(cy, iy)
        x_right = min(cx + cw, ix + iw)
        y_bottom = min(cy + ch, iy + ih)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
            
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        inner_area = iw * ih
        
        if inner_area <= 0: return 0.0
        
        return intersection_area / inner_area

    def _get_size_category(self, w, h):
        """
        Predict size category based on Aspect Ratio (Height / Width).
        Logic:
        - H/W > 1.2  -> Small (Tall items like Weapons)
        - H/W < 0.85 -> Large (Wide items)
        - H/W ~ 1.0  -> Medium or Small (Square) [Differentiated by Area]
        """
        if w <= 0: return 'Small'
        
        ratio_h_w = h / w 
        area = w * h
        
        category = 'Medium' # Default
        
        if ratio_h_w > 1.2:
            category = 'Small'
        elif ratio_h_w < 0.85:
            category = 'Large'
        else:
            # Aspect ratio close to 1:1 (Square)
            # Distinguish Small vs Medium by area threshold (approx 140x140 at 1080p, adjusted for 4k?)
            # 4K area for 140x140 is ~20k-80k depending on scaling.
            # Using a conservative threshold. 
            if area < 20000:
                category = 'Small'
            else:
                category = 'Medium'
        
        logger.debug(f"🔍 Size Check: w={w}, h={h}, ratio(h/w)={ratio_h_w:.2f} -> {category}")
        return category

    def run(self):
        self._last_status_msg = None
        self._emit_status(True, "Initializing engines...")
        self.initialize_services()
        self._emit_status(True, "Scanning: The Bazaar")
        self.running = True
        
        while self.running:
            try:
                # Reload config occasionally to pick up UI changes
                if int(time.time()) % 2 == 0:
                    self.config.settings = self.config.load()
                
                if self.paused or not self.config.settings.get("auto_scan_enabled", False):
                    self._emit_status(False, "Paused / Disabled")
                    time.sleep(1)
                    continue


                # 0. Check Focus
                if not is_focus_valid("The Bazaar"):
                    if self._last_result:
                         self.hide_detail.emit()
                         self._last_result = None
                    self._emit_status(True, "Paused (Background)")
                    time.sleep(0.5)
                    continue

                # 1. Check Window
                win_rect = get_window_rect("The Bazaar") # Adjust title if needed
                if not win_rect:
                    self._emit_status(True, "Waiting for Game Window...")
                    time.sleep(2)
                    continue
                
                self._emit_status(True, "Scanning Active")
                
                # 2. Capture
                self.capturer.set_region(win_rect) # (x, y, w, h)
                frame = self.capturer.capture()
                if frame is None:
                    time.sleep(0.1)
                    continue

                # 3. Detect
                if self.yolo:
                    detections = self.yolo.detect_stream(frame)
                else:
                    detections = []
                
                # Emit detections for debug
                self.scan_results_updated.emit(detections)

                # 4. Check Mouse
                mx, my = get_mouse_pos_relative(win_rect[0], win_rect[1])
                
                # 5. Process Detections & Overlaps
                # Identify "Monster Events" (Event Box + Monster Icon inside)
                monster_events = [] 
                events = [d for d in detections if d['class_id'] == 2] # Event
                monster_icons = [d for d in detections if d['class_id'] == 4] # MonsterIcon
                
                for ev in events:
                    for icon in monster_icons:
                        overlap = self._calculate_iou_or_overlap(ev['box'], icon['box'])
                        if overlap >= 0.8:
                            # This event contains a monster icon -> It is a Monster Event
                            # We clone the event dict but mark it special
                            me = ev.copy()
                            me['_is_monster_event'] = True
                            monster_events.append(me)
                            break



                # 6. Hit Test & Hotkey Logic
                
                # Check for hotkey press
                hotkey_str = self.config.settings.get("detail_hotkey", "")
                hotkey_pressed = False
                if hotkey_str:
                    try:
                        if hotkey_str.startswith("mouse:"):
                            # Mouse button check
                            btn = hotkey_str.split(":")[1]
                            if mouse.is_pressed(btn):
                                hotkey_pressed = True
                        else:
                            # Keyboard check
                            if keyboard.is_pressed(hotkey_str):
                                hotkey_pressed = True
                    except:
                        pass
                
                hit_obj = None
                
                # Check Monster Events first (high priority)
                for me in monster_events:
                     x, y, w, h = me['box']
                     if x <= mx <= x + w and y <= my <= y + h:
                         hit_obj = me
                         break
                
                # If not hit monster event, check items/skills
                if not hit_obj:
                    for det in detections:
                        cls_id = det['class_id']
                        # Item(3) or Skill(8)
                        if cls_id not in [3, 8]: 
                            continue
                            
                        box = det['box']
                        x, y, w, h = box
                        if x <= mx <= x + w and y <= my <= y + h:
                            hit_obj = det
                            break
                
                current_time = time.time()
                
                # --- Hover Logic (Pre-detection) ---
                if hit_obj:
                    # Check if it's the "same" object (simple distance check to handle jitter)
                    is_same_obj = False
                    if self._last_hover_obj_box:
                        lx, ly, lw, lh = self._last_hover_obj_box
                        nx, ny, nw, nh = hit_obj['box']
                        # Center distance check
                        center_dist = ((lx+lw/2)-(nx+nw/2))**2 + ((ly+lh/2)-(ny+nh/2))**2
                        if center_dist < 2500: # 50px radius squared
                            is_same_obj = True
                    
                    if not is_same_obj:
                         self._last_hover_obj_box = hit_obj['box']
                         self._hover_start_time = current_time
                         self._hover_recognized = False
                         self._cached_result = None
                    
                    # Check dwell time (200ms)
                    if not self._hover_recognized and (current_time - self._hover_start_time) > 0.2:
                         # Trigger Pre-Recognition
                         result = self._recognize_object(frame, hit_obj)
                         if result:
                             rtype, rid, rname = result
                             self._cached_result = (rtype, rid)
                             self._hover_recognized = True
                             self.item_pre_detected.emit(rtype, rid, rname)
                else:
                    self._last_hover_obj_box = None
                    self._hover_start_time = 0
                    self._hover_recognized = False
                    self._cached_result = None

                # Optimization: If hotkey not pressed, just sleep and continue
                # But allow hover state to update (already done above)
                if not hotkey_pressed:
                    time.sleep(0.05)
                    continue

                if hit_obj:
                    # Hotkey Action (Sticky)
                    # Use cached result if valid
                    if self._cached_result and self._hover_recognized:
                        rtype, rid = self._cached_result
                        self.force_show_detail.emit(rtype, rid)
                    else:
                        # Recognize immediately
                        result = self._recognize_object(frame, hit_obj)
                        if result:
                            rtype, rid, rname = result
                            self._cached_result = (rtype, rid)
                            self._hover_recognized = True
                            self.force_show_detail.emit(rtype, rid)
                    
                    # Debounce
                    time.sleep(0.3)

            except Exception as e:
                logger.error(f"AutoScanner error: {e}")
                time.sleep(1)
    
    def _recognize_object(self, frame, hit_obj):
        """Helper to recognize object from a hit detection"""
        try:
            bx, by, bw, bh = hit_obj['box']
            h_img, w_img = frame.shape[:2]
            by = max(0, by); bx = max(0, bx)
            bh = min(h_img - by, bh); bw = min(w_img - bx, bw)
            
            if bw <= 0 or bh <= 0:
                return None
                
            crop = frame[by:by+bh, bx:bx+bw]
            
            result_id = None
            result_type = None
            result_name = "Unknown"

            # Logic A: Monster Event
            if hit_obj.get('_is_monster_event'):
                results = self.matcher.match_monster_character(crop)
                if results:
                    result_id, score = results[0]
                    result_type = 'monster'
                    result_name = self.monster_map.get(result_id, "Monster")
            
            # Logic B: Item/Skill
            else:
                cls_id = hit_obj['class_id']
                # Recalculate size cat for reliability
                size_cat = self._get_size_category(bw, bh)
                results = self.matcher.match(crop, size_cat)
                if results:
                    result_id = results[0][0]
                    result_type = 'card'
                    result_name = self.item_map.get(result_id, "Unknown Card")

            if result_id:
                logger.info(f"AutoScanner Identified: {result_name} ({result_id})")
                return (result_type, result_id, result_name)
        except Exception as e:
            logger.error(f"Recognition error: {e}")
        
        return None

    def stop(self):
        self.running = False
        self.wait()
