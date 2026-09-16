import json
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
SAVE_VALID_MASK = True  # vùng polygon ROI hợp lệ; có thể dùng làm ignore-mask khi train


class Entropy1GTLabeler:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Entropy #1 - ROI + Thermal Paste Polygon GT Labeler")
        self.root.geometry("1380x900")
        self.root.minsize(1120, 740)

        # ---------------- Dataset state ----------------
        self.input_dir: Path | None = None
        self.output_dir: Path | None = None
        self.files: list[Path] = []
        self.file_index = -1
        self.current_path: Path | None = None
        self.source_rgb: np.ndarray | None = None

        # ---------------- Labeling state ----------------
        # mode: idle | roi | mask
        self.mode = "idle"

        # ROI polygons are stored in SOURCE-image coordinates.
        self.polygons: list[list[tuple[int, int]]] = []

        # The polygon currently being drawn.
        # In ROI mode: source-image coordinates.
        # In mask mode: ROI-local coordinates.
        self.current_polygon: list[tuple[int, int]] = []

        # Each ROI contains crop, valid_mask and thermal-paste mask polygons.
        self.rois: list[dict] = []
        self.roi_index = 0

        # ---------------- Canvas view transform ----------------
        self.zoom_factor = 1.0           # 1.0 = fit-to-window
        self.pan_x = 0.0                 # canvas pixels relative to centered fit
        self.pan_y = 0.0
        self.min_zoom = 1.0
        self.max_zoom = 24.0
        self.zoom_step = 1.22

        self.display_scale = 1.0
        self.display_offset_x = 0.0
        self.display_offset_y = 0.0
        self.display_w = 1
        self.display_h = 1
        self.photo = None
        self._pan_anchor: tuple[int, int] | None = None

        # ---------------- UI vars ----------------
        self.status_var = tk.StringVar(value="Chọn thư mục ảnh để bắt đầu.")
        self.progress_var = tk.StringVar(value="0 / 0")
        self.roi_progress_var = tk.StringVar(value="")
        self.zoom_var = tk.StringVar(value="Zoom: 100%")

        self._build_ui()
        self._bind_events()

    # ======================================================================
    # UI
    # ======================================================================
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=6)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top, text="1. Chọn thư mục ảnh", command=self.choose_input_folder).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="Chọn thư mục output", command=self.choose_output_folder).pack(side=tk.LEFT, padx=3)
        ttk.Label(top, textvariable=self.progress_var).pack(side=tk.LEFT, padx=15)
        ttk.Label(top, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)

        body = ttk.Frame(self.root, padding=(6, 0, 6, 6))
        body.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(body, bg="#202020", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        panel = ttk.Frame(body, width=320, padding=10)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)

        # ---------- View controls ----------
        ttk.Label(panel, text="VIEW", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        ttk.Label(
            panel,
            text=(
                "Lăn chuột: zoom tại vị trí con trỏ\n"
                "Nút giữa + kéo: pan ảnh\n"
                "+ / - : zoom | 0 : fit ảnh"
            ),
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(2, 5))

        zoom_row = ttk.Frame(panel)
        zoom_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(zoom_row, text="−", width=4, command=self.zoom_out_center).pack(side=tk.LEFT)
        ttk.Button(zoom_row, text="+", width=4, command=self.zoom_in_center).pack(side=tk.LEFT, padx=4)
        ttk.Button(zoom_row, text="Fit", width=7, command=self.reset_view).pack(side=tk.LEFT)
        ttk.Label(zoom_row, textvariable=self.zoom_var).pack(side=tk.LEFT, padx=8)

        ttk.Separator(panel).pack(fill=tk.X, pady=8)

        # ---------- ROI polygon ----------
        ttk.Label(panel, text="ROI POLYGON", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            panel,
            text=(
                "Click trái: thêm đỉnh\n"
                "Enter / chuột phải: chốt polygon\n"
                "Esc: huỷ polygon đang vẽ\n"
                "Ctrl+Z: bỏ đỉnh cuối"
            ),
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(0, 8))

        ttk.Button(panel, text="Chốt polygon ROI hiện tại", command=self.finish_polygon).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="Xoá polygon ROI cuối", command=self.delete_last_polygon).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="Xoá tất cả ROI polygon", command=self.clear_polygons).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="2. OK - Tạo các ROI", command=self.confirm_rois).pack(fill=tk.X, pady=(8, 2))
        ttk.Button(panel, text="Bỏ qua ảnh này", command=self.skip_current_image).pack(fill=tk.X, pady=2)

        ttk.Separator(panel).pack(fill=tk.X, pady=12)

        # ---------- Mask polygon ----------
        ttk.Label(panel, text="THERMAL-PASTE MASK POLYGON", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        ttk.Label(panel, textvariable=self.roi_progress_var).pack(anchor="w", pady=(2, 6))
        ttk.Label(
            panel,
            text=(
                "Trên mỗi ROI, khoanh một hoặc nhiều\n"
                "polygon quanh pixel thuộc Thermal Paste.\n"
                "Enter / chuột phải: chốt polygon mask."
            ),
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(0, 7))

        ttk.Button(panel, text="Chốt polygon mask hiện tại", command=self.finish_polygon).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="Xoá polygon mask cuối", command=self.delete_last_polygon).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="Xoá toàn bộ mask ROI hiện tại", command=self.clear_mask_polygons).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="← ROI trước", command=self.previous_roi).pack(fill=tk.X, pady=(9, 2))
        ttk.Button(panel, text="3. Xác nhận mask + ROI tiếp theo", command=self.save_and_next_roi).pack(fill=tk.X, pady=(8, 2))

        ttk.Separator(panel).pack(fill=tk.X, pady=12)
        ttk.Label(
            panel,
            text=(
                "Output:\n"
                "  images/ : ảnh ROI\n"
                "  masks/  : mask Thermal Paste 0/255\n"
                "  valid/  : vùng ROI polygon hợp lệ\n"
                "  meta/   : polygon/bbox/source"
            ),
            justify=tk.LEFT,
        ).pack(anchor="w")

    def _bind_events(self):
        # Polygon drawing
        self.canvas.bind("<Button-1>", self.on_left_down)
        self.canvas.bind("<Button-3>", self.on_right_down)

        # Pan with middle mouse button
        self.canvas.bind("<ButtonPress-2>", self.on_middle_down)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_up)

        # Mouse wheel: Windows/macOS and Linux/X11
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_linux_wheel_up)
        self.canvas.bind("<Button-5>", self.on_linux_wheel_down)

        self.canvas.bind("<Configure>", lambda _e: self.render())

        self.root.bind("<Return>", lambda _e: self.finish_polygon())
        self.root.bind("<Escape>", lambda _e: self.cancel_current_polygon())
        self.root.bind("<Control-z>", lambda _e: self.undo_polygon_point())
        self.root.bind("<plus>", lambda _e: self.zoom_in_center())
        self.root.bind("<KP_Add>", lambda _e: self.zoom_in_center())
        self.root.bind("<minus>", lambda _e: self.zoom_out_center())
        self.root.bind("<KP_Subtract>", lambda _e: self.zoom_out_center())
        self.root.bind("<Key-0>", lambda _e: self.reset_view())

    # ======================================================================
    # Dataset loading
    # ======================================================================
    def choose_input_folder(self):
        selected = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if not selected:
            return

        self.input_dir = Path(selected)
        self.files = sorted(
            p for p in self.input_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
        )

        if not self.files:
            messagebox.showerror("Không có ảnh", "Không tìm thấy file ảnh được hỗ trợ trong thư mục.")
            return

        if self.output_dir is None:
            self.output_dir = self.input_dir / "_entropy1_gt"
        self._prepare_output_dirs()

        self.file_index = -1
        self.load_next_image()

    def choose_output_folder(self):
        selected = filedialog.askdirectory(title="Chọn thư mục output")
        if not selected:
            return
        self.output_dir = Path(selected)
        self._prepare_output_dirs()
        self.status_var.set(f"Output: {self.output_dir}")

    def _prepare_output_dirs(self):
        if self.output_dir is None:
            return
        for name in ["images", "masks", "meta"]:
            (self.output_dir / name).mkdir(parents=True, exist_ok=True)
        if SAVE_VALID_MASK:
            (self.output_dir / "valid").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_rgb(path: Path) -> np.ndarray:
        with Image.open(path) as im:
            return np.array(im.convert("RGB"), dtype=np.uint8)

    def load_next_image(self):
        if not self.files:
            return

        self.file_index += 1
        if self.file_index >= len(self.files):
            self.mode = "idle"
            self.source_rgb = None
            self.canvas.delete("all")
            self.status_var.set("Hoàn tất toàn bộ queue ảnh.")
            self.progress_var.set(f"{len(self.files)} / {len(self.files)}")
            messagebox.showinfo("Hoàn tất", "Đã đi hết queue ảnh.")
            return

        self.current_path = self.files[self.file_index]
        try:
            self.source_rgb = self.load_rgb(self.current_path)
        except Exception as exc:
            messagebox.showwarning("Lỗi ảnh", f"Không đọc được:\n{self.current_path}\n\n{exc}")
            self.load_next_image()
            return

        self.polygons = []
        self.current_polygon = []
        self.rois = []
        self.roi_index = 0
        self.mode = "roi"
        self.progress_var.set(f"{self.file_index + 1} / {len(self.files)}")
        self.roi_progress_var.set("")
        self.status_var.set(f"ROI mode: {self.current_path.name}")
        self.reset_view(render=False)
        self.render()

    def skip_current_image(self):
        if self.mode == "idle":
            return
        if messagebox.askyesno("Bỏ qua", "Bỏ qua ảnh hiện tại và sang ảnh tiếp theo?"):
            self.load_next_image()

    # ======================================================================
    # Zoom / pan
    # ======================================================================
    def reset_view(self, render=True):
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom_var.set("Zoom: 100%")
        if render:
            self.render()

    def _current_fit_scale(self):
        base = self.get_display_base_image()
        if base is None:
            return 1.0
        h, w = base.shape[:2]
        ch = max(1, self.canvas.winfo_height())
        cw = max(1, self.canvas.winfo_width())
        return max(min(cw / w, ch / h), 1e-9)

    def _zoom_at(self, cx: float, cy: float, new_zoom: float):
        base = self.get_display_base_image()
        if base is None:
            return

        new_zoom = float(np.clip(new_zoom, self.min_zoom, self.max_zoom))
        if abs(new_zoom - self.zoom_factor) < 1e-12:
            return

        # Image point under cursor BEFORE zoom.
        old_scale = self.display_scale
        if old_scale <= 0:
            return
        img_x = (cx - self.display_offset_x) / old_scale
        img_y = (cy - self.display_offset_y) / old_scale

        h, w = base.shape[:2]
        ch = max(1, self.canvas.winfo_height())
        cw = max(1, self.canvas.winfo_width())
        fit = max(min(cw / w, ch / h), 1e-9)
        new_scale = fit * new_zoom
        new_w = w * new_scale
        new_h = h * new_scale
        centered_x = (cw - new_w) / 2.0
        centered_y = (ch - new_h) / 2.0

        # Keep the same image point exactly under the mouse cursor.
        wanted_offset_x = cx - img_x * new_scale
        wanted_offset_y = cy - img_y * new_scale
        self.pan_x = wanted_offset_x - centered_x
        self.pan_y = wanted_offset_y - centered_y
        self.zoom_factor = new_zoom
        self.zoom_var.set(f"Zoom: {self.zoom_factor * 100:.0f}%")
        self.render()

    def zoom_in_center(self):
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        self._zoom_at(cx, cy, self.zoom_factor * self.zoom_step)

    def zoom_out_center(self):
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        self._zoom_at(cx, cy, self.zoom_factor / self.zoom_step)

    def on_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_at(event.x, event.y, self.zoom_factor * self.zoom_step)
        elif event.delta < 0:
            self._zoom_at(event.x, event.y, self.zoom_factor / self.zoom_step)

    def on_linux_wheel_up(self, event):
        self._zoom_at(event.x, event.y, self.zoom_factor * self.zoom_step)

    def on_linux_wheel_down(self, event):
        self._zoom_at(event.x, event.y, self.zoom_factor / self.zoom_step)

    def on_middle_down(self, event):
        self._pan_anchor = (event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def on_middle_drag(self, event):
        if self._pan_anchor is None:
            return
        x0, y0 = self._pan_anchor
        self.pan_x += event.x - x0
        self.pan_y += event.y - y0
        self._pan_anchor = (event.x, event.y)
        self.render()

    def on_middle_up(self, _event):
        self._pan_anchor = None
        self.canvas.configure(cursor="crosshair")

    # ======================================================================
    # Coordinate helpers
    # ======================================================================
    def canvas_to_image(self, cx: float, cy: float):
        if self.display_scale <= 0:
            return None

        x = (cx - self.display_offset_x) / self.display_scale
        y = (cy - self.display_offset_y) / self.display_scale
        x = int(round(x))
        y = int(round(y))

        img = self.get_display_base_image()
        if img is None:
            return None
        h, w = img.shape[:2]
        if x < 0 or y < 0 or x >= w or y >= h:
            return None
        return x, y

    def image_to_canvas(self, x: float, y: float):
        return (
            self.display_offset_x + x * self.display_scale,
            self.display_offset_y + y * self.display_scale,
        )

    # ======================================================================
    # Polygon interaction: ROI mode + mask mode
    # ======================================================================
    def on_left_down(self, event):
        if self.mode not in {"roi", "mask"}:
            return
        p = self.canvas_to_image(event.x, event.y)
        if p is None:
            return

        # In mask mode we allow vertices anywhere inside the rectangular crop.
        # The final raster mask is clipped by valid_mask, so accidental overlap
        # outside the original ROI polygon will never become a positive label.
        self.current_polygon.append(p)
        self.render()

    def on_right_down(self, _event):
        if self.mode in {"roi", "mask"}:
            self.finish_polygon()

    def finish_polygon(self):
        if self.mode not in {"roi", "mask"}:
            return

        if len(self.current_polygon) < 3:
            if self.current_polygon:
                messagebox.showwarning("Polygon", "Polygon cần ít nhất 3 điểm.")
            return

        if self.mode == "roi":
            self.polygons.append(self.current_polygon.copy())
            self.current_polygon = []
            self.status_var.set(f"Đã có {len(self.polygons)} ROI polygon.")
        else:
            roi = self.rois[self.roi_index]
            roi["mask_polygons"].append(self.current_polygon.copy())
            roi["saved"] = False
            self.current_polygon = []
            self.rebuild_mask_from_polygons(roi)
            self.status_var.set(
                f"Mask ROI {self.roi_index + 1}: {len(roi['mask_polygons'])} polygon Thermal Paste."
            )

        self.render()

    def cancel_current_polygon(self):
        if self.mode in {"roi", "mask"} and self.current_polygon:
            self.current_polygon = []
            self.render()

    def undo_polygon_point(self):
        if self.mode not in {"roi", "mask"}:
            return

        if self.current_polygon:
            self.current_polygon.pop()
        elif self.mode == "roi" and self.polygons:
            self.polygons.pop()
        elif self.mode == "mask" and self.rois:
            roi = self.rois[self.roi_index]
            if roi["mask_polygons"]:
                roi["mask_polygons"].pop()
                roi["saved"] = False
                self.rebuild_mask_from_polygons(roi)
        self.render()

    def delete_last_polygon(self):
        if self.mode not in {"roi", "mask"}:
            return

        if self.current_polygon:
            self.current_polygon = []
        elif self.mode == "roi":
            if self.polygons:
                self.polygons.pop()
        else:
            roi = self.rois[self.roi_index]
            if roi["mask_polygons"]:
                roi["mask_polygons"].pop()
                roi["saved"] = False
                self.rebuild_mask_from_polygons(roi)
        self.render()

    def clear_polygons(self):
        if self.mode != "roi":
            return
        self.current_polygon = []
        self.polygons = []
        self.render()

    def clear_mask_polygons(self):
        if self.mode != "mask" or not self.rois:
            return
        roi = self.rois[self.roi_index]
        self.current_polygon = []
        roi["mask_polygons"] = []
        roi["mask"].fill(0)
        roi["saved"] = False
        self.render()

    # ======================================================================
    # ROI creation
    # ======================================================================
    def confirm_rois(self):
        if self.mode != "roi" or self.source_rgb is None:
            return

        if len(self.current_polygon) >= 3:
            self.finish_polygon()
        elif self.current_polygon:
            messagebox.showwarning("ROI", "Polygon ROI hiện tại chưa đủ 3 điểm.")
            return

        if not self.polygons:
            messagebox.showwarning("ROI", "Hãy tạo ít nhất một polygon ROI.")
            return

        self.rois = []
        H, W = self.source_rgb.shape[:2]

        for polygon in self.polygons:
            pts = np.asarray(polygon, dtype=np.int32)
            x, y, w, h = cv2.boundingRect(pts)
            x = max(0, x)
            y = max(0, y)
            w = min(w, W - x)
            h = min(h, H - y)
            if w <= 1 or h <= 1:
                continue

            crop = self.source_rgb[y:y + h, x:x + w].copy()
            local_pts = pts - np.array([x, y], dtype=np.int32)

            valid_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(valid_mask, [local_pts], 255)

            self.rois.append({
                "crop": crop,
                "mask": np.zeros((h, w), dtype=np.uint8),
                "valid_mask": valid_mask,
                "mask_polygons": [],              # ROI-local coordinates
                "polygon_source": [(int(px), int(py)) for px, py in polygon],
                "bbox": [int(x), int(y), int(w), int(h)],
                "saved": False,
            })

        if not self.rois:
            messagebox.showerror("ROI", "Không tạo được ROI hợp lệ.")
            return

        self.mode = "mask"
        self.roi_index = 0
        self.current_polygon = []
        self.reset_view(render=False)
        self.update_roi_status()
        self.render()

    # ======================================================================
    # Mask polygon mode
    # ======================================================================
    @staticmethod
    def rebuild_mask_from_polygons(roi: dict):
        mask = np.zeros_like(roi["valid_mask"], dtype=np.uint8)
        for polygon in roi["mask_polygons"]:
            if len(polygon) < 3:
                continue
            pts = np.asarray(polygon, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

        # Label is valid only inside the ROI polygon.
        mask[roi["valid_mask"] == 0] = 0
        roi["mask"] = mask

    def previous_roi(self):
        if self.mode != "mask" or not self.rois:
            return
        if self.current_polygon:
            if not messagebox.askyesno("Polygon chưa chốt", "Huỷ polygon mask đang vẽ và quay lại ROI trước?"):
                return
            self.current_polygon = []

        if self.roi_index > 0:
            self.roi_index -= 1
            self.reset_view(render=False)
            self.update_roi_status()
            self.render()

    def save_and_next_roi(self):
        if self.mode != "mask" or not self.rois:
            return

        if len(self.current_polygon) >= 3:
            self.finish_polygon()
        elif self.current_polygon:
            messagebox.showwarning("Mask", "Polygon mask hiện tại chưa đủ 3 điểm. Hãy chốt hoặc huỷ trước.")
            return

        self.save_current_roi()

        if self.roi_index + 1 < len(self.rois):
            self.roi_index += 1
            self.current_polygon = []
            self.reset_view(render=False)
            self.update_roi_status()
            self.render()
        else:
            self.status_var.set("Đã lưu toàn bộ ROI của ảnh. Chuyển ảnh tiếp theo...")
            self.root.after(150, self.load_next_image)

    def update_roi_status(self):
        if not self.rois:
            self.roi_progress_var.set("")
            return
        roi = self.rois[self.roi_index]
        bbox = roi["bbox"]
        self.roi_progress_var.set(
            f"ROI {self.roi_index + 1}/{len(self.rois)} | bbox={bbox[2]}x{bbox[3]} | "
            f"mask polygons={len(roi['mask_polygons'])}"
        )
        self.status_var.set("Mask polygon mode: khoanh pixel thuộc Thermal Paste")

    # ======================================================================
    # Save
    # ======================================================================
    def _sample_base_name(self):
        assert self.current_path is not None
        if self.input_dir is not None:
            try:
                rel = self.current_path.relative_to(self.input_dir)
            except ValueError:
                rel = self.current_path
        else:
            rel = self.current_path
        digest = hashlib.sha1(str(rel).encode("utf-8")).hexdigest()[:8]
        safe_stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.current_path.stem)
        return f"{safe_stem}_{digest}"

    def save_current_roi(self):
        if self.output_dir is None:
            messagebox.showerror("Output", "Chưa có thư mục output.")
            return
        self._prepare_output_dirs()

        roi = self.rois[self.roi_index]
        self.rebuild_mask_from_polygons(roi)

        base = self._sample_base_name()
        roi_name = f"{base}__roi_{self.roi_index + 1:03d}"

        image_path = self.output_dir / "images" / f"{roi_name}.png"
        mask_path = self.output_dir / "masks" / f"{roi_name}.png"
        meta_path = self.output_dir / "meta" / f"{roi_name}.json"

        Image.fromarray(roi["crop"], mode="RGB").save(image_path)
        Image.fromarray(roi["mask"], mode="L").save(mask_path)

        valid_path = None
        if SAVE_VALID_MASK:
            valid_path = self.output_dir / "valid" / f"{roi_name}.png"
            Image.fromarray(roi["valid_mask"], mode="L").save(valid_path)

        x0, y0, _, _ = roi["bbox"]
        mask_polygons_source = [
            [[int(x + x0), int(y + y0)] for x, y in polygon]
            for polygon in roi["mask_polygons"]
        ]

        meta = {
            "source_image": str(self.current_path),
            "roi_image": str(image_path),
            "thermal_paste_mask": str(mask_path),
            "valid_mask": str(valid_path) if valid_path else None,
            "bbox_xywh": roi["bbox"],
            "roi_polygon_source_xy": roi["polygon_source"],
            "thermal_paste_polygons_roi_xy": roi["mask_polygons"],
            "thermal_paste_polygons_source_xy": mask_polygons_source,
            "mask_values": {"background": 0, "thermal_paste": 255},
        }
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        roi["saved"] = True

    # ======================================================================
    # Rendering
    # ======================================================================
    def get_display_base_image(self):
        if self.mode == "roi":
            return self.source_rgb
        if self.mode == "mask" and self.rois:
            return self.rois[self.roi_index]["crop"]
        return None

    @staticmethod
    def make_mask_preview(roi: dict):
        img = roi["crop"].copy().astype(np.float32)
        mask = roi["mask"] > 0
        valid = roi["valid_mask"] > 0

        # Darken outside the ROI polygon so the valid region is visually obvious.
        img[~valid] *= 0.30

        # Red overlay for thermal-paste class.
        overlay = img.copy()
        overlay[mask] = np.array([255, 35, 35], dtype=np.float32)
        img[mask] = 0.42 * img[mask] + 0.58 * overlay[mask]
        return np.clip(img, 0, 255).astype(np.uint8)

    def render(self):
        self.canvas.delete("all")
        base = self.get_display_base_image()
        if base is None:
            return

        if self.mode == "mask":
            display_img = self.make_mask_preview(self.rois[self.roi_index])
        else:
            display_img = base

        ch = max(1, self.canvas.winfo_height())
        cw = max(1, self.canvas.winfo_width())
        h, w = display_img.shape[:2]

        fit_scale = max(min(cw / w, ch / h), 1e-9)
        scale = fit_scale * self.zoom_factor
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        centered_x = (cw - new_w) / 2.0
        centered_y = (ch - new_h) / 2.0

        self.display_scale = scale
        self.display_w = new_w
        self.display_h = new_h
        self.display_offset_x = centered_x + self.pan_x
        self.display_offset_y = centered_y + self.pan_y
        self.zoom_var.set(f"Zoom: {self.zoom_factor * 100:.0f}%")

        # Bilinear is fine for viewing the RGB image. Mask itself is not resized/saved from preview.
        pil = Image.fromarray(display_img, mode="RGB").resize((new_w, new_h), Image.Resampling.BILINEAR)
        self.photo = ImageTk.PhotoImage(pil)
        self.canvas.create_image(
            self.display_offset_x,
            self.display_offset_y,
            anchor=tk.NW,
            image=self.photo,
        )

        if self.mode == "roi":
            # Stored ROI polygons
            for poly in self.polygons:
                pts = []
                for x, y in poly:
                    pts.extend(self.image_to_canvas(x, y))
                if len(pts) >= 6:
                    self.canvas.create_polygon(*pts, outline="#00ff6a", fill="", width=2)

            self._render_current_polygon(color="#ffff00")

        elif self.mode == "mask":
            roi = self.rois[self.roi_index]

            # ROI boundary in local coordinates
            x0, y0, _, _ = roi["bbox"]
            local_roi_poly = [(x - x0, y - y0) for x, y in roi["polygon_source"]]
            pts = []
            for x, y in local_roi_poly:
                pts.extend(self.image_to_canvas(x, y))
            if len(pts) >= 6:
                self.canvas.create_polygon(*pts, outline="#ffe600", fill="", width=2)

            # Saved Thermal Paste mask polygons
            for poly in roi["mask_polygons"]:
                pts = []
                for x, y in poly:
                    pts.extend(self.image_to_canvas(x, y))
                if len(pts) >= 6:
                    self.canvas.create_polygon(*pts, outline="#ff3b3b", fill="", width=2)

            self._render_current_polygon(color="#00e5ff")

    def _render_current_polygon(self, color: str):
        if not self.current_polygon:
            return

        pts = []
        for x, y in self.current_polygon:
            cx, cy = self.image_to_canvas(x, y)
            pts.extend((cx, cy))
            r = 3
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

        if len(pts) >= 4:
            self.canvas.create_line(*pts, fill=color, width=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = Entropy1GTLabeler(root)
    root.mainloop()