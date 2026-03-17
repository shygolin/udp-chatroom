import sys
import json
import socket
import time
import random
from datetime import datetime
from threading import Thread
from PyQt6.QtWidgets import (QApplication, QMainWindow, QInputDialog, QLineEdit, QWidget,
                             QLabel, QHBoxLayout, QVBoxLayout, QFrame, QFileDialog,
                             QSizePolicy)
from PyQt6.QtGui import QPixmap, QMovie, QFont
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt
from PyQt6.QtGui import QFont
from udpchatroom_ui import Ui_Form

# Define constants
BROADCAST_PORT = 12345
BROADCAST_ADDR = "255.255.255.255"
HEARTBEAT_INTERVAL = 5
TIMEOUT_SECONDS = 10

# Define signals for communication
class ChatSignals(QObject):
    new_message = pyqtSignal(str, str)
    update_users = pyqtSignal(list)
    flash_window = pyqtSignal()

class MessageBubble(QFrame):
    """自定义消息气泡 widget，支持圆角"""
    def __init__(self, username, message, timestamp, is_self, parent=None):
        super().__init__(parent)
        self.is_self = is_self
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background-color: transparent;")

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 消息容器（用于对齐）
        message_container = QHBoxLayout()
        message_container.setContentsMargins(0, 0, 0, 0)
        message_container.setSpacing(8)

        if not is_self:
            # 如果是别人的消息，显示用户名
            username_label = QLabel(username)
            username_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
            username_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(username_label)

        # 创建气泡和时间戳的垂直布局
        bubble_and_timestamp = QVBoxLayout()
        bubble_and_timestamp.setContentsMargins(0, 0, 0, 0)
        bubble_and_timestamp.setSpacing(2)

        # 气泡内容
        bubble_label = QLabel(message)
        bubble_label.setWordWrap(True)
        bubble_label.setFont(QFont("Microsoft YaHei", 14))

        if is_self:
            # 自己的消息：绿色气泡，右边对齐
            bubble_label.setStyleSheet("""
                background-color: #7CFC00;
                color: black;
                padding: 8px 12px;
                border-radius: 12px;
                font-size: 14px;
            """)
            # 添加气泡到垂直布局
            bubble_and_timestamp.addWidget(bubble_label, alignment=Qt.AlignmentFlag.AlignRight)

            # 时间戳，右对齐
            timestamp_label = QLabel(timestamp)
            timestamp_label.setStyleSheet("font-size: 10px; color: #888;")
            timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            bubble_and_timestamp.addWidget(timestamp_label)

            # 将气泡和时间戳组合添加到消息容器，靠右
            message_container.addStretch()
            message_container.addLayout(bubble_and_timestamp)
        else:
            # 别人的消息：白色气泡，左边对齐
            bubble_label.setStyleSheet("""
                background-color: white;
                color: black;
                padding: 8px 12px;
                border-radius: 12px;
                border: 1px solid #ccc;
                font-size: 14px;
            """)
            # 添加气泡到垂直布局
            bubble_and_timestamp.addWidget(bubble_label, alignment=Qt.AlignmentFlag.AlignLeft)

            # 时间戳，左对齐
            timestamp_label = QLabel(timestamp)
            timestamp_label.setStyleSheet("font-size: 10px; color: #888;")
            timestamp_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bubble_and_timestamp.addWidget(timestamp_label)

            # 将气泡和时间戳组合添加到消息容器，靠左
            message_container.addLayout(bubble_and_timestamp)
            message_container.addStretch()

        layout.addLayout(message_container)

class FileMessageBubble(QFrame):
    """自定义文件消息气泡 widget，支持图片和视频显示"""
    def __init__(self, username, file_path, file_type, timestamp, is_self, parent=None):
        super().__init__(parent)
        print(f"FileMessageBubble created: username={username}, file_type={file_type}, file_path={file_path}")  # 调试信息
        self.is_self = is_self
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background-color: transparent;")

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 消息容器（用于对齐）
        message_container = QHBoxLayout()
        message_container.setContentsMargins(0, 0, 0, 0)
        message_container.setSpacing(8)

        if not is_self:
            # 如果是别人的消息，显示用户名
            username_label = QLabel(username)
            username_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
            username_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(username_label)

        # 创建媒体和时间戳的垂直布局
        media_and_timestamp = QVBoxLayout()
        media_and_timestamp.setContentsMargins(0, 0, 0, 0)
        media_and_timestamp.setSpacing(2)

        # 媒体容器
        media_frame = QFrame()
        media_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {"#7CFC00" if is_self else "white"};
                border-radius: 12px;
                {"border: 1px solid #ccc;" if not is_self else ""}
            }}
        """)

        media_layout = QVBoxLayout(media_frame)
        media_layout.setContentsMargins(0, 0, 0, 0)
        media_layout.setSpacing(0)

        # 根据文件类型显示不同的内容
        if file_type == 'image':
            # 显示图片
            image_label = QLabel()
            pixmap = QPixmap(file_path)

            # 检查图片是否成功加载
            if pixmap.isNull():
                image_label.setText("❌ 图片加载失败")
                image_label.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
            else:
                # 限制图片最大尺寸
                max_size = 300
                if pixmap.width() > max_size or pixmap.height() > max_size:
                    pixmap = pixmap.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)

            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            media_layout.addWidget(image_label)
        elif file_type == 'video':
            # 显示视频（简化版：使用GIF动画或显示播放图标）
            video_label = QLabel("🎬")
            video_label.setStyleSheet("font-size: 48px; color: #333;")
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            media_layout.addWidget(video_label)

            # 显示文件名
            filename_label = QLabel(file_path.split('\\')[-1])
            filename_label.setStyleSheet("font-size: 12px; color: #333; padding: 4px;")
            filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            filename_label.setWordWrap(True)
            media_layout.addWidget(filename_label)
        else:
            # 不支持的文件类型
            unsupported_label = QLabel("❓")
            unsupported_label.setStyleSheet("font-size: 48px; color: #333;")
            unsupported_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            media_layout.addWidget(unsupported_label)

        # 设置media_frame的最大宽度
        media_frame.setMaximumWidth(300)
        media_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        if is_self:
            # 自己的消息：右边对齐
            media_and_timestamp.addWidget(media_frame, alignment=Qt.AlignmentFlag.AlignRight)

            # 时间戳，右对齐
            timestamp_label = QLabel(timestamp)
            timestamp_label.setStyleSheet("font-size: 10px; color: #888;")
            timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            media_and_timestamp.addWidget(timestamp_label)

            # 将媒体和时间戳组合添加到消息容器，靠右
            message_container.addStretch()
            message_container.addLayout(media_and_timestamp)
        else:
            # 别人的消息：左边对齐
            media_and_timestamp.addWidget(media_frame, alignment=Qt.AlignmentFlag.AlignLeft)

            # 时间戳，左对齐
            timestamp_label = QLabel(timestamp)
            timestamp_label.setStyleSheet("font-size: 10px; color: #888;")
            timestamp_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            media_and_timestamp.addWidget(timestamp_label)

            # 将媒体和时间戳组合添加到消息容器，靠左
            message_container.addLayout(media_and_timestamp)
            message_container.addStretch()

        layout.addLayout(message_container)

class UDPChatClient(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.running = True
        self.users = {}
        self.signals = ChatSignals()
        # 文件传输相关
        self.incoming_files = {}  # 存储正在接收的文件片段 {file_id: {chunks: [], total_chunks: 0, filename: "", file_type: ""}}
        self.incoming_files_lock = __import__('threading').Lock()  # 用于线程安全
        # 新增以下兩行：設置 central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)  
        # 將 UI 設置在 central widget 上
        self.ui = Ui_Form()
        self.ui.setupUi(central_widget)  
        # Adjust window size and title
        self.setWindowTitle("UINE聊天室")

        # 連接傳送按鈕和enter鍵到send_message函數
        self.ui.send.clicked.connect(self.send_message)
        self.ui.lineEdit.returnPressed.connect(self.send_message)
        self.ui.file_button.clicked.connect(self.select_and_send_file)

        # Initialize UDP communication
        self.init_udp()

        # 检查UDP是否成功初始化
        if not self.sock:
            self.show_message("系统", "⚠️ 网络初始化失败，无法发送消息。只能接收消息。")

        # Connect signals to slots
        self.signals.new_message.connect(self.show_message)
        self.signals.update_users.connect(self.update_user_list)
        self.signals.flash_window.connect(self.flash_title)

        # Start threads and timers
        self.receive_thread = Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()
        self.send_heartbeat()
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.cleanup_inactive_users)
        self.cleanup_timer.start(3000)

    def init_udp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # 允许多个程序实例同时绑定同一个端口
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 增加接收缓冲区大小（32KB）
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32768)
        try:
            self.sock.bind(("0.0.0.0", BROADCAST_PORT))
        except Exception as e:
            print(f"无法绑定端口 {BROADCAST_PORT}: {e}")
            self.sock = None

    def send_message(self):
        message = self.ui.lineEdit.text().strip()
        if not message or not self.sock:
            return
        packet = {
            "type": "message",
            "username": self.username,
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        self.sock.sendto(json.dumps(packet).encode("utf-8"), (BROADCAST_ADDR, BROADCAST_PORT))
        # 立即在界面上显示自己的消息
        self.signals.new_message.emit(self.username, message)
        self.ui.lineEdit.clear()

    def select_and_send_file(self):
        """选择并发送文件（图片或视频）"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;Videos (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All Files (*.*)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                self.send_file(file_path)

    def send_file(self, file_path):
        """发送文件（分片传输）"""
        if not self.sock:
            self.show_message("系统", "网络未初始化")
            return
        import os
        import base64

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 限制文件大小为 5MB
        max_size = 5 * 1024 * 1024
        if file_size > max_size:
            self.show_message("系统", "文件过大，最大支持 5MB")
            return

        # 读取文件内容并转为 base64
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_data_base64 = base64.b64encode(file_data).decode('utf-8')

        # 判断文件类型
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            file_type = 'image'
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']:
            file_type = 'video'
        else:
            self.show_message("系统", "不支持的文件格式")
            return

        # 立即在发送方的界面上显示文件（自己也能看到）
        self.show_message(self.username, f"[FILE]{file_type}:{file_path}")

        # 分片发送
        chunk_size = 2000  # 每个片的大小（字符数），减小以避免UDP数据包过大
        chunks = [file_data_base64[i:i+chunk_size] for i in range(0, len(file_data_base64), chunk_size)]
        total_chunks = len(chunks)
        file_id = f"{self.username}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        # 发送文件头信息
        header_packet = {
            "type": "file_header",
            "username": self.username,
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "total_chunks": total_chunks,
            "timestamp": datetime.now().isoformat()
        }
        self.sock.sendto(json.dumps(header_packet).encode("utf-8"), (BROADCAST_ADDR, BROADCAST_PORT))

        # 发送文件数据片
        for i, chunk in enumerate(chunks):
            time.sleep(0.01)  # 避免网络拥堵
            chunk_packet = {
                "type": "file_chunk",
                "username": self.username,
                "file_id": file_id,
                "chunk_index": i,
                "chunk_data": chunk,
                "timestamp": datetime.now().isoformat()
            }
            self.sock.sendto(json.dumps(chunk_packet).encode("utf-8"), (BROADCAST_ADDR, BROADCAST_PORT))

        # 发送文件结束标记
        footer_packet = {
            "type": "file_end",
            "username": self.username,
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        }
        self.sock.sendto(json.dumps(footer_packet).encode("utf-8"), (BROADCAST_ADDR, BROADCAST_PORT))

    def send_heartbeat(self):
        def heartbeat_task():
            while self.running:
                if self.sock:
                    packet = {"type": "heartbeat", "username": self.username}
                    self.sock.sendto(json.dumps(packet).encode("utf-8"), (BROADCAST_ADDR, BROADCAST_PORT))
                time.sleep(HEARTBEAT_INTERVAL)

        Thread(target=heartbeat_task, daemon=True).start()

    def receive_loop(self):
        if not self.sock:
            return
        while self.running:
            try:
                data, addr = self.sock.recvfrom(65535)  # 增加接收缓冲区到64KB
                packet = json.loads(data.decode("utf-8"))
                if packet["type"] == "heartbeat":
                    self.users[packet["username"]] = datetime.now()
                    self.signals.update_users.emit(list(self.users.keys()))
                elif packet["type"] == "message":
                    # 不显示自己发送的消息，因为已经在send_message中显示了
                    if packet["username"] != self.username:
                        self.signals.new_message.emit(packet["username"], packet["content"])
                        self.signals.flash_window.emit()
                elif packet["type"] == "file_header" and packet["username"] != self.username:
                    # 接收文件头
                    print(f"Received file header: {packet['file_name']}, chunks: {packet['total_chunks']}, type: {packet['file_type']}")  # 调试信息
                    with self.incoming_files_lock:
                        self.incoming_files[packet["file_id"]] = {
                            "chunks": [],
                            "total_chunks": packet["total_chunks"],
                            "filename": packet["file_name"],
                            "file_type": packet["file_type"],
                            "username": packet["username"]
                        }
                elif packet["type"] == "file_chunk" and packet["file_id"] in self.incoming_files:
                    # 接收文件数据片
                    with self.incoming_files_lock:
                        if packet["username"] != self.username:
                            self.incoming_files[packet["file_id"]]["chunks"].append(
                                (packet["chunk_index"], packet["chunk_data"])
                            )
                            # 定期打印进度
                            if packet["chunk_index"] % 10 == 0:
                                print(f"Received chunk {packet['chunk_index']}/{self.incoming_files[packet['file_id']]['total_chunks']}")  # 调试信息
                elif packet["type"] == "file_end" and packet["file_id"] in self.incoming_files:
                    # 文件传输完成，重组文件
                    if packet["username"] != self.username:
                        print(f"File transfer completed, processing file...")  # 调试信息
                        self.process_received_file(packet["file_id"])
                elif packet["type"] == "leave":
                    if packet["username"] in self.users:
                        del self.users[packet["username"]]
                    self.signals.update_users.emit(list(self.users.keys()))
            except Exception as e:
                print(f"Error receiving data: {e}")

    def process_received_file(self, file_id):
        """处理接收到的文件，重组并保存"""
        import base64
        import os

        with self.incoming_files_lock:
            if file_id not in self.incoming_files:
                return

            file_info = self.incoming_files[file_id]
            chunks = file_info["chunks"]

            # 检查是否接收到了所有的chunk
            print(f"Received {len(chunks)}/{file_info['total_chunks']} chunks")  # 调试信息
            if len(chunks) != file_info["total_chunks"]:
                print(f"Warning: Missing chunks! Expected {file_info['total_chunks']}, got {len(chunks)}")  # 调试信息

            # 按顺序重组数据
            chunks.sort(key=lambda x: x[0])
            file_data_base64 = "".join([chunk[1] for chunk in chunks])

            # 解码并保存文件
            try:
                print(f"Decoding file data, base64 length: {len(file_data_base64)}")  # 调试信息
                file_data = base64.b64decode(file_data_base64)
                print(f"Decoded file data length: {len(file_data)} bytes")  # 调试信息

                # 创建临时目录
                temp_dir = os.path.join(os.path.dirname(__file__), "temp_files")
                os.makedirs(temp_dir, exist_ok=True)

                # 保存文件
                file_path = os.path.join(temp_dir, file_info["filename"])
                # 确保文件路径是绝对路径
                file_path = os.path.abspath(file_path)
                with open(file_path, 'wb') as f:
                    f.write(file_data)

                print(f"File saved: {file_path}")  # 调试信息

                # 显示文件消息
                self.signals.new_message.emit(file_info["username"], f"[FILE]{file_info['file_type']}:{file_path}")

            except Exception as e:
                print(f"Error processing file: {e}")
            finally:
                # 清理已接收的文件信息
                del self.incoming_files[file_id]

    def show_message(self, username, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        is_self = (username == self.username)

        # 检查是否是文件消息
        if message.startswith("[FILE]"):
            # 解析文件消息格式：[FILE]{file_type}:{file_path}
            try:
                file_type, file_path = message[6:].split(":", 1)
                print(f"File message received: type={file_type}, path={file_path}")  # 调试信息
                # 创建文件消息气泡
                message_bubble = FileMessageBubble(username, file_path, file_type, timestamp, is_self)
            except Exception as e:
                print(f"Error parsing file message: {e}, message={message}")  # 调试信息
                message_bubble = MessageBubble(username, "文件加载失败", timestamp, is_self)
        else:
            # 创建普通文本消息气泡
            message_bubble = MessageBubble(username, message, timestamp, is_self)

        # 将消息气泡添加到 scrollLayout（在 stretch 之前）
        self.ui.scrollLayout.insertWidget(self.ui.scrollLayout.count() - 1, message_bubble)

        # 滚动到底部
        QTimer.singleShot(100, lambda: self.ui.scrollArea.verticalScrollBar().setValue(
            self.ui.scrollArea.verticalScrollBar().maximum()
        ))

    def update_user_list(self, users):
        """更新在線用戶列表"""
        self.ui.user_list.clear()  # 清空列表
        for user in users:
            self.ui.user_list.addItem(user)  # 添加用戶到列表
        self.ui.user_label.setText(f"在線用戶 (人數{len(users)})")  # 更新用戶數量

    def flash_title(self):
        original = self.windowTitle()
        self.setWindowTitle("💬 新消息！")
        QTimer.singleShot(1500, lambda: self.setWindowTitle(original))

    def cleanup_inactive_users(self):
        now = datetime.now()
        inactive = [u for u, t in self.users.items() if (now - t).total_seconds() > TIMEOUT_SECONDS]
        for user in inactive:
            del self.users[user]
        self.signals.update_users.emit(list(self.users.keys()))

    def closeEvent(self, event):
        self.running = False
        if self.sock:
            packet = {"type": "leave", "username": self.username}
            try:
                self.sock.sendto(json.dumps(packet).encode("utf-8"), (BROADCAST_ADDR, BROADCAST_PORT))
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    username, ok = QInputDialog.getText(None, "名稱", "請輸入名稱：", QLineEdit.EchoMode.Normal, "User" + str(random.randint(1000, 9999)))
    if ok and username:
        window = UDPChatClient(username)
        window.resize(900, 600)  # 設置窗口大小
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
