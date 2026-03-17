# -*- coding: utf-8 -*-

from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(900, 600)  # 初始窗口大小
        Form.setStyleSheet("background-color: #FFFFFF; font-family: 'Microsoft YaHei', 'Segoe UI', Arial;")  # 設置亮色背景和字體

        # 主布局
        self.main_layout = QtWidgets.QVBoxLayout(Form)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 使用 QSplitter 分割用戶列表和聊天區域
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E5E5E5;
                width: 1px;
            }
        """)

        # 左側用戶列表區域
        self.user_list_frame = QtWidgets.QFrame(self.splitter)
        self.user_list_frame.setStyleSheet(
            "background-color: #FFFFFF; border: none;"
        )
        self.user_list_layout = QtWidgets.QVBoxLayout(self.user_list_frame)
        self.user_list_layout.setContentsMargins(16, 16, 16, 16)

        self.user_label = QtWidgets.QLabel(self.user_list_frame)
        self.user_label.setText("在線用戶 (人數: 1)")
        self.user_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #666;")
        self.user_list_layout.addWidget(self.user_label)

        self.user_list = QtWidgets.QListWidget(self.user_list_frame)
        self.user_list.setStyleSheet(
            "background-color: #FFFFFF; border: none; font-size: 15px; color: #333333; padding: 8px;"
        )
        self.user_list_layout.addWidget(self.user_list)

        # 右側聊天區域
        self.chat_frame = QtWidgets.QFrame(self.splitter)
        self.chat_frame.setStyleSheet("background-color: #FFFFFF; border: none;")
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_frame)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(0)

        # 使用 QScrollArea 替代 QTextBrowser 以支持自定义圆角消息气泡
        self.scrollArea = QtWidgets.QScrollArea(self.chat_frame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet(
            "background-color: #F0F2F5; border: none;"
        )
        self.chat_layout.addWidget(self.scrollArea)

        # 创建 content widget 作为滚动区域的内容
        self.scrollContent = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.scrollContent)
        self.scrollLayout = QtWidgets.QVBoxLayout(self.scrollContent)
        self.scrollLayout.setContentsMargins(16, 16, 16, 16)
        self.scrollLayout.setSpacing(8)
        self.scrollLayout.addStretch()  # 添加弹性空间，将消息推到顶部

        # 輸入框区域容器
        self.input_container = QtWidgets.QFrame(self.chat_frame)
        self.input_container.setStyleSheet("background-color: #FFFFFF; border-top: 1px solid #E5E5E5;")
        self.input_container_layout = QtWidgets.QVBoxLayout(self.input_container)
        self.input_container_layout.setContentsMargins(16, 12, 16, 12)
        
        self.input_layout = QtWidgets.QHBoxLayout()
        self.input_layout.setSpacing(8)

        # 文件按钮（发送图片/视频）
        self.file_button = QtWidgets.QPushButton(self.chat_frame)
        self.file_button.setText("📎")
        self.file_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #666;
                font-size: 20px;
                border-radius: 20px;
                padding: 10px 14px;
                border: 1px solid #E5E5E5;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                color: #333;
            }
            QPushButton:pressed {
                background-color: #EBEBEB;
            }
        """)
        self.file_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)
        self.input_layout.addWidget(self.file_button)

        # 輸入框
        self.lineEdit = QtWidgets.QLineEdit(self.chat_frame)
        self.lineEdit.setPlaceholderText("請輸入消息...")
        self.lineEdit.setStyleSheet(
            "background-color: #FFFFFF; border-radius: 20px; border: 1px solid #E5E5E5; font-size: 16px; color: #333333; padding: 10px 16px;"
        )
        self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        self.input_layout.addWidget(self.lineEdit)

        # 發送按鈕
        self.send = QtWidgets.QPushButton(self.chat_frame)
        self.send.setText("發送")
        self.send.setStyleSheet("""
            QPushButton {
                background-color: #85C75A;
                color: white;
                font-size: 16px;
                font-weight: 600;
                border-radius: 20px;
                padding: 10px 24px;
                font-family: 'Microsoft YaHei', Arial;
                border: none;
            }
            QPushButton:hover {
                background-color: #76B34F;
            }
            QPushButton:pressed {
                background-color: #6A9F47;
            }
        """)
        self.send.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)
        self.input_layout.addWidget(self.send)

        self.input_container_layout.addLayout(self.input_layout)
        self.chat_layout.addWidget(self.input_container)

        # 添加 QSplitter 到主布局
        self.main_layout.addWidget(self.splitter)

        # 設置 QSplitter 的初始比例
        self.splitter.setSizes([300, 600])  # 左側用戶列表寬度 300，右側聊天區域寬度 600

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "UINE聊天室"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
