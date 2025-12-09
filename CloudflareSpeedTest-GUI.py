import sys
import os
import json
import subprocess
import ctypes
from functools import partial
from PyQt5 import QtWidgets, QtGui, QtCore

def resource_path(relative_path):
    """获取 PyInstaller 打包后资源文件路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

APP_ICON = resource_path("app.ico")
CFST_EXE = "cfst.exe"
IP_FILE_NAME = "ip.txt"
SAVED_SETTINGS_FILE = "saved_settings.json"
APP_USER_MODEL_ID = "com.example.cloudflarespeedtest"

def _set_windows_appid(appid):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except Exception:
        pass


if sys.platform.startswith("win"):
    _set_windows_appid(APP_USER_MODEL_ID)

class MainWin(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CloudflareSpeedTest_GUI -- 小琳解说")

        # 图标（修复：PyInstaller 下也能找到）
        if os.path.exists(APP_ICON):
            self.setWindowIcon(QtGui.QIcon(APP_ICON))
        else:
            self.setWindowIcon(QtGui.QIcon(resource_path("app.ico")))

        self.setFont(QtGui.QFont("Microsoft YaHei", 10))
        self.resize(500, 520)

        self._build_ui()
        self._load_saved_settings_list()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        params = [
            ("-n", "200", "延迟线程 1-1000"),
            ("-t", "4", "延迟次数"),
            ("-dn", "10", "下载数量"),
            ("-dt", "10", "下载时间(秒)"),
            ("-tp", "443", "端口"),
            ("-url", "https://cf.xiu2.xyz/url", "测速地址"),
            ("-httping", "", "HTTPing 模式 (勾选启用)"),
            ("-httping-code", "200", "HTTP 有效状态码"),
            ("-cfcolo", "HKG,KHH,NRT,LAX", "地区码, HTTPing 模式可用"),
            ("-tl", "9999", "平均延迟上限(ms)"),
            ("-tll", "0", "平均延迟下限(ms)"),
            ("-tlr", "1.00", "丢包上限 0.00-1.00"),
            ("-sl", "0", "下载速度下限 MB/s"),
            ("-p", "10", "显示结果数量"),
            ("-f", "ip.txt", "IP 段文件"),
            ("-ip", "", "指定 IP 段"),
            ("-o", "result.csv", "输出文件"),
            ("-dd", "", "禁用下载测速 (勾选启用)"),
            ("-allip", "", "测速全部 IP (勾选启用)")
        ]

        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)

        self.controls = {}
        row = 0

        for key, default, hint in params:
            cb = QtWidgets.QCheckBox(key)
            cb.setChecked(False)

            if key == "-n":
                widget = QtWidgets.QSpinBox()
                widget.setRange(1, 1000)
                try:
                    widget.setValue(int(default))
                except Exception:
                    widget.setValue(200)
                widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                widget.setEnabled(False)
            else:
                widget = QtWidgets.QLineEdit(default)
                if default == "":
                    widget.setPlaceholderText(hint)
                widget.setEnabled(False)
                widget.setStyleSheet("QLineEdit:disabled { color: gray; }")

            lbl = QtWidgets.QLabel(hint)
            cb.stateChanged.connect(partial(self._on_checkbox_toggled, key))

            grid.addWidget(cb, row, 0)
            grid.addWidget(widget, row, 1)
            grid.addWidget(lbl, row, 2)

            self.controls[key] = (cb, widget)
            row += 1

        main_layout.addLayout(grid)

        save_load_layout = QtWidgets.QGridLayout()
        save_load_layout.setColumnStretch(1, 1)

        save_label = QtWidgets.QLabel("保存设置名称")
        self.save_name_edit = QtWidgets.QLineEdit()
        self.save_name_edit.setPlaceholderText("填写保存设置名称")
        self.save_btn = QtWidgets.QPushButton("保存设置")

        load_label = QtWidgets.QLabel("已保存设置")
        self.load_combo = QtWidgets.QComboBox()
        self.load_combo.setEditable(False)

        sp = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.save_name_edit.setSizePolicy(sp)
        self.load_combo.setSizePolicy(sp)

        self.load_btn = QtWidgets.QPushButton("加载设置")
        self.delete_btn = QtWidgets.QPushButton("删除已保存")

        load_btns_layout = QtWidgets.QHBoxLayout()
        load_btns_layout.addWidget(self.load_btn)
        load_btns_layout.addWidget(self.delete_btn)
        load_btns_layout.addStretch()

        save_load_layout.addWidget(save_label, 0, 0)
        save_load_layout.addWidget(self.save_name_edit, 0, 1)
        save_load_layout.addWidget(self.save_btn, 0, 2)

        save_load_layout.addWidget(load_label, 1, 0)
        save_load_layout.addWidget(self.load_combo, 1, 1)
        save_load_layout.addLayout(load_btns_layout, 1, 2)

        # 运行按钮
        self.run_btn = QtWidgets.QPushButton("运行\n测速")
        btn_size = 88
        self.run_btn.setFixedSize(btn_size, btn_size)

        font = QtGui.QFont("Microsoft YaHei", 14)
        font.setBold(True)
        self.run_btn.setFont(font)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)

        save_load_layout.addWidget(
            self.run_btn, 0, 3, 2, 1, alignment=QtCore.Qt.AlignCenter
        )

        main_layout.addLayout(save_load_layout)

        self.save_btn.clicked.connect(self._on_save_clicked)
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.run_btn.clicked.connect(self._on_run_clicked)

    def _on_checkbox_toggled(self, key, state):
        cb, widget = self.controls[key]
        enabled = (state == 2)
        widget.setEnabled(enabled)
        if isinstance(widget, QtWidgets.QLineEdit):
            if enabled:
                widget.setStyleSheet("QLineEdit { color: black; }")
            else:
                widget.setStyleSheet("QLineEdit:disabled { color: gray; }")

    def _load_saved_settings_list(self):
        self.load_combo.clear()
        if not os.path.exists(SAVED_SETTINGS_FILE):
            return
        try:
            with open(SAVED_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            names = sorted(data.keys())
            self.load_combo.addItems(names)
        except Exception:
            pass

    def _read_saved_settings(self):
        if not os.path.exists(SAVED_SETTINGS_FILE):
            return {}
        try:
            with open(SAVED_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_saved_settings(self, data):
        try:
            with open(SAVED_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def _on_save_clicked(self):
        name = self.save_name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "保存失败", "请填写保存设置的名称。")
            return

        settings = {}
        for k, (cb, widget) in self.controls.items():
            if isinstance(widget, QtWidgets.QSpinBox):
                val = widget.value()
            else:
                val = widget.text()
            settings[k] = [cb.isChecked(), val]

        all_saved = self._read_saved_settings()
        all_saved[name] = settings

        ok = self._write_saved_settings(all_saved)
        if ok:
            QtWidgets.QMessageBox.information(self, "保存成功", f"设置已保存为: {name}")
            self._load_saved_settings_list()
            idx = self.load_combo.findText(name)
            if idx >= 0:
                self.load_combo.setCurrentIndex(idx)
        else:
            QtWidgets.QMessageBox.warning(self, "保存失败", "写入保存文件失败。")

    def _on_load_clicked(self):
        name = self.load_combo.currentText().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "加载失败", "请先选择一个已保存的设置名称。")
            return

        all_saved = self._read_saved_settings()
        if name not in all_saved:
            QtWidgets.QMessageBox.warning(self, "加载失败", "所选设置不存在或已被删除。")
            self._load_saved_settings_list()
            return

        settings = all_saved[name]

        for k, (cb, widget) in self.controls.items():
            if k in settings:
                checked, val = settings[k]
                cb.setChecked(bool(checked))
                if isinstance(widget, QtWidgets.QSpinBox):
                    try:
                        widget.setValue(int(val))
                    except Exception:
                        pass
                    widget.setEnabled(bool(checked))
                else:
                    widget.setText(str(val))
                    widget.setEnabled(bool(checked))
                    widget.setStyleSheet(
                        "QLineEdit { color: black; }" if widget.isEnabled() else "QLineEdit:disabled { color: gray; }"
                    )

        QtWidgets.QMessageBox.information(self, "加载成功", f"已加载设置: {name}")

    def _on_delete_clicked(self):
        name = self.load_combo.currentText().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "删除失败", "请先选择一个已保存的设置名称。")
            return

        all_saved = self._read_saved_settings()
        if name not in all_saved:
            QtWidgets.QMessageBox.warning(self, "删除失败", "所选设置不存在。")
            self._load_saved_settings_list()
            return

        reply = QtWidgets.QMessageBox.question(
            self, "确认删除",
            f"确定要删除已保存设置: {name} ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        del all_saved[name]
        ok = self._write_saved_settings(all_saved)
        if ok:
            QtWidgets.QMessageBox.information(self, "删除成功", f"已删除: {name}")
            self._load_saved_settings_list()
        else:
            QtWidgets.QMessageBox.warning(self, "删除失败", "删除时写入文件失败。")

    def _find_file_case_insensitive(self, target_name):
        target_lower = target_name.lower()
        for entry in os.listdir("."):
            if entry.lower() == target_lower:
                return entry
        return None

    def _build_cmd_list(self, exe_name):
        cmd_list = [exe_name]

        for k, (cb, widget) in self.controls.items():
            if not cb.isChecked():
                continue

            if k == "-n":
                cmd_list.append(k)
                cmd_list.append(str(widget.value()))
                continue

            if k in ("-httping", "-dd", "-allip"):
                cmd_list.append(k)
                continue

            val = widget.text().strip()
            if val == "":
                continue

            cmd_list.append(k)
            cmd_list.append(val)

        return cmd_list

    def _on_run_clicked(self):
        cfst_actual = self._find_file_case_insensitive(CFST_EXE)
        ip_actual = self._find_file_case_insensitive(IP_FILE_NAME)

        missing = []
        if not cfst_actual:
            missing.append(CFST_EXE)
        if not ip_actual:
            missing.append(IP_FILE_NAME)

        if missing:
            missing_str = "，".join(missing)
            QtWidgets.QMessageBox.warning(
                self, "文件缺失",
                f"未找到必要文件: {missing_str}\n请将缺失文件放在程序同目录后重试。"
            )
            return

        cmd_list = self._build_cmd_list(cfst_actual)
        if not cmd_list:
            cmd_list = [cfst_actual]

        try:
            if os.name == "nt":
                CREATE_NEW_CONSOLE = 0x00000010
                subprocess.Popen(cmd_list, creationflags=CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(cmd_list)
        except Exception:
            return

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # 全局图标
    app.setWindowIcon(QtGui.QIcon(APP_ICON))

    w = MainWin()
    w.show()
    sys.exit(app.exec_())