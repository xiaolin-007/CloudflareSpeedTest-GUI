import sys
import os
import json
import subprocess
import ctypes
from PyQt5 import QtWidgets, QtGui, QtCore

CONFIG_FILE = "cfst_gui_presets_ext.json"
ICON_FILE = "app.ico"
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def strip_spinbox_arrows(widget):
    try:
        widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
    except Exception:
        pass

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CFST_GUI高阶版 --小琳解说")
        self.resize(600, 750)
        self.setMinimumSize(550, 600)

        icon_path = resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
            myappid = 'mycompany.cfst.gui.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        self.setStyleSheet("""
            QWidget { 
                background-color: #f3f4f6; 
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif; 
                font-size: 13px;
                color: #1f2937;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
                color: #2563eb;
                font-size: 12px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 22px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3b82f6;
            }
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
                background: #f9fafb;
                color: #9ca3af;
                border: 1px solid #e5e7eb;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 5px 10px;
                color: #374151;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #f3f4f6; }
            QScrollArea { border: none; background: transparent; }
        """)

        self.process = None
        self.poll_timer = QtCore.QTimer(self)
        self.poll_timer.setInterval(500)
        self.poll_timer.timeout.connect(self._poll_process)
        self.presets = {}

        self._build_ui()
        self.load_presets()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        top_bar = QtWidgets.QHBoxLayout()
        note = QtWidgets.QLabel("💡 提示：cfst.exe 等相关文件必须与本程序在同一目录")
        note.setStyleSheet("color: #6b7280; font-style: italic; background: transparent;")
        top_bar.addWidget(note)
        main_layout.addLayout(top_bar)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(content_widget)
        self.content_layout.setSpacing(12)
        self.content_layout.setContentsMargins(0,0,0,0)
        scroll.setWidget(content_widget)
        
        self._create_group_performance()
        self._create_group_target()
        self._create_group_filter()
        self._create_group_io()

        main_layout.addWidget(scroll, 1)

        preset_container = QtWidgets.QFrame()
        preset_container.setStyleSheet("background: #ffffff; border-radius: 6px; border: 1px solid #e5e7eb;")
        preset_layout = QtWidgets.QHBoxLayout(preset_container)
        preset_layout.setContentsMargins(8, 8, 8, 8)
        
        self.preset_name = QtWidgets.QLineEdit()
        self.preset_name.setPlaceholderText("预设名称")
        self.preset_name.setMinimumWidth(200)
        
        self.btn_save = QtWidgets.QPushButton("设置保存")
        self.btn_save.setFixedWidth(80)
        self.btn_save.setFixedHeight(30)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
                color: white; font-size: 14px; border: none; border-radius: 6px;
                padding: 6px 12px; font-weight: 600;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); }
            QPushButton:disabled { background: #d1d5db; color: #9ca3af; }
        """)
        self.btn_save.clicked.connect(self.save_preset)

        self.combo_presets = QtWidgets.QComboBox()
        self.combo_presets.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        self.btn_load = QtWidgets.QPushButton("设置加载")
        self.btn_load.setFixedWidth(80)
        self.btn_load.setFixedHeight(30)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fb923c, stop:1 #f97316);
                color: white; font-size: 14px; border: none; border-radius: 6px;
                padding: 6px 12px; font-weight: 600;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f97316, stop:1 #ea580c); }
            QPushButton:disabled { background: #d1d5db; color: #9ca3af; }
        """)
        self.btn_load.clicked.connect(self.load_selected_preset)

        preset_layout.addWidget(self.preset_name, 2)
        preset_layout.addWidget(self.btn_save, 0)
        preset_layout.addSpacing(10)
        preset_layout.addWidget(self.combo_presets, 3)
        preset_layout.addWidget(self.btn_load, 0)
        
        main_layout.addWidget(preset_container)

        btn_layout = QtWidgets.QHBoxLayout()
        
        self.btn_run = QtWidgets.QPushButton("运行测速")
        self.btn_run.setFixedHeight(48)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb);
                color: white; font-size: 16px; border: none; border-radius: 6px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8); }
            QPushButton:disabled { background: #d1d5db; color: #9ca3af; }
        """)
        self.btn_run.clicked.connect(self.on_run)

        self.btn_stop = QtWidgets.QPushButton("停止")
        self.btn_stop.setFixedHeight(48)
        self.btn_stop.setFixedWidth(100)
        self.btn_stop.setStyleSheet("""
            QPushButton { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; border-radius: 6px;}
            QPushButton:hover { background: #fecaca; }
            QPushButton:disabled { background: #f3f4f6; color: #d1d5db; border: 1px solid #e5e7eb; }
        """)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_run)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(self.btn_stop)
        main_layout.addLayout(btn_layout)

    def _prepare_widget(self, widget):
        if isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            strip_spinbox_arrows(widget)
        widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        widget.setMinimumWidth(80)

    def _add_grid_row(self, layout, row, check, widget, hint):
        self._prepare_widget(widget)
        layout.addWidget(check, row, 0)
        layout.addWidget(widget, row, 1)
        lbl = QtWidgets.QLabel(hint)
        lbl.setStyleSheet("color: #6b7280; font-size: 12px;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl, row, 2)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)

    def _create_group_performance(self):
        group = QtWidgets.QGroupBox("并发与性能")
        layout = QtWidgets.QGridLayout(group)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(10)
        self.content_layout.addWidget(group)

        self.chk_n = QtWidgets.QCheckBox("-n (延迟测速线程)")
        self.spin_n = QtWidgets.QSpinBox(); self.spin_n.setRange(1, 1000); self.spin_n.setValue(200); self.spin_n.setEnabled(False)
        self.chk_n.stateChanged.connect(lambda s: self.spin_n.setEnabled(s == 2))
        self._add_grid_row(layout, 0, self.chk_n, self.spin_n, "默认 200，范围 1-1000")

        self.chk_t = QtWidgets.QCheckBox("-t (延迟测速次数)")
        self.spin_t = QtWidgets.QSpinBox(); self.spin_t.setRange(1, 100); self.spin_t.setValue(4); self.spin_t.setEnabled(False)
        self.chk_t.stateChanged.connect(lambda s: self.spin_t.setEnabled(s == 2))
        self._add_grid_row(layout, 1, self.chk_t, self.spin_t, "默认 4 次")

        self.chk_dn = QtWidgets.QCheckBox("-dn (下载测速数量)")
        self.spin_dn = QtWidgets.QSpinBox(); self.spin_dn.setRange(0, 1000); self.spin_dn.setValue(10); self.spin_dn.setEnabled(False)
        self.chk_dn.stateChanged.connect(lambda s: self.spin_dn.setEnabled(s == 2))
        self._add_grid_row(layout, 2, self.chk_dn, self.spin_dn, "默认 10")

        self.chk_dt = QtWidgets.QCheckBox("-dt (下载测速时间 秒)")
        self.spin_dt = QtWidgets.QSpinBox(); self.spin_dt.setRange(1, 3600); self.spin_dt.setValue(10); self.spin_dt.setEnabled(False)
        self.chk_dt.stateChanged.connect(lambda s: self.spin_dt.setEnabled(s == 2))
        self._add_grid_row(layout, 3, self.chk_dt, self.spin_dt, "默认 10 秒")

    def _create_group_target(self):
        group = QtWidgets.QGroupBox("模式与目标")
        layout = QtWidgets.QGridLayout(group)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(10)
        self.content_layout.addWidget(group)

        self.chk_tp = QtWidgets.QCheckBox("-tp (指定测速端口)")
        self.spin_tp = QtWidgets.QSpinBox(); self.spin_tp.setRange(1, 65535); self.spin_tp.setValue(443); self.spin_tp.setEnabled(False)
        self.chk_tp.stateChanged.connect(lambda s: self.spin_tp.setEnabled(s == 2))
        self._add_grid_row(layout, 0, self.chk_tp, self.spin_tp, "默认 443")

        self.chk_url = QtWidgets.QCheckBox("-url (测速地址)")
        self.le_url = QtWidgets.QLineEdit(); self.le_url.setPlaceholderText("https://..."); self.le_url.setEnabled(False)
        self.chk_url.stateChanged.connect(lambda s: self.le_url.setEnabled(s == 2))
        self._add_grid_row(layout, 1, self.chk_url, self.le_url, "用于 HTTPing/TCPing 的地址")

        self.chk_httping = QtWidgets.QCheckBox("-httping (使用 HTTP 测速模式)")
        layout.addWidget(self.chk_httping, 2, 0, 1, 3)

        self.chk_httping_code = QtWidgets.QCheckBox("-httping-code")
        self.le_httping_code = QtWidgets.QLineEdit(); self.le_httping_code.setPlaceholderText("200"); self.le_httping_code.setEnabled(False)
        self.chk_httping_code.stateChanged.connect(lambda s: self.le_httping_code.setEnabled(s == 2))
        self._add_grid_row(layout, 3, self.chk_httping_code, self.le_httping_code, "默认 200 301 302")

        self.chk_cfcolo = QtWidgets.QCheckBox("-cfcolo (匹配指定地区)")
        self.le_cfcolo = QtWidgets.QLineEdit(); self.le_cfcolo.setPlaceholderText("HKG,LAX..."); self.le_cfcolo.setEnabled(False)
        self.chk_cfcolo.stateChanged.connect(lambda s: self.le_cfcolo.setEnabled(s == 2))
        self._add_grid_row(layout, 4, self.chk_cfcolo, self.le_cfcolo, "逗号分隔，HTTPing 模式可用")

    def _create_group_filter(self):
        group = QtWidgets.QGroupBox("过滤条件")
        layout = QtWidgets.QGridLayout(group)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(10)
        self.content_layout.addWidget(group)

        self.chk_tl = QtWidgets.QCheckBox("-tl (平均延迟上限)")
        self.spin_tl = QtWidgets.QSpinBox(); self.spin_tl.setRange(0, 99999); self.spin_tl.setValue(9999); self.spin_tl.setEnabled(False)
        self.chk_tl.stateChanged.connect(lambda s: self.spin_tl.setEnabled(s == 2))
        self._add_grid_row(layout, 0, self.chk_tl, self.spin_tl, "默认 9999 ms")

        self.chk_tll = QtWidgets.QCheckBox("-tll (平均延迟下限)")
        self.spin_tll = QtWidgets.QSpinBox(); self.spin_tll.setRange(0, 99999); self.spin_tll.setValue(0); self.spin_tll.setEnabled(False)
        self.chk_tll.stateChanged.connect(lambda s: self.spin_tll.setEnabled(s == 2))
        self._add_grid_row(layout, 1, self.chk_tll, self.spin_tll, "默认 0 ms")

        self.chk_tlr = QtWidgets.QCheckBox("-tlr (丢包几率上限)")
        self.dspin_tlr = QtWidgets.QDoubleSpinBox(); self.dspin_tlr.setRange(0.0, 1.0); self.dspin_tlr.setSingleStep(0.01); self.dspin_tlr.setValue(1.0); self.dspin_tlr.setEnabled(False)
        self.chk_tlr.stateChanged.connect(lambda s: self.dspin_tlr.setEnabled(s == 2))
        self._add_grid_row(layout, 2, self.chk_tlr, self.dspin_tlr, "默认 1.00")

        self.chk_sl = QtWidgets.QCheckBox("-sl (下载速度下限)")
        self.dspin_sl = QtWidgets.QDoubleSpinBox(); self.dspin_sl.setRange(0.0, 10000.0); self.dspin_sl.setSingleStep(0.1); self.dspin_sl.setValue(0.0); self.dspin_sl.setEnabled(False)
        self.chk_sl.stateChanged.connect(lambda s: self.dspin_sl.setEnabled(s == 2))
        self._add_grid_row(layout, 3, self.chk_sl, self.dspin_sl, "默认 0.00 MB/s")

    def _create_group_io(self):
        group = QtWidgets.QGroupBox("输入与输出")
        layout = QtWidgets.QGridLayout(group)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(10)
        self.content_layout.addWidget(group)

        self.chk_p = QtWidgets.QCheckBox("-p (显示结果数量)")
        self.spin_p = QtWidgets.QSpinBox(); self.spin_p.setRange(0, 10000); self.spin_p.setValue(10); self.spin_p.setEnabled(False)
        self.chk_p.stateChanged.connect(lambda s: self.spin_p.setEnabled(s == 2))
        self._add_grid_row(layout, 0, self.chk_p, self.spin_p, "默认 10，0 为不显示直接退出")

        self.chk_o = QtWidgets.QCheckBox("-o (写入结果文件)")
        self.le_o = QtWidgets.QLineEdit(); self.le_o.setPlaceholderText("result.csv"); self.le_o.setEnabled(False)
        self.chk_o.stateChanged.connect(lambda s: self.le_o.setEnabled(s == 2))
        self._add_grid_row(layout, 1, self.chk_o, self.le_o, "留空或设置为 \"\" 表示不写入文件")

        self.chk_f = QtWidgets.QCheckBox("-f (IP段数据文件)")
        self.le_f = QtWidgets.QLineEdit(); self.le_f.setPlaceholderText("ip.txt"); self.le_f.setEnabled(False)
        self.chk_f.stateChanged.connect(lambda s: self.le_f.setEnabled(s == 2))
        self._add_grid_row(layout, 2, self.chk_f, self.le_f, "如含空格请加引号")

        self.chk_ip = QtWidgets.QCheckBox("-ip (指定 IP 段 数据)")
        self.le_ip = QtWidgets.QLineEdit(); self.le_ip.setPlaceholderText("1.1.1.1/24,..."); self.le_ip.setEnabled(False)
        self.chk_ip.stateChanged.connect(lambda s: self.le_ip.setEnabled(s == 2))
        self._add_grid_row(layout, 3, self.chk_ip, self.le_ip, "逗号分隔")

        self.chk_dd = QtWidgets.QCheckBox("-dd (禁用下载测速)")
        layout.addWidget(self.chk_dd, 4, 0, 1, 3)
        self.chk_dd_label = QtWidgets.QLabel("禁用下载测速后按延迟排序")
        self.chk_dd_label.setStyleSheet("color: #6b7280; font-size: 12px; margin-left: 20px;")
        layout.addWidget(self.chk_dd_label, 5, 0, 1, 3)

        self.chk_allip = QtWidgets.QCheckBox("-allip (测速全部的 IP)")
        layout.addWidget(self.chk_allip, 6, 0, 1, 3)
        self.chk_allip_label = QtWidgets.QLabel("对 IP 段中每个 IPv4 进行测速")
        self.chk_allip_label.setStyleSheet("color: #6b7280; font-size: 12px; margin-left: 20px;")
        layout.addWidget(self.chk_allip_label, 7, 0, 1, 3)

    def find_default_exe(self):
        cand = os.path.join(os.getcwd(), "cfst.exe")
        return cand if os.path.exists(cand) else None

    def build_args(self):
        args = []
        if self.chk_n.isChecked(): args += ["-n", str(self.spin_n.value())]
        if self.chk_t.isChecked(): args += ["-t", str(self.spin_t.value())]
        if self.chk_dn.isChecked(): args += ["-dn", str(self.spin_dn.value())]
        if self.chk_dt.isChecked(): args += ["-dt", str(self.spin_dt.value())]
        if self.chk_tp.isChecked(): args += ["-tp", str(self.spin_tp.value())]
        if self.chk_url.isChecked() and self.le_url.text().strip(): args += ["-url", self.le_url.text().strip()]
        if self.chk_httping.isChecked(): args += ["-httping"]
        if self.chk_httping_code.isChecked() and self.le_httping_code.text().strip(): args += ["-httping-code", self.le_httping_code.text().strip()]
        if self.chk_cfcolo.isChecked() and self.le_cfcolo.text().strip(): args += ["-cfcolo", self.le_cfcolo.text().strip()]
        if self.chk_tl.isChecked(): args += ["-tl", str(self.spin_tl.value())]
        if self.chk_tll.isChecked(): args += ["-tll", str(self.spin_tll.value())]
        if self.chk_tlr.isChecked(): args += ["-tlr", f"{self.dspin_tlr.value():.2f}"]
        if self.chk_sl.isChecked(): args += ["-sl", f"{self.dspin_sl.value():.2f}"]
        if self.chk_p.isChecked(): args += ["-p", str(self.spin_p.value())]
        if self.chk_f.isChecked() and self.le_f.text().strip(): args += ["-f", self.le_f.text().strip()]
        if self.chk_ip.isChecked() and self.le_ip.text().strip(): args += ["-ip", self.le_ip.text().strip()]
        if self.chk_o.isChecked():
            val = self.le_o.text()
            if val == "": args += ["-o", ""]
            elif val.strip(): args += ["-o", val.strip()]
        if self.chk_dd.isChecked(): args += ["-dd"]
        if self.chk_allip.isChecked(): args += ["-allip"]
        return args

    def validate_before_run(self):
        if self.chk_n.isChecked():
            v = self.spin_n.value()
            if v < 1 or v > 1000:
                return False, "-n 必须在 1 到 1000 之间"
        if self.chk_httping.isChecked() and not (self.chk_url.isChecked() and self.le_url.text().strip()):
            return False, "启用 -httping 时建议设置 -url 参数"
        return True, ""

    def on_run(self):
        ok, msg = self.validate_before_run()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "参数校验失败", msg)
            return

        exe_path = self.find_default_exe()
        if not exe_path:
            QtWidgets.QMessageBox.warning(self, "错误", "未在当前目录找到 cfst.exe")
            return

        args = self.build_args()
        try:
            self.process = subprocess.Popen([exe_path] + args, cwd=os.path.dirname(exe_path) or None, creationflags=CREATE_NEW_CONSOLE)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "启动失败", f"无法启动程序: {e}")
            self.process = None
            return

        self.btn_run.setEnabled(False)
        self.btn_run.setText("运行中...")
        self.btn_stop.setEnabled(True)
        self.poll_timer.start()

    def _poll_process(self):
        running = False
        if self.process:
            if self.process.poll() is None:
                running = True
            else:
                self.process = None
        if not running:
            self.poll_timer.stop()
            self.btn_run.setEnabled(True)
            self.btn_run.setText("运行测速")
            self.btn_stop.setEnabled(False)

    def on_stop(self):
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
        except Exception:
            pass
        self.process = None
        self.btn_stop.setEnabled(False)
        self.btn_run.setEnabled(True)
        self.btn_run.setText("运行测速")
        self.poll_timer.stop()

    def load_presets(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.presets = json.load(f)
            except Exception:
                self.presets = {}
        else:
            self.presets = {}
        self.refresh_preset_combo()

    def refresh_preset_combo(self):
        self.combo_presets.clear()
        self.combo_presets.addItems(sorted(self.presets.keys()))

    def save_preset(self):
        name = self.preset_name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "错误", "请填写预设名")
            return
        preset = {
            "n_enabled": self.chk_n.isChecked(), "n_value": self.spin_n.value(),
            "t_enabled": self.chk_t.isChecked(), "t_value": self.spin_t.value(),
            "dn_enabled": self.chk_dn.isChecked(), "dn_value": self.spin_dn.value(),
            "dt_enabled": self.chk_dt.isChecked(), "dt_value": self.spin_dt.value(),
            "tp_enabled": self.chk_tp.isChecked(), "tp_value": self.spin_tp.value(),
            "url_enabled": self.chk_url.isChecked(), "url_value": self.le_url.text(),
            "httping": self.chk_httping.isChecked(),
            "httping_code_enabled": self.chk_httping_code.isChecked(), "httping_code": self.le_httping_code.text(),
            "cfcolo_enabled": self.chk_cfcolo.isChecked(), "cfcolo": self.le_cfcolo.text(),
            "tl_enabled": self.chk_tl.isChecked(), "tl_value": self.spin_tl.value(),
            "tll_enabled": self.chk_tll.isChecked(), "tll_value": self.spin_tll.value(),
            "tlr_enabled": self.chk_tlr.isChecked(), "tlr_value": self.dspin_tlr.value(),
            "sl_enabled": self.chk_sl.isChecked(), "sl_value": self.dspin_sl.value(),
            "p_enabled": self.chk_p.isChecked(), "p_value": self.spin_p.value(),
            "f_enabled": self.chk_f.isChecked(), "f_value": self.le_f.text(),
            "ip_enabled": self.chk_ip.isChecked(), "ip_value": self.le_ip.text(),
            "o_enabled": self.chk_o.isChecked(), "o_value": self.le_o.text(),
            "dd": self.chk_dd.isChecked(), "allip": self.chk_allip.isChecked()
        }
        self.presets[name] = preset
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.presets, f, ensure_ascii=False, indent=2)
        self.refresh_preset_combo()
        QtWidgets.QMessageBox.information(self, "已保存", f"预设 {name} 已保存")

    def load_selected_preset(self):
        name = self.combo_presets.currentText()
        if not name: return
        p = self.presets.get(name)
        if not p: return
        
        self.chk_n.setChecked(p.get("n_enabled", False)); self.spin_n.setValue(p.get("n_value", 200))
        self.chk_t.setChecked(p.get("t_enabled", False)); self.spin_t.setValue(p.get("t_value", 4))
        self.chk_dn.setChecked(p.get("dn_enabled", False)); self.spin_dn.setValue(p.get("dn_value", 10))
        self.chk_dt.setChecked(p.get("dt_enabled", False)); self.spin_dt.setValue(p.get("dt_value", 10))
        self.chk_tp.setChecked(p.get("tp_enabled", False)); self.spin_tp.setValue(p.get("tp_value", 443))
        self.chk_url.setChecked(p.get("url_enabled", False)); self.le_url.setText(p.get("url_value", ""))
        self.chk_httping.setChecked(p.get("httping", False))
        self.chk_httping_code.setChecked(p.get("httping_code_enabled", False)); self.le_httping_code.setText(p.get("httping_code", ""))
        self.chk_cfcolo.setChecked(p.get("cfcolo_enabled", False)); self.le_cfcolo.setText(p.get("cfcolo", ""))
        self.chk_tl.setChecked(p.get("tl_enabled", False)); self.spin_tl.setValue(p.get("tl_value", 9999))
        self.chk_tll.setChecked(p.get("tll_enabled", False)); self.spin_tll.setValue(p.get("tll_value", 0))
        self.chk_tlr.setChecked(p.get("tlr_enabled", False)); self.dspin_tlr.setValue(p.get("tlr_value", 1.0))
        self.chk_sl.setChecked(p.get("sl_enabled", False)); self.dspin_sl.setValue(p.get("sl_value", 0.0))
        self.chk_p.setChecked(p.get("p_enabled", False)); self.spin_p.setValue(p.get("p_value", 10))
        self.chk_f.setChecked(p.get("f_enabled", False)); self.le_f.setText(p.get("f_value", ""))
        self.chk_ip.setChecked(p.get("ip_enabled", False)); self.le_ip.setText(p.get("ip_value", ""))
        self.chk_o.setChecked(p.get("o_enabled", False)); self.le_o.setText(p.get("o_value", ""))
        self.chk_dd.setChecked(p.get("dd", False)); self.chk_allip.setChecked(p.get("allip", False))
        
        QtWidgets.QMessageBox.information(self, "已加载", f"预设 {name} 已加载")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    font = QtGui.QFont("Microsoft YaHei", 10)
    font.setStyleStrategy(QtGui.QFont.PreferAntialias)
    app.setFont(font)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
